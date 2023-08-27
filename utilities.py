
from datetime import date,time, timedelta, datetime, timezone;
import pytz
import calendar;

def get_procedure_date(dt):
    return datetime.strptime(dt, '%Y-%m-%d')

def get_block_date_with_time(dt):
    return datetime.strptime(dt, '%Y-%m-%dT%H:%M:%S.%f%z')

def get_block_date_with_timezone(dt):
    return datetime.strptime(dt, '%Y-%m-%d %H:%M:%S%f%z')

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
def create_date_with_time(dt, tm):
    # time example 10:00 AM
    timezone = pytz.timezone("US/Central")
    # print('time', tm, 'type', type(tm))
    time_components = tm.split(':')
    hour = time_components[0][-2:]
    minute_components = time_components[1].split(' ') 
    minutes= minute_components[0]
    # print('hour', hour, 'minutes', minutes)
    if ('PM' in minute_components[1]):
        if (int(hour) != 12):
            hour = int(hour) + 12
    return timezone.localize(datetime(dt.year, dt.month, dt.day,int(hour), int(minutes), 0))   


def get_text_of_time(dt):
    curHour = dt.hour
    curMinute = dt.minute
    merideim = 'AM'
    if (curHour == 12):
        merideim = 'PM'
    if (curHour > 12):
        curHour = curHour - 12
        merideim = 'PM'
    print ('text from time', dt,f"{curHour}:{curMinute} {merideim}" )
    return f"{curHour}:{curMinute} {merideim}"
    



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

def get_date_range_with_date(start_date, months):
    delta = timedelta(days=-1)
    if start_date.month == 12:
        next_month = 1
        next_year = start_date.year +1
    else:
        next_month = start_date.month +months
        next_year = start_date.year
    end_date = date(next_year, next_month,1) + delta
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

def create_zulu_datetime_from_string_format2(date_string):
    return datetime.strptime(date_string,'%Y-%m-%d %H:%M:%S%z')

def get_date_from_datetime(date_time):
    return date_time.date()

def get_procedure_date_with_time(dt):
    return datetime.strptime(dt, '%Y-%m-%d %H:%M:%S').strftime("%Y-%m-%d")

def cast_to_cst(curDateTime):
    timezone = pytz.timezone("US/Central")
    return timezone.localize(datetime.combine(date(curDateTime.year, curDateTime.month, curDateTime.day), 
                            time(curDateTime.hour, curDateTime.minute,curDateTime.second)))
    

    







