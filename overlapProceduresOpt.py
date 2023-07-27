import pandas as pd

def get_procedures_overlap_early_and_late(data, startTime, endTime):
    return data[(data['ptStart'] < startTime) & (data['ptEnd']> endTime)]


def get_procedures_overlap_early(data, startTime, endTime):
    return data[(data['ptStart'] < startTime) & (data['ptEnd'] > startTime) & (data['ptEnd']< endTime)]

def get_complete_overlap_procedures(procedures,hours,prime_time_start, prime_time_end):
    overlap_procedures = get_procedures_overlap_early_and_late(procedures.copy(),prime_time_start, prime_time_end)
    prime_time_minutes = (prime_time_end - prime_time_start).total_seconds()/60
    if (len(overlap_procedures) > 0):
        overlap_procedures['prime_time_minutes'] = prime_time_minutes
        overlap_procedures['non_prime_time_minutes'] = 0
        overlap_procedures['non_prime_time_minutes'] = overlap_procedures.apply(lambda row: row['non_prime_time_minutes'] + ((prime_time_start - row['ptStart']).total_seconds()/60),axis=1)
        overlap_procedures['non_prime_time_minutes'] = overlap_procedures.apply(lambda row: row['non_prime_time_minutes'] + ((row['ptEnd']- prime_time_end).total_seconds()/60),axis=1)
        hours = pd.concat([overlap_procedures, hours])
    return hours


def get_overlap_early_procedures(procedures, hours, prime_time_start, prime_time_end):
    overlap_procedures = get_procedures_overlap_early(procedures.copy(), prime_time_start,prime_time_end)
    if (len(overlap_procedures) > 0): 
        overlap_procedures['non_prime_time_minutes'] = overlap_procedures.apply(lambda row:((prime_time_start - row['ptStart']).total_seconds()/60),axis=1)
        overlap_procedures['prime_time_minutes'] = overlap_procedures.apply(lambda row:((row['ptEnd']- prime_time_start).total_seconds()/60),axis=1)
        hours = pd.concat([overlap_procedures, hours])
    return hours


def get_procedures_overlap_late(data,startTime, endTime):
    return data[(data['ptStart'] > startTime) & (data['ptStart'] < endTime) & (data['ptEnd'] > endTime)]

def get_overlap_late_procedures(procedures, hours,prime_time_start, prime_time_end):
    overlap_procedures = get_procedures_overlap_late(procedures.copy(),prime_time_start, prime_time_end)
    if (len(overlap_procedures) > 0): 
        overlap_procedures['non_prime_time_minutes'] = overlap_procedures.apply(lambda row:((row['ptEnd'] - prime_time_end).total_seconds()/60),axis=1)
        overlap_procedures['prime_time_minutes'] = overlap_procedures.apply(lambda row:((prime_time_end - row['ptStart']).total_seconds()/60),axis=1)
        hours = pd.concat([overlap_procedures, hours])
    return hours

def get_procedures_before_time(data, startTime):
    return data[data['ptEnd'] < startTime]

def get_early_procedures(procedures, hours, prime_time_start):
    early_procedures= get_procedures_before_time(procedures.copy(), prime_time_start)
    if (len(early_procedures) > 0): 
        early_procedures['non_prime_time_minutes'] = early_procedures.apply(lambda row:((row['ptEnd'] - row['ptStart']).total_seconds()/60),axis=1)
        early_procedures['prime_time_minutes'] = 0
        hours = pd.concat([early_procedures, hours])
    return hours

def get_procedures_after_time(data, endTime):
    # print('endtime', endTime)
    # print('late procedures', data.columns)
    return data[endTime <= data['ptStart']]

def get_late_procedures(procedures, hours, prime_time_end):
    late_procedures= get_procedures_after_time(procedures.copy(), prime_time_end)
    # print('late procedures', late_procedures)
    if (len(late_procedures) > 0): 
        late_procedures['non_prime_time_minutes'] = late_procedures.apply(lambda row:((row['ptEnd'] - row['ptStart']).total_seconds()/60),axis=1)
        late_procedures['prime_time_minutes'] = 0
        hours = pd.concat([late_procedures, hours])
    return hours 

def get_procedures_between_time(data, startTime, endTime):
    return data[(data['ptStart'] >= startTime ) & (data['ptEnd'] <= endTime)]


def get_prime_time_procedures(procedures, hours, prime_time_start, prime_time_end):
    prime_time_procedures= get_procedures_between_time(procedures.copy(),prime_time_start, prime_time_end)
    if (len(prime_time_procedures) > 0): 
            prime_time_procedures['prime_time_minutes'] = prime_time_procedures.apply(lambda row:((row['ptEnd'] - row['ptStart']).total_seconds()/60),axis=1)
            prime_time_procedures['non_prime_time_minutes'] = 0
            hours = pd.concat([prime_time_procedures, hours])
    return hours 
