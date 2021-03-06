import logging
import datetime

from google.appengine.ext import webapp

import util

_SE_MONTH_NAMES = {
    1: "januari", 2: "februari", 3: "mars", 4: "april", 5: "maj", 6: "juni",
    7: "juli", 8: "augusti", 9: "september", 10: "oktober", 11: "november",
    12: "december"
}

register = webapp.template.create_template_register()

def format(time):
    """Format seconds to HH:MM:SS format"""
    return str(datetime.timedelta(seconds=time))

def formatd(indate):
    """Format datetime to just date"""
    return util.utc_as_cet(indate).strftime("%Y-%m-%d")
  
def formatdv(indate):
    """Format datetime to just date"""
    month_name = _SE_MONTH_NAMES.get(indate.month, "sommari")
    return util.utc_as_cet(indate).strftime("%d %%s %Y") % month_name

def formatdvsy(indate):
    month_name = _SE_MONTH_NAMES.get(indate.month, "sommari")
    return util.utc_as_cet(indate).strftime("%d %%s") % month_name
  
def formatt(indate):
    """Format datetime to just time"""
    return util.utc_as_cet(indate).strftime("%H:%M:%S")

def formaty(indate):
    """Format datetime to just time"""
    return util.utc_as_cet(indate).strftime("%Y")

def duration_from_now(dt):
    duration = datetime.datetime.utcnow() - dt
    return util.duration_to_text(duration)


register.filter(format)
register.filter(formatd)
register.filter(formatdv)
register.filter(formatdvsy)
register.filter(formatt)
register.filter(formaty)
register.filter(duration_from_now)
