import pandas as pd
from padData import remove_weekends
from utilities import formatMinutes,formatProcedureTimes,get_procedure_date
from overlapProceduresOpt import get_complete_overlap_procedures,get_overlap_early_procedures,get_complete_overlap_procedures,get_overlap_late_procedures
from overlapProceduresOpt import get_early_procedures, get_late_procedures, get_prime_time_procedures
import pytz;
from datetime import date, time,datetime;
from primeTimeProcedures import RoomOptions
from datetime import  timedelta

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

def get_number_unique_rooms(procedure_rooms):
    return procedure_rooms.drop_duplicates().shape[0]

def get_weekdays(startDate, endDate, weekday):
    d = endDate - startDate
    days = 0
    for i in range(d.days+1):
        day = startDate + timedelta(days=i)
        if(day.weekday() == weekday):
            days = days + 1
    return days


def get_total_pt_minutes(rooms,procedure_rooms, prime_time_hours,roomSelectionOption,selectedRooms,startDate, endDate):
    pt_start, pt_end = get_pt_times(prime_time_hours['start'], prime_time_hours['end'])
    # print('pt start', pt_start),
    # print('pt_end', pt_end)
    pt_minutes_per_room = ((pt_end - pt_start).total_seconds())/60
    # print('pt_minutesroom', pt_minutes_per_room)
    # print('room selection option', roomSelectionOption, type(roomSelectionOption))
    # print('roomoptons All', RoomOptions.All)
    # print('rooms', rooms)
    # print('days', days)
    if (roomSelectionOption == 1):
        return len(rooms) * pt_minutes_per_room 
    elif (roomSelectionOption == 2):
        return len(selectedRooms)* pt_minutes_per_room 
    else:
        num_rooms = get_number_unique_rooms(procedure_rooms)
        return num_rooms * pt_minutes_per_room 




# def get_pt_times2(prime_time_start, prime_time_end):
#     pt_start_hours, pt_start_minutes = get_pt_hours_minutes(prime_time_start)
#     # timezone = pytz.timezone("US/Central")
#     timezone = pytz.timezone("US/Central")
#     pt_start = timezone.localize(datetime.combine(date(2023, 1, 1), 
#                             time(pt_start_hours, pt_start_minutes,0)))
#     pt_end_hours, pt_end_minutes = get_pt_hours_minutes(prime_time_end)
#     pt_end = timezone.localize(datetime.combine(date(2023, 1, 1), 
#                             time(pt_end_hours, pt_end_minutes,0)))
#     return pt_start, pt_end


def generate_pt_hours(procedures,prime_time_hours, prime_time_start, prime_time_end):
    prime_time_hours = get_complete_overlap_procedures(procedures,prime_time_hours, prime_time_start, prime_time_end)
    prime_time_hours = get_overlap_early_procedures(procedures, prime_time_hours,prime_time_start, prime_time_end)
    prime_time_hours = get_overlap_late_procedures(procedures, prime_time_hours, prime_time_start, prime_time_end)
    prime_time_hours = get_early_procedures(procedures, prime_time_hours, prime_time_start)
    prime_time_hours = get_late_procedures(procedures,prime_time_hours, prime_time_end)
    prime_time_hours = get_prime_time_procedures(procedures, prime_time_hours, prime_time_start, prime_time_end)
    return prime_time_hours

def remove_weekends_procedures(data):
    return data[(data['weekday'] != 6) & (data['weekday'] != 7)]



def get_prime_time_procedures_from_range(data, prime_time_start, prime_time_end):
    data = remove_weekends_procedures(data)
    prime_time_hours = pd.DataFrame(columns=prime_time_hours_cols)
    data['prime_time_minutes'] = 0
    data['non_prime_time_minutes'] = 0
    prime_time_start, prime_time_end = get_pt_times (prime_time_start, prime_time_end)
    procedures = data
    prime_time_hours = generate_pt_hours(procedures,prime_time_hours, prime_time_start, prime_time_end)
    return prime_time_hours.sort_values(by=['local_start_time', 'local_end_time','room'])


def get_prime_time_procedure_hours(data, prime_time_start, prime_time_end,start_date):
    data = remove_weekends(start_date, data)
    prime_time_hours = pd.DataFrame(columns=prime_time_hours_cols)
    data['prime_time_minutes'] = 0
    data['non_prime_time_minutes'] = 0
    prime_time_start, prime_time_end = get_pt_times (prime_time_start, prime_time_end)
    procedures = data
    prime_time_hours = generate_pt_hours(procedures,prime_time_hours, prime_time_start, prime_time_end)
    return prime_time_hours.sort_values(by=['local_start_time', 'local_end_time','room'])

def get_unit_report_hours(data):
    unit_report_hours = [{'id': index,
                          'calendar': {
                              'unit': row.unit,'NPI': row.NPI,'procedureDate': str(row.procedureDtNoTime), 
                              'room': row.room, 'prime_time_minutes': row.prime_time_minutes,'non_prime_time_minutes':row.non_prime_time_minutes, 'weekday': str(row.weekday) },
                            'grid': {'unit': row.unit,'room': row.room,'NPI':row.NPI, 'procedureDate': str(row.procedureDtNoTime),
                                     'prime_time_minutes': str(row.prime_time_minutes),'non_prime_time_minutes':str(row.non_prime_time_minutes),'block_status':row.block_status },
                            'details': {'room':row.room, 'fullName': row.fullName,'local_start_time': formatProcedureTimes(row.local_start_time),'local_end_time': formatProcedureTimes(row.local_end_time), 
                                        'procedureName': row.procedureName,'duration':formatMinutes(row.duration),'procedureDate': str(row.procedureDtNoTime)}
                          } for index, row in data.iterrows()] 
    return unit_report_hours


pt_total_cols = ['date', 'dayOfWeek', 'display','nonPTMinutes', 'ptMinutes', 'subHeading1', 'subHeading2']

def get_pt_totals(data,basePTMinutes,startDate,endDate):
    pt_totals = pd.DataFrame(columns=pt_total_cols)
    for i in range(5):
        curData = data[data['weekday'] == (i + 1)]
        num_days = get_weekdays(startDate,endDate,i)
        total_pt_minutes = basePTMinutes * num_days
        title = 'PT Totals'
        dayOfWeek = i + 1
        ptMinutes = curData['prime_time_minutes'].sum()
        nonptMinutes = curData['non_prime_time_minutes'].sum()
        subHeading1 = formatMinutes(ptMinutes)
        subHeading2 = formatMinutes(nonptMinutes)
        display = str(int(round(ptMinutes/total_pt_minutes*100,0))) +'%'
        pt_totals = pt_totals.append({'date':title,'dayOfWeek':dayOfWeek,'ptMinutes': ptMinutes,'nonPTMinutes':nonptMinutes,
                          'subHeading1':subHeading1,'subHeading2':subHeading2,'display':display},ignore_index=True)

    unit_pt_totals= [{'date': 'PT TOTALS', 'dayOfWeek': row.dayOfWeek,'ptMinutes': str(row.ptMinutes), 
                              'notPTMinutes': row.nonPTMinutes, 'subHeading1': row.subHeading1,'subHeading2':row.subHeading2, 'display': row.display }
                          for index, row in pt_totals.iterrows()] 
    return unit_pt_totals
