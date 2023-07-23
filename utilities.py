
from datetime import date, timedelta, datetime, timezone;
import pytz
import calendar;

def get_procedure_date(dt):
    return datetime.strptime(dt, '%Y-%m-%d')

def get_block_date_with_time(dt):
    return datetime.strptime(dt, '%Y-%m-%dT%H:%M:%S.%f%z')

def get_procedure_date_with_time(dt):
    return datetime.strptime(dt, '%Y-%m-%d %H:%M:%S').strftime("%Y-%m-%d")

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


def get_pt_hours_minutes(pt):
    hour_minutes = pt.split(':')
    return hour_minutes[0], hour_minutes[1]

def getTimeChange(date, hour, minute): 
    tz = pytz.timezone("US/Central")
    new_date= tz.localize(datetime(date.year, date.month, date.day, 0), is_dst=None)                                                                           
    total_time = int(hour)*60 + int(minute)
    new_date = ((new_date + timedelta(minutes=total_time)))
    return (new_date)


def getPrimeTimeWithDate(date, prime_time_start, prime_time_end):
    prime_start_hour, prime_start_minutes = get_pt_hours_minutes(prime_time_start)
    prime_end_hour, prime_end_minutes = get_pt_hours_minutes(prime_time_end)
    new_prime_time_start = getTimeChange(date, prime_start_hour, prime_start_minutes)
    new_prime_time_end = getTimeChange(date,prime_end_hour, prime_end_minutes)
    return new_prime_time_start, new_prime_time_end

def convert_zulu_to_central_time_from_date(date):
    return date.replace(tzinfo=timezone.utc).astimezone(pytz.timezone("US/Central"))

def create_zulu_datetime_from_string(date_string):
    return datetime.strptime(date_string,"%Y-%m-%dT%H:%M:%S.%fZ")

def get_date_from_datetime(date_time):
    return date_time.date()