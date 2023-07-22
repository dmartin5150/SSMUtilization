
from datetime import date, timedelta, datetime;
import pytz
import calendar;

def get_procedure_date(dt):
    return datetime.strptime(dt, '%Y-%m-%d')

def get_block_date_with_time(dt):
    return datetime.strptime(dt, '%Y-%m-%dT%H:%M:%S.%f%z')

def formatProcedureTimes(date):
    return date.strftime("%I:%M %p")

def formatMinutes(minutes):
       h, m = divmod(minutes, 60)
       return '{:d} hours {:02d} minutes'.format(int(h), int(m))

def get_time(dt, tm):
    timezone = pytz.timezone("US/Central")
    time_components = tm.split(':')
    hour = time_components[0][-2:]
    minutes = time_components[1]
    return timezone.localize(datetime(dt.year, dt.month, dt.day,int(hour), int(minutes), 0))

def all_dates_current_month(month,year):
    number_of_days = calendar.monthrange(year, month)[1]
    first_date = date(year, month, 1)
    last_date = date(year, month, number_of_days)
    delta = last_date - first_date
    return [(first_date + timedelta(days=i)).strftime('%Y-%m-%d') for i in range(delta.days + 1)]