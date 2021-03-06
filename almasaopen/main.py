#!/usr/bin/env python
import calendar
import datetime
import email.utils
import os

from google.appengine.ext import webapp, db
from google.appengine.ext.webapp import template
import google.appengine.ext.webapp.util
from google.appengine.api import images, users

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
        login=users.create_login_url('/')
        self.render("index.html", leader=leader, runner_ups=runner_ups,
                    noobs=noobs, fail=fail, login=login, home=True)

    def make_scoreboard(self):
        dt = datetime.datetime(2012,4,23)
        races = Race.all()
        races.filter("start_time > ", dt)
        # races.order("start_time")
        # races.order("total_time")
        shit_list = []
        race_list = []
        for race in races:
            if race.racer not in shit_list:
                shit_list.append(race.racer)
                race_list.append(race)

        return_list = sorted(race_list, key=lambda race: race.total_time)
        for i, race in enumerate(return_list):
            race.position = i + 1
        try:
            return return_list[0:1][0], return_list[1:5], return_list[5:]
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
    def get(self, race_id):
        race = db.get(race_id)
        self.response.headers["Content-Type"] = 'image/jpeg'
        d = datetime.datetime.utcnow() + datetime.timedelta(days=365*10)
        t = calendar.timegm(d.utctimetuple())
        self.response.headers["Expires"] = email.utils.formatdate(t,
                                                  localtime=False, usegmt=True)
        self.response.headers["Cache-Control"] = "max-age=" + str(86400*365*10)
        self.response.out.write(self.photo(race))

    def photo(self, race):
        raise NotImplementedError


class StartPhotoHandler(BasePhotoHandler):
    def photo(self, race):
        return race.start_photo


class FinishPhotoHandler(BasePhotoHandler):
    def photo(self, race):
        return race.finish_photo


class CommentsHandler(BaseHandler):
    """Handler for comments"""
    def post(self, race_id):
        comment = Comment()
        comment.racer = self.current_racer
        comment.comment = self.request.get('comment')
        comment.ref = db.get(race_id)
        comment.put()
        self.redirect('/races/' + race_id)


class CommentHandler(BaseHandler):
    def post(self, race_id, comment_id):
        comment = db.get(comment_id)
        if self.current_racer == comment.racer :
            comment.delete()
        self.redirect("/races/%s" % race_id)


class RaceHandler(BaseHandler):
    """Handler to show a specific race"""
    def get(self, race_id):
        race = db.get(race_id)
        comments = race.comments.order("-time")
        self.render("showrace.html", race=race, comments=comments)


class RemoveRace(BaseHandler):
    """Handler for removing a race from the datastore"""
    def get(self, race_id):
        race = db.get(race_id)
        self.render("remove.html", race=race)

    def post(self, race_id):
        race = db.get(race_id)
        if self.current_racer == race.racer:
            race.delete()
        self.redirect('/?fail=Lopp raderat.')


class Information(BaseHandler):
    """Handler for the information page"""
    def get(self):
        self.render("info.html")


class RacersHandler(BaseHandler):
    def get(self):
        q = Racer.all()
        key = lambda x: x.nickname.lower()
        racers = sorted([racer for racer in q], key=key)
        self.render("racers.html", col1=racers[0::3], col2=racers[1::3],
                    col3=racers[2::3])


class RacerHandler(BaseHandler):
    def post(self, racer_id):
        if self.current_racer and self.request.get("name")!="":
            self.current_racer.nickname = self.request.get("name")
            self.current_racer.put()
        self.redirect("/racers/%s" % racer_id)

    def get(self, racer_id):
        racer = Racer.get(racer_id)
        q = Race.all()
        q.filter("racer =", racer)
        q.order("-start_time")
        races = [race for race in q.run()]
        self.render("racer.html", racer=racer, races=races)


def main():
    webapp.template.register_template_library('filters')
    application = webapp.WSGIApplication([('/', MainHandler),
                                        ('/upload', UploadHandler),
                                        ('/races/([^/]*)/photos/start', StartPhotoHandler),
                                        ('/races/([^/]*)/photos/finish', FinishPhotoHandler),
                                        ('/races/([^/]*)/comments', CommentsHandler),
                                        ('/races/([^/]*)/comments/(.*)', CommentHandler),
                                        ('/races/([^/]*)', RaceHandler),
                                        ('/removerace/(.*)', RemoveRace),
                                        ('/info', Information),
                                        ('/racers/(.*)', RacerHandler),
                                        ('/racers', RacersHandler)],
                                         debug=True)
    google.appengine.ext.webapp.util.run_wsgi_app(application)


if __name__ == '__main__':
    main()
