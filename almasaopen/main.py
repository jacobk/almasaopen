#!/usr/bin/env python

from google.appengine.ext import webapp, db
from google.appengine.ext.webapp import util, template
from google.appengine.api import images, users
from google.appengine.ext.webapp.util import login_required
from datetime import datetime, timedelta
import os

# TODO: Move vogel to vendor
import jpeg

class Race(db.Model):
    """Datastore model for a race with a user, start- and finish photo"""
    startPhoto = db.BlobProperty()
    startTime = db.DateTimeProperty()
    finishPhoto = db.BlobProperty()
    finishTime = db.DateTimeProperty()
    totalTime = db.IntegerProperty()
    user = db.UserProperty()
    extra = db.TextProperty()


class Comment(db.Model):
    """Datastore model for comments to a race"""
    user = db.UserProperty()
    time = db.DateTimeProperty()
    comment = db.TextProperty()
    ref = db.ReferenceProperty(Race, collection_name="comments")


class BaseHandler(webapp.RequestHandler):
    def render(self, template_name, **kwargs):
        path = os.path.join(os.path.dirname(__file__), "templates",
                            template_name)
        kwargs.update({"current_user": users.get_current_user()})
        self.response.out.write(template.render(path, kwargs))

    @property
    def current_user(self):
        return users.get_current_user()


class MainHandler(BaseHandler):
    def get(self):
        leader, runner_ups, noobs = self.make_scoreboard()
        fail = self.request.get("fail", None)
        logout = users.create_logout_url('/')
        login = users.create_login_url('/')
        home = True
        template_values = locals()
        template_values.pop("self")
        self.render("index.html", **template_values)

    def make_scoreboard(self):
        races = Race.all()
        races.order("totalTime")
        shit_list = []
        race_list = []
        for race in races:
            if race.user.nickname() not in shit_list:
                shit_list.append(race.user.nickname())
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
        race = Race()
        try:
            startTime = jpeg.Exif(self.request.get("start"))["DateTimeDigitized"]
            race.startTime = datetime.strptime(startTime, "%Y:%m:%d %H:%M:%S")
            startPhoto = images.Image(self.request.get("start"))
            startPhoto.resize(width=200, height=200)
            startPhoto.im_feeling_lucky()
            if self.request.get("startrot") :
                startPhoto.rotate(int(self.request.get("startrot")));
            race.startPhoto = db.Blob(startPhoto.execute_transforms())

            finishTime = jpeg.Exif(self.request.get("finish"))["DateTimeDigitized"]
            race.finishTime = datetime.strptime(finishTime, "%Y:%m:%d %H:%M:%S")
            finishPhoto = images.Image(self.request.get("finish"))
            finishPhoto.resize(width=200, height=200)
            finishPhoto.im_feeling_lucky()
            if self.request.get("finishrot") :
                finishPhoto.rotate(int(self.request.get("finishrot")));
            race.finishPhoto = db.Blob(finishPhoto.execute_transforms())
        except ValueError:
            self.redirect('/?fail=Oj! Bilderna har ej korrekt EXIF data.')
        else:
            totalTime = race.finishTime - race.startTime
            
            race.totalTime = totalTime.seconds
            
            if self.request.get("extra") :
                race.extra = self.request.get("extra")
            race.user = users.get_current_user()
            if race.finishTime<=race.startTime:
                self.redirect('/?fail=Oj! Bilderna i fel ordning.')
            else:
                race.put()
                self.redirect('/showrace/' + str(race.key()))
        
class GetImage(BaseHandler):
    """Handler for getting an image from the datastore"""
    def get(self):
        race = db.get(self.request.get("race_id"))
        photo_type = self.request.get("type")
        
        self.response.headers['Content-Type'] = 'image/jpeg'
        if photo_type == "start":
            self.response.out.write(race.startPhoto)
        if photo_type == "finish":
            self.response.out.write(race.finishPhoto)

class AddComment(BaseHandler):
    """Handler for comments"""
    def post(self, *ar):
        comment = Comment()
        comment.user = users.get_current_user()
        comment.comment = self.request.get('comment')
        comment.time = datetime.now()
        comment.ref = db.get(ar[0])
        comment.put()
        self.redirect('/showrace/' + ar[0])

class RemoveComment(BaseHandler):
    """docstring for RemoveComment"""
    def post(self):
        comment = db.get(self.request.get("commentid"))
        if users.get_current_user() == comment.user :
            comment.delete()

class ShowRace(BaseHandler):
    """Handler to show a specific race"""
    def get(self, *ar):
        race = db.get(ar[0])
        template_values = {}
        
        template_values['id'] = ar[0]
        template_values['username'] = race.user
        template_values['starttime'] = race.startTime
        template_values['finishtime'] = race.finishTime
        template_values['totaltime'] = race.totalTime
        template_values['currentuser'] = users.get_current_user()
        template_values['logout'] = users.create_logout_url('/')
        template_values['comments'] = race.comments
        template_values['extra'] = race.extra
        self.render("showrace.html", **template_values)


class RemoveRace(BaseHandler):
    """Handler for removing a race from the datastore"""
    def get(self, *ar):
        race = db.get(ar[0])
        template_values = {}
        template_values['id'] = ar[0]
        template_values['username'] = race.user.nickname()
        template_values['starttime'] = race.startTime
        template_values['finishtime'] = race.finishTime
        template_values['totaltime'] = race.totalTime
        template_values['currentuser'] = users.get_current_user()
        template_values['logout'] = users.create_logout_url('/')
        self.render("remove.html", **template_values)

    def post(self, *ar):
        db.get(ar[0]).delete()
        self.redirect('/?fail=Lopp raderat.')

class MyRaces(BaseHandler):
    """Handler to show all of a specific users races"""
    @login_required
    def get(self):
        races = Race.all()
        races.filter("user =", users.get_current_user())
        races.order("-startTime")
        template_values = {}

        template_values['races'] = races
        template_values['currentuser'] = users.get_current_user()
        template_values['logout'] = users.create_logout_url('/')
        self.render("myraces.html", **template_values)


class Information(BaseHandler):
    """Handler for the information page"""
    def get(self):
        
        template_values = {}

        template_values['currentuser'] = users.get_current_user()
        template_values['logout'] = users.create_logout_url('/')
        self.render("info.html", **template_values)


def main():
    webapp.template.register_template_library('filters')
    
    application = webapp.WSGIApplication([('/', MainHandler),
                                        ('/upload', UploadHandler),
                                        ('/img', GetImage),
                                        ('/showrace/(.*)', ShowRace),
                                        ('/addcomment/(.*)', AddComment),
                                        ('/removecomment', RemoveComment),
                                        ('/removerace/(.*)', RemoveRace),
                                        ('/myraces', MyRaces),
                                        ('/info', Information)],
                                         debug=True)
    util.run_wsgi_app(application)


if __name__ == '__main__':
    main()
