

def get_procedures_overlap_early_and_late(data, startTime, endTime):
    return data[(data['local_start_time'] < startTime) & (data['local_end_time']> endTime)].sort_values(by=['local_start_time', 'local_end_time'])


def get_procedures_overlap_early(data, startTime, endTime):
    return data[(data['local_start_time'] < startTime) & (data['local_end_time'] > startTime) & (data['local_end_time']< endTime)].sort_values(by=['local_start_time', 'local_end_time'])

def get_complete_overlap_procedures(procedures,hours,prime_time_start, prime_time_end):
    overlap_procedures = get_procedures_overlap_early_and_late(procedures,prime_time_start, prime_time_end)
    prime_time_minutes = (prime_time_end - prime_time_start).total_seconds()/60
    if (len(overlap_procedures) > 0):
        for index, procedure in overlap_procedures.iterrows():
            non_prime_time_minutes =0
            non_prime_time_minutes += (prime_time_start - procedure['local_start_time']).total_seconds()/60
            non_prime_time_minutes += (procedure['local_end_time']- prime_time_end).total_seconds()/60
            procedure['prime_time_minutes'] = prime_time_minutes
            procedure['non_prime_time_minutes'] = non_prime_time_minutes
            hours = hours.append(procedure, ignore_index=True)
    return hours




def get_overlap_early_procedures(procedures, hours, prime_time_start, prime_time_end):
    overlap_procedures = get_procedures_overlap_early(procedures, prime_time_start,prime_time_end)
    if (len(overlap_procedures) > 0): 
        for index, procedure in overlap_procedures.iterrows():
            procedure['non_prime_time_minutes'] = (prime_time_start - procedure['local_start_time']).total_seconds()/60
            procedure['prime_time_minutes'] = (procedure['local_end_time'] - prime_time_start).total_seconds()/60
            hours= hours.append(procedure, ignore_index=True)
    return hours


def get_procedures_overlap_late(data,startTime, endTime):
    return data[(data['local_start_time'] > startTime) & (data['local_start_time'] < endTime) & (data['local_end_time'] > endTime)].sort_values(by=['local_start_time','local_end_time'])

def get_overlap_late_procedures(procedures, hours,prime_time_start, prime_time_end):
    overlap_procedures = get_procedures_overlap_late(procedures,prime_time_start, prime_time_end)
    if (len(overlap_procedures) > 0): 
        for index, procedure in overlap_procedures.iterrows():
            procedure['prime_time_minutes'] = (prime_time_end - procedure['local_start_time']).total_seconds()/60
            procedure['non_prime_time_minutes'] = (procedure['local_end_time'] - prime_time_end).total_seconds()/60
            hours= hours.append(procedure, ignore_index=True)
    return hours

def get_procedures_before_time(data, startTime):
    return data[data['local_end_time'] < startTime].sort_values(by=['local_start_time', 'local_end_time'])

def get_early_procedures(procedures, hours, prime_time_start):
    early_procedures= get_procedures_before_time(procedures, prime_time_start)
    if (len(early_procedures) > 0): 
        for index, procedure in early_procedures.iterrows():
            procedure['non_prime_time_minutes'] = (procedure['local_end_time'] - procedure['local_start_time']).total_seconds()/60
            procedure['prime_time_minutes'] = 0
            hours= hours.append(procedure, ignore_index=True)
    return hours

def get_procedures_after_time(data, endTime):
    return data[endTime <= data['local_start_time']].sort_values(by=['local_start_time','local_end_time'])

def get_late_procedures(procedures, hours, prime_time_end):
    late_procedures= get_procedures_after_time(procedures, prime_time_end)
    if (len(late_procedures) > 0): 
        for index, procedure in late_procedures.iterrows():
            procedure['non_prime_time_minutes'] = (procedure['local_end_time'] - procedure['local_start_time']).total_seconds()/60
            procedure['prime_time_minutes'] = 0
            hours= hours.append(procedure, ignore_index=True)
    return hours 

def get_procedures_between_time(data, startTime, endTime):
    return data[(data['local_start_time'] >= startTime ) & (data['local_end_time'] <= endTime)].sort_values(by=['local_start_time', 'local_end_time'])


def get_prime_time_procedures(procedures, hours, prime_time_start, prime_time_end):
    prime_time_procedures= get_procedures_between_time(procedures,prime_time_start, prime_time_end)
    if (len(prime_time_procedures) > 0): 
        for index, procedure in prime_time_procedures.iterrows():
            procedure['prime_time_minutes'] = (procedure['local_end_time'] - procedure['local_start_time']).total_seconds()/60
            procedure['non_prime_time_minutes'] = 0
            hours= hours.append(procedure, ignore_index=True)
    return hours 


