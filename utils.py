
import pytz
from os import path as ospath
from trytond.pool import Pool
from datetime import datetime

_cached_timezone = None

def get_timezone():
    '''returns the current timezone specified for the company/facility 
    or the default which is the value in /etc/localtime'''
    global _cached_timezone
    if _cached_timezone:
        return _cached_timezone
    else:
        try:
            company = Transaction().context.get('company')
            company = Pool().get('company.company')(company)
            tz = company.get_timezone
        except:
            tz = None

    if tz:
        _cached_timezone = pytz.timezone(tz)
    elif ospath.exists('/etc/localtime'):
        _cached_timezone = pytz.tzfile.build_tzinfo('local',open('/etc/localtime', 'rb'))
    else:
        raise pytz.UnknownTimeZoneError('Cannot find suitable time zone')

    return _cached_timezone

def localtime(current):
    '''returns a datetime object with local timezone. naive datetime
    assumed to be in utc'''
    tz = get_timezone()
    if current.tzinfo is None:
        # assume it's utc. convert it to timezone aware
        cdt = datetime(*current.timetuple()[:6], tzinfo=pytz.UTC,
                       microsecond=current.microsecond)
    else:
        cdt = current
    return cdt.astimezone(tz)
