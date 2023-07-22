from datetime import  datetime;

def get_procedure_date(dt):
    return datetime.strptime(dt, '%Y-%m-%d')

def get_block_date_with_time(dt):
    return datetime.strptime(dt, '%Y-%m-%dT%H:%M:%S.%f%z')

def formatProcedureTimes(date):
    return date.strftime("%I:%M %p")

def formatMinutes(minutes):
       h, m = divmod(minutes, 60)
       return '{:d} hours {:02d} minutes'.format(int(h), int(m))