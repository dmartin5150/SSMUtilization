import pandas as pd
from padData import remove_weekends
from utilities import getPrimeTimeWithDate,formatMinutes,get_procedure_date_with_time,formatProcedureTimes
from primeTimeProcedures import get_procedures_from_date
from overlapProcedures import get_complete_overlap_procedures,get_overlap_early_procedures,get_complete_overlap_procedures,get_overlap_late_procedures
from overlapProcedures import get_early_procedures, get_late_procedures, get_prime_time_procedures
import pytz;
from datetime import date, time,datetime, timezone;

prime_time_hours_cols = ['duration', 'unit', 'procedureName', 'NPI', 'room', 'procedureDate',
       'startTime', 'endTime', 'name', 'lastName', 'npi', 'fullName',
       'new_procedureDate', 'local_start_time', 'local_end_time',
       'prime_time_minutes','non_prime_time_minutes']


def getProcedureDates(data): 
    return data['procedureDate'].drop_duplicates().sort_values().to_list()

def get_pt_hours_minutes(pt):
    hour_minutes = pt.split(':')
    return int(hour_minutes[0]), int(hour_minutes[1])

def get_pt_times (prime_time_start, prime_time_end):
    timezone = pytz.timezone("US/Central")
    pt_start_hours, pt_start_minutes = get_pt_hours_minutes(prime_time_start)
    pt_start = timezone.localize(datetime.combine(date(2023, 1, 1), 
                          time(pt_start_hours, pt_start_minutes,0)))
    pt_end_hours, pt_end_minutes = get_pt_hours_minutes(prime_time_end)
    pt_end = timezone.localize(datetime.combine(date(2023, 1, 1), 
                          time(pt_end_hours, pt_end_minutes,0)))
    return pt_start, pt_end



def get_prime_time_procedure_hours(data, prime_time_start, prime_time_end,start_date):
    data = remove_weekends(start_date, data)
    prime_time_hours = pd.DataFrame(columns=prime_time_hours_cols)
    data['prime_time_minutes'] = 0
    data['non_prime_time_minutes'] = 0
    procedureDates = getProcedureDates(data)
    for procedure in procedureDates:
        prime_time_start, prime_time_end = get_pt_times (prime_time_start, prime_time_end)
        procedures = get_procedures_from_date(data, procedure)
        prime_time_hours = get_complete_overlap_procedures(procedures,prime_time_hours, prime_time_start, prime_time_end)
        prime_time_hours = get_overlap_early_procedures(procedures, prime_time_hours,prime_time_start, prime_time_end)
        prime_time_hours = get_overlap_late_procedures(procedures, prime_time_hours, prime_time_start, prime_time_end)
        prime_time_hours = get_early_procedures(procedures, prime_time_hours, prime_time_start)
        prime_time_hours = get_late_procedures(procedures,prime_time_hours, prime_time_end)
        prime_time_hours = get_prime_time_procedures(procedures, prime_time_hours, prime_time_start, prime_time_end)
    return prime_time_hours