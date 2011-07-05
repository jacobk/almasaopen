#!/usr/bin/env python

from google.appengine.ext import webapp, db
from google.appengine.ext.webapp import util, template
from google.appengine.api import images, users
from google.appengine.ext.webapp.util import login_required
from datetime import datetime, timedelta
import os
import jpeg
import operator

class Race(db.Model):
    """Datastore model for a race with a user, start- and finish photo"""
    startPhoto = db.BlobProperty()
    startTime = db.DateTimeProperty()
    finishPhoto = db.BlobProperty()
    finishTime = db.DateTimeProperty()
    totalTime = db.IntegerProperty()
    user = db.UserProperty()
        
class MainHandler(webapp.RequestHandler):
    def get(self):
        template_values = {}
        user = users.get_current_user()
        races = Race.all()
        races.order("totalTime")
        shit_list = []
        time_list = []
        for race in races:
            if race.user.nickname() not in shit_list:
                shit_list.append(race.user.nickname())
                time_list.append(race)
            if len(shit_list)>4:
                break

        template_values['races'] = time_list
        fail = self.request.get("fail")
        if fail:
            template_values['fail'] = fail
        if user:
            template_values['currentuser'] = users.get_current_user().nickname()
            template_values['logout'] = users.create_logout_url('/')
        else:
            template_values['login'] = users.create_login_url('/')
        
        path = os.path.join(os.path.dirname(__file__), 'index.html')
        self.response.out.write(template.render(path, template_values))


class UploadHandler(webapp.RequestHandler):
    """Handler for adding a race to the datastore"""
    def post(self):
        race = Race()
        try:
            startPhoto = images.Image(self.request.get("start"))
            startPhoto.resize(width=200, height=200)
            startPhoto.im_feeling_lucky()
            race.startPhoto = db.Blob(startPhoto.execute_transforms())
            startTime = jpeg.Exif(self.request.get("start"))["DateTimeDigitized"]
            race.startTime = datetime.strptime(startTime, "%Y:%m:%d %H:%M:%S")

            finishPhoto = images.Image(self.request.get("finish"))
            finishPhoto.resize(width=200, height=200)
            finishPhoto.im_feeling_lucky()
            race.finishPhoto = db.Blob(finishPhoto.execute_transforms())
            finishTime = jpeg.Exif(self.request.get("finish"))["DateTimeDigitized"]
            race.finishTime = datetime.strptime(finishTime, "%Y:%m:%d %H:%M:%S")
        except ValueError:
            self.redirect('/?fail=Oj! Bilderna har ej korrekt EXIF data.')
        else:
            totalTime = race.finishTime - race.startTime
            
            race.totalTime = totalTime.seconds
            
            race.user = users.get_current_user()
            if race.finishTime<race.startTime:
                self.redirect('/?fail=Oj! Bilderna i fel ordning.')
            else:
                race.put()
                self.redirect('/showrace/' + str(race.key()))
        
class GetImage(webapp.RequestHandler):
    """Handler for getting an image from the datastore"""
    def get(self):
        race = db.get(self.request.get("race_id"))
        photo_type = self.request.get("type")
        
        self.response.headers['Content-Type'] = 'image/jpeg'
        if photo_type == "start":
            self.response.out.write(race.startPhoto)
        if photo_type == "finish":
            self.response.out.write(race.finishPhoto)

class ShowRace(webapp.RequestHandler):
    """Handler to show a specific race"""
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
        
        path = os.path.join(os.path.dirname(__file__), 'showrace.html')
        self.response.out.write(template.render(path, template_values))
        
class RemoveRace(webapp.RequestHandler):
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
        path = os.path.join(os.path.dirname(__file__), 'remove.html')
        self.response.out.write(template.render(path, template_values))
        
    def post(self, *ar):
        db.get(ar[0]).delete()
        self.redirect('/?fail=Lopp raderat.')

class MyRaces(webapp.RequestHandler):
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
        
        path = os.path.join(os.path.dirname(__file__), 'myraces.html')
        self.response.out.write(template.render(path, template_values))

class Information(webapp.RequestHandler):
    """Handler for the information page"""
    def get(self):
        
        template_values = {}

        template_values['currentuser'] = users.get_current_user()
        template_values['logout'] = users.create_logout_url('/')
        
        path = os.path.join(os.path.dirname(__file__), 'info.html')
        self.response.out.write(template.render(path, template_values))

def main():
    webapp.template.register_template_library('filters')
    
    application = webapp.WSGIApplication([('/', MainHandler),
                                        ('/upload', UploadHandler),
                                        ('/img', GetImage),
                                        ('/showrace/(.*)', ShowRace),
                                        ('/removerace/(.*)', RemoveRace),
                                        ('/myraces', MyRaces),
                                        ('/info', Information)],
                                         debug=True)
    util.run_wsgi_app(application)


if __name__ == '__main__':
    main()
