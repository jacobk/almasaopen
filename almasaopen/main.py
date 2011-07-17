#!/usr/bin/env python
import calendar
import datetime
import email.utils
import logging
import os

from google.appengine.ext import webapp, db
from google.appengine.ext.webapp import template
import google.appengine.ext.webapp.util
from google.appengine.api import images, users
from google.appengine.ext.webapp.util import login_required

# TODO: Move vogel to vendor
import jpeg
import util

class AlmasaError(Exception):
    """Base class for all exceptions in the almasa main module"""


class ValidationError(AlmasaError):
    pass


class Racer(db.Model):
    user = db.UserProperty(required=True)
    nickname = db.StringProperty()

    def __eq__(self, other):
         if isinstance(other, Racer):
             return self.user == other.user
         return NotImplemented

    def __ne__(self, other):
        result = self.__eq__(other)
        if result is NotImplemented:
            return result
        return not result


class Race(db.Model):
    """Datastore model for a race with a user, start- and finish photo"""
    start_photo = db.BlobProperty()
    start_time = db.DateTimeProperty()
    finish_photo = db.BlobProperty()
    finish_time = db.DateTimeProperty()
    total_time = db.IntegerProperty()
    extra = db.TextProperty()
    racer = db.ReferenceProperty(Racer, collection_name="races")


class Comment(db.Model):
    """Datastore model for comments to a race"""
    racer = db.ReferenceProperty(Racer, collection_name="comments")
    time = db.DateTimeProperty(auto_now_add=True)
    comment = db.TextProperty()
    ref = db.ReferenceProperty(Race, collection_name="comments")


class BaseHandler(webapp.RequestHandler):
    def render(self, template_name, **kwargs):
        path = os.path.join(os.path.dirname(__file__), "templates",
                            template_name)
        kwargs.update({"current_racer": self.current_racer,
                       "logout": users.create_logout_url('/')})
        self.response.out.write(template.render(path, kwargs))

    @property
    def current_racer(self):
        if hasattr(self, "_current_user"):
            return self._current_user
        current_user = users.get_current_user()
        if current_user: # logged in
            q = Racer.all()
            q.filter("user =", current_user)
            racer = q.get()
            if not racer: # no corresponding racer entity
                racer = Racer(user=current_user)
                racer.nickname = current_user.nickname()
                racer.put()
            current_user = racer
        self._current_user = current_user
        return self._current_user


class MainHandler(BaseHandler):
    def get(self):
        leader, runner_ups, noobs = self.make_scoreboard()
        fail = self.request.get("fail", None)
        login = users.create_login_url('/')
        home = True
        template_values = locals()
        template_values.pop("self")
        self.render("index.html", **template_values)

    def make_scoreboard(self):
        races = Race.all()
        races.order("total_time")
        shit_list = []
        race_list = []
        for race in races:
            if race.racer not in shit_list:
                shit_list.append(race.racer)
                race_list.append(race)
        for i, race in enumerate(race_list):
            race.position = i + 1
        try:
            return race_list[0:1][0], race_list[1:5], race_list[5:]
        except IndexError:
            return None, [], []


class UploadHandler(BaseHandler):
    """Handler for adding a race to the datastore"""
    def post(self):
        start_photo_data = self.request.get("start")
        finish_photo_data = self.request.get("finish")
        try:
            self._create_race(start_photo_data, finish_photo_data)
        except ValidationError, e:
            self.redirect('/?fail=Oj! %s' % str(e))

    def _create_race(self, start_photo_data, finish_photo_data):
        race = Race(racer=self.current_racer)
        race.start_time = self._extract_time(start_photo_data)
        race.finish_time = self._extract_time(finish_photo_data)
        if race.finish_time < race.start_time:
            raise ValidationError("Bilderna i fel ordning.")
        start_photo = self._process_photo_data(start_photo_data,
                                               self.request.get("startrot"))
        finish_photo = self._process_photo_data(finish_photo_data,
                                                self.request.get("finishrot"))
        race.start_photo = db.Blob(start_photo.execute_transforms())
        race.finish_photo = db.Blob(finish_photo.execute_transforms())
        total_time = race.finish_time - race.start_time
        race.total_time = total_time.seconds
        if self.request.get("extra") :
            race.extra = self.request.get("extra")
        race.put()
        self.redirect('/races/' + str(race.key()))

    def _process_photo_data(self, photo_data, rot=None):
        photo = images.Image(photo_data)
        if rot:
            photo.rotate(int(rot));
        photo.resize(width=220)
        photo.im_feeling_lucky()
        return photo

    def _extract_time(self, photo_data):
        try:
            exif_time = jpeg.Exif(photo_data)["DateTimeDigitized"]
        except ValueError:
            raise ValidationError("Bilderna har ej korrekt EXIF data.")
        except KeyError:
            raise ValidationError("Bilderna saknar tidsdata :(")
        dt = datetime.datetime.strptime(exif_time, "%Y:%m:%d %H:%M:%S")
        return util.cet_as_utc(dt)


