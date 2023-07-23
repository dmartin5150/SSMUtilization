import pandas as pd

def get_procedures_overlap_early_and_late(data, startTime, endTime):
    return data[(data['local_start_time'] < startTime) & (data['local_end_time']> endTime)].sort_values(by=['local_start_time', 'local_end_time'])


def get_procedures_overlap_early(data, startTime, endTime):
    return data[(data['local_start_time'] < startTime) & (data['local_end_time'] > startTime) & (data['local_end_time']< endTime)].sort_values(by=['local_start_time', 'local_end_time'])

def get_complete_overlap_procedures(procedures,hours,prime_time_start, prime_time_end):
    overlap_procedures = get_procedures_overlap_early_and_late(procedures,prime_time_start, prime_time_end)
    prime_time_minutes = (prime_time_end - prime_time_start).total_seconds()/60
    if (len(overlap_procedures) > 0):
        overlap_procedures['prime_time_minutes'] = prime_time_minutes
        overlap_procedures['non_prime_time_minutes'] = 0
        overlap_procedures['non_prime_time_minutes'] = overlap_procedures.apply(lambda row: row['non_prime_time_minutes'] + ((prime_time_start - row['local_start_time']).total_seconds()/60))
        overlap_procedures['non_prime_time_minutes'] = overlap_procedures.apply(lambda row: row['non_prime_time_minutes'] + ((row['local_end_time']- prime_time_end).total_seconds()/60))
        hours = pd.concat([overlap_procedures, hours])
    return hours


def get_overlap_early_procedures(procedures, hours, prime_time_start, prime_time_end):
    overlap_procedures = get_procedures_overlap_early(procedures, prime_time_start,prime_time_end)
    if (len(overlap_procedures) > 0): 
        overlap_procedures['non_prime_time_minutes'] = overlap_procedures.apply(lambda row:((prime_time_start - row['local_start_time']).total_seconds()/60))
        overlap_procedures['prime_time_minutes'] = overlap_procedures.apply(lambda row:((row['local_end_time']- prime_time_start).total_seconds()/60))
        hours = pd.concat([overlap_procedures, hours])
    return hours


def get_procedures_overlap_late(data,startTime, endTime):
    return data[(data['local_start_time'] > startTime) & (data['local_start_time'] < endTime) & (data['local_end_time'] > endTime)].sort_values(by=['local_start_time','local_end_time'])

def get_overlap_late_procedures(procedures, hours,prime_time_start, prime_time_end):
    overlap_procedures = get_procedures_overlap_late(procedures,prime_time_start, prime_time_end)
    if (len(overlap_procedures) > 0): 
        overlap_procedures['non_prime_time_minutes'] = overlap_procedures.apply(lambda row:((row['local_end_time'] - prime_time_end).total_seconds()/60))
        overlap_procedures['prime_time_minutes'] = overlap_procedures.apply(lambda row:((prime_time_end - row['local_start_time']).total_seconds()/60))
        hours = pd.concat([overlap_procedures, hours])
    return hours

def get_procedures_before_time(data, startTime):
    return data[data['local_end_time'] < startTime].sort_values(by=['local_start_time', 'local_end_time'])

def get_early_procedures(procedures, hours, prime_time_start):
    early_procedures= get_procedures_before_time(procedures, prime_time_start)
    if (len(early_procedures) > 0): 
        early_procedures['non_prime_time_minutes'] = early_procedures.apply(lambda row:((row['local_end_time'] - row['local_start_time']).total_seconds()/60))
        early_procedures['prime_time_minutes'] = 0
        hours = pd.concat([early_procedures, hours])
    return hours

def get_procedures_after_time(data, endTime):
    return data[endTime <= data['local_start_time']].sort_values(by=['local_start_time','local_end_time'])

def get_late_procedures(procedures, hours, prime_time_end):
    late_procedures= get_procedures_after_time(procedures, prime_time_end)
    if (len(late_procedures) > 0): 
        late_procedures['non_prime_time_minutes'] = late_procedures.apply(lambda row:((row['local_end_time'] - row['local_start_time']).total_seconds()/60))
        late_procedures['prime_time_minutes'] = 0
        hours = pd.concat([late_procedures, hours])
    return hours 

def get_procedures_between_time(data, startTime, endTime):
    return data[(data['local_start_time'] >= startTime ) & (data['local_end_time'] <= endTime)].sort_values(by=['local_start_time', 'local_end_time'])


def get_prime_time_procedures(procedures, hours, prime_time_start, prime_time_end):
    prime_time_procedures= get_procedures_between_time(procedures,prime_time_start, prime_time_end)
    if (len(prime_time_procedures) > 0): 
            prime_time_procedures['prime_time_minutes'] = prime_time_procedures.apply(lambda row:((row['local_end_time'] - row['local_start_time']).total_seconds()/60))
            prime_time_procedures['non_prime_time_minutes'] = 0
            hours = pd.concat([prime_time_procedures, hours])
    return hours 
