from google.appengine.ext import webapp
from datetime import datetime, timedelta, date


register = webapp.template.create_template_register()

def format(time):
    """Format seconds to HH:MM:SS format"""
    return str(timedelta(seconds=time))

def formatd(indate):
    """Format datetime to just date"""
    return indate.strftime("%Y-%m-%d")
  
def formatt(indate):
    """Format datetime to just date"""
    return indate.strftime("%H:%M:%S")
    
    
register.filter(format)
register.filter(formatd)
register.filter(formatt)