class BasePhotoHandler(BaseHandler):
    """Handler for getting an image from the datastore"""
    def serve_photo(self, race_id, photo_type):
        race = db.get(race_id)
        self.response.headers.add_header("Content-Type", 'image/jpeg')
        d = datetime.datetime.utcnow() + datetime.timedelta(days=365*10)
        t = calendar.timegm(d.utctimetuple())
        self.response.headers.add_header("Expires", email.utils.formatdate(t,
                                         localtime=False, usegmt=True))
        self.response.headers.add_header("Cache-Control",
                                         "max-age=" + str(86400*365*10))
        self.response.out.write(getattr(race, photo_type))


class StartPhotoHandler(BasePhotoHandler):
    def get(self, race_id):
        self.serve_photo(race_id, "start_photo")


class FinishPhotoHandler(BasePhotoHandler):
    def get(self, race_id):
        self.serve_photo(race_id, "finish_photo")


class CommentsHandler(BaseHandler):
    """Handler for comments"""
    def post(self, *ar):
        comment = Comment()
        comment.racer = self.current_racer
        comment.comment = self.request.get('comment')
        comment.ref = db.get(ar[0])
        comment.put()
        self.redirect('/races/' + ar[0])


class CommentHandler(BaseHandler):
    def post(self, race_id, comment_id):
        comment = db.get(comment_id)
        if self.current_racer == comment.racer :
            comment.delete()
        self.redirect("/races/%s" % race_id)


class ShowRace(BaseHandler):
    """Handler to show a specific race"""
    def get(self, *ar):
        race = db.get(ar[0])
        template_values = {}
        template_values['id'] = ar[0]
        template_values['comments'] = race.comments.order("-time")
        template_values['race'] = race
        self.render("showrace.html", **template_values)


class RemoveRace(BaseHandler):
    """Handler for removing a race from the datastore"""
    def get(self, *ar):
        race = db.get(ar[0])
        template_values = {}
        template_values['id'] = ar[0]
        template_values['username'] = race.racer.nickname
        template_values['start_time'] = race.start_time
        template_values['finish_time'] = race.finish_time
        template_values['total_time'] = race.total_time
        
        self.render("remove.html", **template_values)

    def post(self, *ar):
        db.get(ar[0]).delete()
        self.redirect('/?fail=Lopp raderat.')


class MyRaces(BaseHandler):
    """Handler to show all of a specific users races"""
    @login_required
    def get(self):
        q = Race.all()
        q.filter("racer =", self.current_racer)
        q.order("-start_time")
        races = [race for race in q.run()]
        self.render("myraces.html", races=races)


class Information(BaseHandler):
    """Handler for the information page"""
    def get(self):
        template_values = {}
        self.render("info.html", **template_values)


class RacersHandler(BaseHandler):
    def get(self):
        pass


class RacerHandler(BaseHandler):
    def post(self, racer_id):
        if self.current_racer:
            self.current_racer.nickname = self.request.get("name")
            self.current_racer.put()
        self.redirect("/myraces")


class UTCMigrater(webapp.RequestHandler):
    def get(self):
        q = Race.all()
        for race in q:
            race.start_time = util.cet_as_utc(race.start_time)
            race.finish_time = util.cet_as_utc(race.finish_time)
            race.put()
        self.response.out.write("DONE!")


def main():
    webapp.template.register_template_library('filters')
    
    application = webapp.WSGIApplication([('/', MainHandler),
                                        ('/upload', UploadHandler),
                                        ('/races/([^/]*)/photos/start', StartPhotoHandler),
                                        ('/races/([^/]*)/photos/finish', FinishPhotoHandler),
                                        ('/races/([^/]*)/comments', CommentsHandler),
                                        ('/races/([^/]*)/comments/(.*)', CommentHandler),
                                        ('/races/([^/]*)', ShowRace),
                                        ('/removerace/(.*)', RemoveRace),
                                        ('/myraces', MyRaces),
                                        ('/info', Information),
                                        ('/racers/(.*)', RacerHandler),
                                        ('/convert_to_utc', UTCMigrater),
                                        ('/racers', RacersHandler)],
                                         debug=True)
    google.appengine.ext.webapp.util.run_wsgi_app(application)


if __name__ == '__main__':
    main()
