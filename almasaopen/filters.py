from datetime import datetime, timedelta, date

def format(time):
    """Format seconds to HH:MM:SS format"""
    return str(timedelta(seconds=time))

def formatd(indate):
    """Format datetime to just date"""
    return indate.strftime("%Y-%m-%d")
  
def formatt(indate):
    """Format datetime to just date"""
    return indate.strftime("%H:%M:%S")