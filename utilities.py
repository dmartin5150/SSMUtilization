
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

def get_date_range(start_date):
    start_date = get_procedure_date(start_date).date()
    if start_date.month == 12:
        next_month = 1
        next_year = start_date.year +1
    else:
        next_month = start_date.month +1
        next_year = start_date.year
    end_date = date(next_year, next_month,1)
    return start_date, end_date