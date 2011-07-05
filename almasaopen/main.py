#!/usr/bin/env python
import logging
import os
import sys
import urllib
import wsgiref.handlers

# Filthy path loadpath manipulation
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'vendor/tornado'))

import tornado.web
import tornado.wsgi
from google.appengine.ext import db
from google.appengine.api import images, users
# from google.appengine.ext.webapp.util import login_required
from datetime import datetime, timedelta

# TODO: Move vogel to vendor
import jpeg
import filters


class AlmasaError(Exception):
    """Base class for all exceptions in the almasa module"""


class ValidationError(AlmasaError):
    pass


class Race(db.Model):
    """Datastore model for a race with a user, start- and finish photo"""
    start_photo = db.BlobProperty()
    start_time = db.DateTimeProperty()
    finish_photo = db.BlobProperty()
    finish_time = db.DateTimeProperty()
    total_time = db.IntegerProperty()
    user = db.UserProperty()


class BaseHandler(tornado.web.RequestHandler):
    _DEFAULT_ERROR_FMT = "Oj! %s"
    
    """Implements Google Accounts authentication methods."""
    def get_current_user(self):
        user = users.get_current_user()
        return user

    def get_login_url(self):
        return users.create_login_url(self.request.uri)

    def render_string(self, template_name, **kwargs):
        # Let the templates access the users module to generate login URLs
        return tornado.web.RequestHandler.render_string(
            self, template_name, users=users, **kwargs)

    def redirect_fail(self, url, message, fmt=_DEFAULT_ERROR_FMT):
        params = {"fail": fmt % message}
        self.redirect("%s?%s" % (url, urllib.urlencode(params)))

    def render(self, *args, **kwargs):
        super(BaseHandler, self).render(filters=filters, *args, **kwargs)


class MainHandler(BaseHandler):
    def get(self):
        races = Race.all()
        races.order("total_time")
        shit_list = []
        time_list = []
        for race in races:
            if race.user.nickname() not in shit_list:
                shit_list.append(race.user.nickname())
                time_list.append(race)
            if len(shit_list)>4:
                break

        template_values = {}
        template_values['races'] = time_list
        template_values['fail'] = self.get_argument("fail", None)
        if self.current_user:
            template_values['current_user'] = users.get_current_user()
            template_values['logout'] = users.create_logout_url('/')
        else:
            template_values['login'] = users.create_login_url('/')
        self.render("index.html", **template_values)


class UploadHandler(BaseHandler):
    """Handler for adding a race to the datastore"""
    @tornado.web.authenticated
    def post(self):
        start_photo_data = self.request.files.get("start")[0]["body"]
        finish_photo_data = self.request.files.get("finish")[0]["body"]
        try:
            self._create_race(start_photo_data, finish_photo_data)
        except ValidationError, e:
            self.redirect_fail("/", str(e))

    def _create_race(self, start_photo_data, finish_photo_data):
        race = Race()
        race.start_time = self._extract_time(start_photo_data)
        race.finish_time = self._extract_time(finish_photo_data)
        if race.finish_time < race.start_time:
            raise ValidationError("Bilderna i fel ordning.")
        start_photo = self._process_photo_data(start_photo_data)
        finish_photo = self._process_photo_data(finish_photo_data)
        race.start_photo = db.Blob(start_photo.execute_transforms())
        race.finish_photo = db.Blob(finish_photo.execute_transforms())
        total_time = race.finish_time - race.start_time
        race.total_time = total_time.seconds
        race.user = users.get_current_user()
        race.put()
        self.redirect('/showrace/' + str(race.key()))

    def _process_photo_data(self, photo_data):
        photo = images.Image(photo_data)
        photo.resize(width=200, height=200)
        photo.im_feeling_lucky()
        return photo

    def _extract_time(self, photo_data):
        try:
            exif_time = jpeg.Exif(photo_data)["DateTimeDigitized"]
        except ValueError:
            raise ValidationError("Bilderna har ej korrekt EXIF data.")
        except KeyError:
            raise ValidationError("Bilderna saknar tidsdata")
        return datetime.strptime(exif_time, "%Y:%m:%d %H:%M:%S")


class GetImage(BaseHandler):
    """Handler for getting an image from the datastore"""
    def get(self):
        race = db.get(self.get_argument("race_id"))
        photo_type = self.get_argument("type")
        self.set_header('Content-Type', 'image/jpeg')
        # TODO: Resolve issue with wsgiref not handeling GAE Blob str stubclas
        if photo_type == "start":
            self.write(str(race.start_photo))
        if photo_type == "finish":
            self.write(str(race.finish_photo))


class ShowRace(BaseHandler):
    """Handler to show a specific race"""
    def get(self, *ar):
        race = db.get(ar[0])
        template_values = {}
        template_values['id'] = ar[0]
        template_values['username'] = race.user.nickname()
        template_values['start_time'] = race.start_time
        template_values['finish_time'] = race.finish_time
        template_values['total_time'] = race.total_time
        template_values['current_user'] = users.get_current_user()
        template_values['logout'] = users.create_logout_url('/')
        self.render("showrace.html", **template_values)


class RemoveRace(BaseHandler):
    """Handler for removing a race from the datastore"""
    def get(self, *ar):
        race = db.get(ar[0])
        template_values = {}
        template_values['id'] = ar[0]
        template_values['username'] = race.user.nickname()
        template_values['start_time'] = race.start_time
        template_values['finish_time'] = race.finish_time
        template_values['total_time'] = race.total_time
        template_values['current_user'] = users.get_current_user()
        template_values['logout'] = users.create_logout_url('/')
        self.render("remove.html", **template_values)

    def post(self, *ar):
        db.get(ar[0]).delete()
        self.redirect_fail("/", "Lopp raderat.")


class MyRaces(BaseHandler):
    """Handler to show all of a specific users races"""
    @tornado.web.authenticated
    def get(self):
        races = Race.all()
        races.filter("user =", users.get_current_user())
        races.order("-start_time")
        template_values = {}
        template_values['races'] = races
        template_values['current_user'] = users.get_current_user()
        template_values['logout'] = users.create_logout_url('/')
        self.render("myraces.html", **template_values)


class Information(BaseHandler):
    """Handler for the information page"""
    def get(self):
        template_values = {}
        template_values['current_user'] = users.get_current_user()
        template_values['logout'] = users.create_logout_url('/')
        self.render("info.html", **template_values)


settings = {
    "template_path": os.path.join(os.path.dirname(__file__), "templates"),
    # "xsrf_cookies": True,
    "autoescape": None,
}
application = tornado.wsgi.WSGIApplication([
    (r"/", MainHandler),
    (r"/upload", UploadHandler),
    (r"/img", GetImage),
    (r"/showrace/(.*)", ShowRace),
    (r"/removerace/(.*)", RemoveRace),
    ("/myraces", MyRaces),
    ('/info', Information),
], **settings)


def main():
    wsgiref.handlers.CGIHandler().run(application)


if __name__ == '__main__':
    main()
