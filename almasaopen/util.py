import datetime

HOUR_SEC = 3600
MIN_SEC = 60

class CET(datetime.tzinfo):

    HOUR = datetime.timedelta(hours=1)

    def utcoffset(self, dt):
        return self.HOUR + self.dst(dt)

    def dst(self, dt):
        d = datetime.datetime(dt.year, 4, 1) # DST starts last Sunday in March
        self.dston = d - datetime.timedelta(days=d.weekday() + 1)
        d = datetime.datetime(dt.year, 11, 1) # ends last Sunday in October
        self.dstoff = d - datetime.timedelta(days=d.weekday() + 1)
        if self.dston <=  dt.replace(tzinfo=None) < self.dstoff:
            return datetime.timedelta(hours=1)
        else:
            return datetime.timedelta(0)

    def tzname(self,dt):
         return "CET"


def pluralize(count, singular, plural):
    return "%d %s" % (count, singular if count == 1 else plural)


def duration_to_text(duration):
    days = duration.days
    if days:
        return pluralize(days, "dag", "dagar")
    hours, rest = divmod(duration.seconds, HOUR_SEC)
    if hours:
        return pluralize(hours, "timme", "timmar")
    minutes, rest = divmod(rest, MIN_SEC)
    if minutes:
        return pluralize(minutes, "minut", "minuter")
    return pluralize(rest, "sekund", "sekunder")    