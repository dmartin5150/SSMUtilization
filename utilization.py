import pandas as pd;
from datetime import date, timedelta, datetime, timezone;
import calendar;
import json;
import pytz;
from flask import Flask, flash, request, redirect, render_template, send_from_directory,abort
from flask_cors import CORS
from calendar import Calendar, monthrange
import re

from facilityconstants import units,jriRooms, stmSTORRooms,MTORRooms,orLookUp,primetime_minutes_per_room
from utilities import formatProcedureTimes, formatMinutes
from blockData import get_block_data
from blockTemplates import get_block_templates
from blockSchedule import get_block_schedule
from gridBlockSchedule import get_grid_block_schedule
from blockDetails import get_block_details_data
from blockOwner import get_block_owner
from unitData import get_unit_data
from primeTimeProcedures import getPTProcedures
from roomDetails import get_room_details


app = Flask(__name__)
CORS(app)
app.secret_key = "seamless care" # for encrypting the session
app.config['CORS_HEADERS'] = 'Content-Type'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024



def get_procedure_date_without_time(dt):
    return datetime.date(dt)

def get_procedure_date(dt):
    # print('date', dt)
    return datetime.strptime(dt, '%Y-%m-%d')

def get_block_date_with_time(dt):
    return datetime.strptime(dt, '%Y-%m-%dT%H:%M:%S.%f%z')

block_data = pd.read_csv("blockslots.csv")
block_data = get_block_data(block_data)
block_templates = get_block_templates(block_data)
startDate = get_procedure_date('2023-6-1').date()
roomLists = [jriRooms,stmSTORRooms,MTORRooms]
block_no_release, block_schedule = get_block_schedule(startDate, block_templates,roomLists) 
grid_block_schedule = get_grid_block_schedule(startDate,roomLists,block_schedule)  
block_owner = pd.read_csv("blockowners.csv")
block_owner = get_block_owner(block_owner)




jriData = get_unit_data('JRIData.csv',grid_block_schedule)
STMSTORData = get_unit_data('STMSTORData.csv',grid_block_schedule)
MTORData = get_unit_data('MTORData.csv',grid_block_schedule)
dataFrameLookup = {'BH JRI': jriData, 'STM ST OR': STMSTORData, 'MT OR': MTORData}

# def formatMinutes(minutes):
#        h, m = divmod(minutes, 60)
#        return '{:d} hours {:02d} minutes'.format(int(h), int(m))




def all_dates_current_month(month,year):
    number_of_days = calendar.monthrange(year, month)[1]
    first_date = date(year, month, 1)
    last_date = date(year, month, number_of_days)
    delta = last_date - first_date
    return [(first_date + timedelta(days=i)).strftime('%Y-%m-%d') for i in range(delta.days + 1)]



def get_procedure_date_with_time(dt):
    return datetime.strptime(dt, '%Y-%m-%d %H:%M:%S').strftime("%Y-%m-%d")

def getDailyUtilization(unit, date,data, prime_minutes_per_room):

    prime_minutes = len(orLookUp[unit]) * prime_minutes_per_room
    procedure_date = get_procedure_date(date)
    daily_data = data[data['new_procedureDate'] == procedure_date]['duration']
    if len(daily_data) != 0: 
        total_surgical_time = daily_data.sum()
    else:
        total_surgical_time = 0
    return round(total_surgical_time/prime_minutes*100,0)

def get_daily_utilization_per_room(room,date, data,prime_minute_per_room):
    room_data = data[(data['new_procedureDate'] == date) & (data['room'] == room)]['duration']
    if len(room_data) != 0:
        room_surgical_time = room_data.sum()
    else:
        room_surgical_time = 0
    return round(room_surgical_time/prime_minute_per_room*100,0)

def pad_calendar_data(utilization):
    first_procedure_date = get_procedure_date(utilization[0]['date'])
    firstDayOfWeek =first_procedure_date.isoweekday()
    for i in range(firstDayOfWeek-1):
        utilization.insert(0, {'date':i, 'display':'Blank'})
    return utilization


def remove_weekend(data, procedure_date):
    return (data[data['procedureDtNoTime'] != procedure_date])


blank_cols = ['unit','NPI', 'procedureDate', 'room', 'prime_time_minutes', 'non-prime_time_minutes' ]

def addBlankCalendarData(data, procedure_date, unit): 
    blank_data = pd.DataFrame(columns=blank_cols)
    blank_data['unit'] = unit
    blank_data['NPI'] = '0'
    blank_data['procedure_date'] = procedure_date
    blank_data['room'] = '0'
    blank_data['prime_time_minutes'] = '0'
    blank_data['non_prime_time_minutes'] = '0'
    return data.append(blank_data, ignore_index=True)

def getBlankEntry (id, unit,date):
    return {'id': id, 'calendar': {'unit': unit, 'NPI': '0', 'procedureDate': date, 'room': 'none', 'prime_time_minutes': '0', 'non_prime_time_minutes': '0'}, 'grid': {'unit': unit, 'room': 'none', 'procedureDate': date, 'prime_time_minutes': '0', 'non_prime_time_minutes': '0'}, 'details': {'fullName': 'Blank', 'local_start_time': '00:00 PM', 'local_end_time': '00:00 PM', 'procedureName': 'Blank', 'duration': '0', 'procedureDate': date}}



def pad_data(pt_hours,unit,start_date):
    data = pt_hours['surgeryInfo']
    # print('data', data)
    procedure_dates = []
    for procedure in data:
        if procedure['calendar']['procedureDate'] in procedure_dates:
            continue
        procedure_dates.append(procedure['calendar']['procedureDate'])
    procedure_date = get_procedure_date(start_date)
    month_dates = all_dates_current_month(procedure_date.month, procedure_date.year)
    missing_dates = list(set(month_dates).difference(procedure_dates))
    weekdays = []
    for date in missing_dates:
        curDate = get_procedure_date(date)
        if ((curDate.isoweekday() == 6) | (curDate.isoweekday() == 7)):
            continue
        weekdays.append(date)
    for weekday in weekdays:
        idx = len(pt_hours) 
        blankEntry = getBlankEntry(idx,unit, weekday)
        pt_hours['surgeryInfo'].append(blankEntry)
    return pt_hours


#remove weekends 
def remove_weekends(start_date, data):
    procedure_date = get_procedure_date(start_date)
    month_dates = all_dates_current_month(procedure_date.month, procedure_date.year)
    for date in month_dates: 
        procedure_date = get_procedure_date(date).date()
        if ((procedure_date.isoweekday()==6) | (procedure_date.isoweekday() == 7)):
            data = remove_weekend(data,procedure_date)
            continue
    return data
        



def get_monthly_utilization(start_date,unit,data):
    utilization = []
    Saturday = 4
    Sunday = 5
    procedure_date = get_procedure_date(start_date)
    month_dates = all_dates_current_month(procedure_date.month ,procedure_date.year)
    for date in month_dates:
        procedure_date = get_procedure_date(date)
        # print('Procedure Day',procedure_date, procedure_date.weekday() )
        if ((procedure_date.isoweekday() == 6) | (procedure_date.isoweekday() == 7)):
            continue
        # print('in loop', date)
        daily_utilization = getDailyUtilization(unit, date,data,primetime_minutes_per_room)
        utilization.append({'date':date, 'display':str(int(daily_utilization)) + '%'})
    # utilization = pad_calendar_data(utilization)
    return json.dumps(utilization)


def get_daily_room_utilization(unit, selected_date,data):
    utilization = []
    procedure_date = get_procedure_date(selected_date)
    rooms = orLookUp[unit]
    for room in rooms:
        room_utlization = get_daily_utilization_per_room(room, procedure_date,data,primetime_minutes_per_room)
        utilization.append({'id':room,'name':room,'property':str(int(room_utlization)) + '%'})
    return json.dumps(utilization)


def get_data(request, string):
    data_requested = request[string]
    return data_requested

def get_providers(unit):
    data = dataFrameLookup[unit]
    data = data[data['NPI'] != 0]
    providers = data[['fullName','NPI']].copy()
    providers = providers.drop_duplicates().sort_values(by=['fullName'])
    surgeon_list = [{'id': row.NPI, 'name':row.fullName,'NPI':row.NPI, 'selected':True} for index, row in providers.iterrows() ] 
    return surgeon_list


unit_report_hours_cols = ['duration', 'unit', 'procedureName', 'NPI', 'room', 'procedureDate',
       'startTime', 'endTime', 'name', 'lastName', 'npi', 'fullName',
       'new_procedureDate', 'local_start_time', 'local_end_time',
       'prime_time_minutes','non_prime_time_minutes']

def get_unit_report_hours(data):
    unit_report_hours = [{'id': index,
                          'calendar': {
                              'unit': row.unit,'NPI': row.NPI,'procedureDate': str(row.procedureDtNoTime), 
                              'room': row.room, 'prime_time_minutes': row.prime_time_minutes,'non_prime_time_minutes':row.non_prime_time_minutes, 'weekday': str(row.weekday) },
                            'grid': {'unit': row.unit,'room': row.room,'NPI':row.NPI, 'procedureDate': str(get_procedure_date_with_time(str(row.new_procedureDate))),
                                     'prime_time_minutes': str(row.prime_time_minutes),'non_prime_time_minutes':str(row.non_prime_time_minutes),'block_status':row.block_status },
                            'details': {'room':row.room, 'fullName': row.fullName,'local_start_time': formatProcedureTimes(row.local_start_time),'local_end_time': formatProcedureTimes(row.local_end_time), 
                                        'procedureName': row.procedureName,'duration':formatMinutes(row.duration),'procedureDate': str(get_procedure_date_with_time(str(row.new_procedureDate)))}
                          } for index, row in data.iterrows()] 
    return unit_report_hours


def getProcedureDates(data): 
    return data['procedureDate'].drop_duplicates().sort_values().to_list()

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



def get_procedures_from_date(data, date):
    selected_date = datetime.strptime('2023-07-24', "%Y-%m-%d").date()
    return data[data['procedureDtNoTime'] == date.date()].sort_values(by=['local_start_time'])


def get_procedures_from_room(data, room):
    return data[data['room'] == room].sort_values(by=['local_start_time'])

def get_procedures_before_time(data, startTime):
    return data[data['local_end_time'] < startTime].sort_values(by=['local_start_time', 'local_end_time'])

def get_procedures_after_time(data, endTime):
    return data[endTime <= data['local_start_time']].sort_values(by=['local_start_time','local_end_time'])

def get_procedures_between_time(data, startTime, endTime):
    return data[(data['local_start_time'] >= startTime ) & (data['local_end_time'] <= endTime)].sort_values(by=['local_start_time', 'local_end_time'])

def get_procedures_overlap_early(data, startTime, endTime):
    return data[(data['local_start_time'] < startTime) & (data['local_end_time'] > startTime) & (data['local_end_time']< endTime)].sort_values(by=['local_start_time', 'local_end_time'])

def get_procedures_overlap_late(data,startTime, endTime):
    return data[(data['local_start_time'] > startTime) & (data['local_start_time'] < endTime) & (data['local_end_time'] > endTime)].sort_values(by=['local_start_time','local_end_time'])

def get_procedures_overlap_early_and_late(data, startTime, endTime):
    return data[(data['local_start_time'] < startTime) & (data['local_end_time']> endTime)].sort_values(by=['local_start_time', 'local_end_time'])


prime_time_hours_cols = ['duration', 'unit', 'procedureName', 'NPI', 'room', 'procedureDate',
       'startTime', 'endTime', 'name', 'lastName', 'npi', 'fullName',
       'new_procedureDate', 'local_start_time', 'local_end_time',
       'prime_time_minutes','non_prime_time_minutes']

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


def get_overlap_late_procedures(procedures, hours,prime_time_start, prime_time_end):
    overlap_procedures = get_procedures_overlap_late(procedures,prime_time_start, prime_time_end)
    if (len(overlap_procedures) > 0): 
        for index, procedure in overlap_procedures.iterrows():
            procedure['prime_time_minutes'] = (prime_time_end - procedure['local_start_time']).total_seconds()/60
            procedure['non_prime_time_minutes'] = (procedure['local_end_time'] - prime_time_end).total_seconds()/60
            hours= hours.append(procedure, ignore_index=True)
    return hours

def get_early_procedures(procedures, hours, prime_time_start):
    early_procedures= get_procedures_before_time(procedures, prime_time_start)
    if (len(early_procedures) > 0): 
        for index, procedure in early_procedures.iterrows():
            procedure['non_prime_time_minutes'] = (procedure['local_end_time'] - procedure['local_start_time']).total_seconds()/60
            procedure['prime_time_minutes'] = 0
            hours= hours.append(procedure, ignore_index=True)
    return hours

def get_late_procedures(procedures, hours, prime_time_end):
    late_procedures= get_procedures_after_time(procedures, prime_time_end)
    if (len(late_procedures) > 0): 
        for index, procedure in late_procedures.iterrows():
            procedure['non_prime_time_minutes'] = (procedure['local_end_time'] - procedure['local_start_time']).total_seconds()/60
            procedure['prime_time_minutes'] = 0
            hours= hours.append(procedure, ignore_index=True)
    return hours 


def get_prime_time_procedures(procedures, hours, prime_time_start, prime_time_end):
    prime_time_procedures= get_procedures_between_time(procedures,prime_time_start, prime_time_end)
    if (len(prime_time_procedures) > 0): 
        for index, procedure in prime_time_procedures.iterrows():
            procedure['prime_time_minutes'] = (procedure['local_end_time'] - procedure['local_start_time']).total_seconds()/60
            procedure['non_prime_time_minutes'] = 0
            hours= hours.append(procedure, ignore_index=True)
    return hours 


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

def getProcedures(unit,start_date):
    data = dataFrameLookup[unit]
    data = data[data['room'].isin(orLookUp[unit])]
    start_date, end_date = get_date_range(start_date)
    data = data[(data['procedureDtNoTime']>= start_date) & (data['procedureDtNoTime'] < end_date)]
    return data.copy()


def get_prime_time_procedure_hours(data, prime_time_start_time, prime_time_end_time,start_date):
    data = remove_weekends(start_date, data)
    prime_time_hours = pd.DataFrame(columns=prime_time_hours_cols)
    data['prime_time_minutes'] = 0
    data['non_prime_time_minutes'] = 0
    procedureDates = getProcedureDates(data)
    for procedure in procedureDates:
        prime_time_start, prime_time_end = getPrimeTimeWithDate(procedure, prime_time_start_time, prime_time_end_time)
        procedures = get_procedures_from_date(data, procedure)
        prime_time_hours = get_complete_overlap_procedures(procedures,prime_time_hours, prime_time_start, prime_time_end)
        prime_time_hours = get_overlap_early_procedures(procedures, prime_time_hours,prime_time_start, prime_time_end)
        prime_time_hours = get_overlap_late_procedures(procedures, prime_time_hours, prime_time_start, prime_time_end)
        prime_time_hours = get_early_procedures(procedures, prime_time_hours, prime_time_start)
        prime_time_hours = get_late_procedures(procedures,prime_time_hours, prime_time_end)
        prime_time_hours = get_prime_time_procedures(procedures, prime_time_hours, prime_time_start, prime_time_end)
    return prime_time_hours




def get_monthly_stats(npi, procedures):
    daysOfWeek = list(calendar.day_abbr)
    card =[]
    for i in range(1,6):
        weekday = daysOfWeek[i-1]
        provider_procedures = procedures[(procedures['NPI'] == npi) & (procedures['weekday'] == i)]
        num_procedures = provider_procedures.shape[0]
        minutes = formatMinutes(provider_procedures['duration'].sum())
        card.append({'day':weekday, 'procedure':num_procedures, 'hour':minutes})
    return card


def get_stats(unit,name, npi): 
    secondary_cards = []
    july_procedures = getProcedures(unit,'2023-7-1')
    # print('july procs', july_procedures)
    july_card_data = get_monthly_stats(npi, july_procedures)
    july_card = {'title':'July', 'data':july_card_data}
    june_procedures = getProcedures(unit,'2023-6-1')
    june_card_data = get_monthly_stats(npi, june_procedures)
    june_card = {'title':'June', 'data':june_card_data}
    may_procedures = getProcedures(unit,'2023-7-1')
    may_card_data = get_monthly_stats(npi, may_procedures)
    may_card = {'title':'May', 'data':may_card_data}
    april_procedures = getProcedures(unit,'2023-7-1')
    april_card_data = get_monthly_stats(npi, april_procedures)
    april_card = {'title':'April', 'data':april_card_data}
    secondary_cards.append(april_card)
    secondary_cards.append(may_card)
    secondary_cards.append(june_card)
  
    return {'surgeon':{'id':npi,'value':npi, 'label':name},
            'mainCard':july_card,
            'secondaryCards':secondary_cards}


def get_blocks_from_unit(block_schedule, unit):
    return block_schedule[block_schedule['unit'] == unit]

def get_block_dates (block_schedule):
    return block_schedule['blockDate'].drop_duplicates().sort_values().tolist()

def get_block_rooms (block_schedule):
    return block_schedule['room'].drop_duplicates().sort_values().tolist()


def create_block_owners(data, npis):
    data.reset_index(inplace=True)
    cur_npi_list = []
    num_rows = data.shape[0]
    for x in range(num_rows):
        cur_row = data.iloc[x]
        for npi in range (npis):
            if cur_row[f'npis[{npi}]'] == -1:
                break
            cur_npi_list.append(int(cur_row[f'npis[{npi}]'])) 

    return cur_npi_list




def getOwnerNPIs (data, flexId,num_npis):
    curData = data[data['ownerId'] == flexId]
    return create_block_owners(curData,num_npis)

def get_time(dt, tm):
    timezone = pytz.timezone("US/Central")
    time_components = tm.split(':')
    hour = time_components[0][-2:]
    minutes = time_components[1]
    return timezone.localize(datetime(dt.year, dt.month, dt.day,int(hour), int(minutes), 0))

def update_block_times(data):
    data['blockStartTime'] = data.apply(lambda row: get_time(row['blockDate'], row['start_time']), axis=1)
    data['blockEndTime'] = data.apply(lambda row: get_time(row['blockDate'], row['end_time']), axis=1)
    return data

def get_all_block_procedures(procedure_data,npis,block_date):
    return procedure_data[(procedure_data['NPI'].isin(npis)) & 
                          (procedure_data['procedureDtNoTime'] == block_date)].sort_values(by=['local_start_time'])

def get_in_room_block_procedures(procedure_data,npis,block_date,room):
    return procedure_data[(procedure_data['NPI'].isin(npis)) & 
                          ((procedure_data['procedureDtNoTime'] == block_date)) & 
                          (procedure_data['room'] == room)].sort_values(by=['local_start_time'])  
                                                                                                                                                        
def get_out_room_block_procedures(procedure_data,npis,block_date,room):
    return procedure_data[(procedure_data['NPI'].isin(npis)) & 
                          (procedure_data['procedureDtNoTime'] == block_date) &
                          (procedure_data['room'] != room) ].sort_values(by=['local_start_time'])    

pseudo_schedule_cols = ['local_start_time', 'local_end_time']

def create_pseudo_schedule(procedures):
    new_schedule = pd.DataFrame(columns=pseudo_schedule_cols)
    if procedures.shape[0] > 0:
        local_start_time = procedures.iloc[0]['local_start_time']
        local_end_time = procedures.iloc[0]['local_end_time']
        for x in range(1,procedures.shape[0]):
            curRow = procedures.iloc[x]
            if (curRow['local_start_time'] > local_end_time):
                new_schedule.loc[len(new_schedule.index)] = [local_start_time, local_end_time] 
                local_start_time = curRow['local_start_time']
                local_end_time =  curRow['local_end_time']
            elif ((curRow['local_start_time'] < local_end_time) & (curRow['local_end_time'] < local_end_time)):
                continue
            else:
                local_end_time = curRow['local_end_time']
        new_schedule.loc[len(new_schedule.index)] = [local_start_time, local_end_time]
    return new_schedule 


def get_block_usage(procedures, block_start, block_end,room_type,id):
        non_block_time = 0
        block_time = 0
        total_minutes = (block_end - block_start).total_seconds()/60
        for x in range(procedures.shape[0]):
            curRow = procedures.loc[x]
            # if ((block_type == 'ALL') & (id == 430001)):
            #     print('block usage', block_start, block_end, 'proc stat', curRow['local_start_time'], 'proc end', curRow['local_end_time'])
            if ((curRow['local_end_time'] <= block_start) | (curRow['local_start_time'] >= block_end)):
                non_block_time += (curRow['local_end_time'] - curRow['local_start_time']).total_seconds()/60
                continue
            if ((curRow['local_start_time'] >= block_start) & (curRow['local_end_time'] <= block_end)):
                block_time += (curRow['local_end_time'] - curRow['local_start_time']).total_seconds()/60
                continue
            if ((curRow['local_start_time'] < block_start) & (curRow['local_end_time'] > block_end)):
                block_time += (block_end - block_start).total_seconds()/60
                non_block_time += (block_start - curRow['local_start_time']).total_seconds()/60
                non_block_time += (curRow['local_end_time'] - block_end).total_seconds()/60
                continue
            if ((curRow['local_start_time'] == block_start) & (curRow['local_end_time'] > block_end)):
                block_time += (block_end - block_start).total_seconds()/60
                non_block_time += (curRow['local_end_time'] - block_end).total_seconds()/60
                continue
            if ((curRow['local_start_time'] <block_start) & (curRow['local_end_time'] == block_end)):
                block_time += (block_end - block_start).total_seconds()/60
                non_block_time += (block_start-curRow['local_start_time']).total_seconds()/60
                continue
            if((curRow['local_start_time'] < block_start) & (curRow['local_end_time'] < block_end)):
                block_time += (curRow['local_end_time'] - block_start).total_seconds()/60
                non_block_time += (block_start - curRow['local_start_time']).total_seconds()/60
                continue
            if((curRow['local_start_time'] > block_start) & (curRow['local_end_time'] > block_end)):
                block_time += (block_end - curRow['local_start_time']).total_seconds()/60 
                non_block_time += (curRow['local_end_time'] - block_end).total_seconds()/60
                continue
        return  block_time, non_block_time, total_minutes

def get_block_minutes(procedures,unit, data, block_date,room,block_stats,room_type):
    pseudo_schedule = create_pseudo_schedule(procedures)
    bt_minutes, nbt_minutes, total_minutes = get_block_usage(pseudo_schedule, data['blockStartTime'], data['blockEndTime'],room_type,data['flexId'])
    if total_minutes == 0:
        utilization = '0%'
    else:
        utilization = str(round(bt_minutes/total_minutes*100,0)) +'%'
    block_stats.loc[len(block_stats.index)]=[data['flexId'],block_date,unit,room,utilization,bt_minutes, nbt_minutes, total_minutes, room_type,data['blockType']]

    return block_stats

def updateProcedureLists(curRow,unit,room, block_date, procedures,roomType,procList):
        procedures['procedureDtNoTime']= procedures['procedureDtNoTime'].apply(lambda x: x.strftime("%Y-%m-%d"))
        procedures['local_start_time']= procedures['local_start_time'].apply(lambda x: formatProcedureTimes(x))
        procedures['local_end_time']=procedures['local_end_time'].apply(lambda x: formatProcedureTimes(x))
        localProcList =[]
        bt='ALL'
        weekday = block_date.isoweekday()
        for x in range(procedures.shape[0]):
            procedureRow = procedures.iloc[x]
            if(room == procedureRow.room):
                bt = 'IN'
            else: 
                bt = 'OUT'
            curProcedure = {'fullName':procedureRow.fullName, 'procedureDtNoTime':procedureRow.procedureDtNoTime,
                       'unit':procedureRow.unit, 'procedureName':procedureRow.procedureName,'NPI': str(procedureRow.NPI),
                       'local_start_time':procedureRow.local_start_time, 'local_end_time':procedureRow.local_end_time,
                       'room':procedureRow.room, 'type':bt}
            localProcList.append(curProcedure)
        blockObj ={'blockId': str(curRow['flexId']), 'blockName':curRow['blockName'], 'room':room,'unit':unit,
                   'weekday':weekday, 'blockDate':block_date.strftime("%Y-%m-%d"), 'type': bt, 'procs':localProcList,'blockType': curRow['blockType'],
                   'start_time':str(formatProcedureTimes(get_block_date_with_time(curRow['start_time']))),'end_time':str(formatProcedureTimes(get_block_date_with_time(curRow['end_time']))),
                   'blockName':curRow['blockName'],
                    'releaseDate':date.strftime(curRow['releaseDate'],"%m-%d-%Y") }

        procList.append(blockObj)
        return procList

def get_all_block_stats(curRow,unit, procedure_data,npis, block_date, room,block_stats,procList):
    procedures = get_all_block_procedures(procedure_data,npis,block_date)
    # print(block_date)
    procList = updateProcedureLists(curRow,unit,room, block_date, procedures.copy(),'ALL',procList)
    return get_block_minutes(procedures,unit, curRow, block_date,room,block_stats,'ALL')

def get_in_room_block_stats(curRow,unit, procedure_data,npis, block_date, room,block_stats,procList):
    procedures = get_in_room_block_procedures(procedure_data,npis,block_date,room)
    # procList = updateProcedureLists(curRow,unit,room, block_date, procedures.copy(),'IN',procList)
    return get_block_minutes(procedures,unit, curRow, block_date,room,block_stats,'IN'), procList 

def get_out_room_block_stats(curRow,unit, procedure_data,npis, block_date, room,block_stats,procList):
    procedures = get_out_room_block_procedures(procedure_data,npis,block_date,room)
    # procList = updateProcedureLists(curRow,unit,room, block_date, procedures.copy(),'OUT',procList)
    return get_block_minutes(procedures,unit, curRow, block_date,room,block_stats,'OUT'), procList     
        
block_stats_cols = ['id', 'blockDate','unit', 'room', 'utilization', 'bt_minutes', 'nbt_minutes','total_minutes', 'type','blockType']


def get_block_report_hours(data):
    block_report_hours = [{'id':str(row.id), 'blockDate':row.blockDate.strftime("%Y-%m-%d"),'unit':row.unit,
                                    'room':row.room, 'utilization':row.utilization,'bt_minutes':str(row.bt_minutes),
                                    'nbt_minutes':str(row.nbt_minutes),'total_minutes':str(row.total_minutes),
                                    'type':row.type,'blockType':row.blockType} for index, row in data.iterrows()] 
    return block_report_hours


def pad_block_data(stats,start_date,unit):
    stats = remove_block_weekends(start_date, stats)
    block_dates = stats['blockDate'].apply(lambda x: x.strftime("%Y-%m-%d"))
    block_dates = block_dates.drop_duplicates().to_list()
    # print('block dates', block_dates)
    # procedure_date = get_procedure_date(start_date)
    procedure_date = start_date
    month_dates = all_dates_current_month(procedure_date.month, procedure_date.year)
    missing_dates = list(set(month_dates).difference(block_dates))
    weekdays = []
    for date in missing_dates:
        # print('missing date', date)
        curDate = get_procedure_date(date)
        if ((curDate.isoweekday() == 6) | (curDate.isoweekday() == 7)):
            continue
        weekdays.append(date)
        for weekday in weekdays:
            idx = len(stats) 
            stats.loc[len(stats.index)]=[idx+.25,datetime.strptime(weekday, "%Y-%m-%d"),unit,'none','No Block',0, 0, 0, 'ALL','None']
            stats.loc[len(stats.index)]=[idx+.5,datetime.strptime(weekday, "%Y-%m-%d"),unit,'none','No Block',0, 0, 0, 'IN','None']
            stats.loc[len(stats.index)]=[idx+.75,datetime.strptime(weekday, "%Y-%m-%d"),unit,'none','No Block',0, 0, 0, 'OUT','None']
    return stats.sort_values(by=['blockDate'])

def checkSelectedNPIs(npis, selectedNPIs):
    for npi in selectedNPIs:
        if (npi in npis):
            return True
    return False


def get_block_stats(block_schedule, block_owner, procedure_data,unit,num_npis,start_date,selectAll, selectedNPIs):
    block_stats = pd.DataFrame(columns=block_stats_cols)
    
    # print('blockStats cols',block_stats.columns)
    block_data = get_blocks_from_unit(block_schedule,unit)
    block_data = update_block_times(block_data.copy())
    # print('block_data_cols', block_data.columns)
    block_dates = get_block_dates(block_data)
    block_rooms = get_block_rooms(block_data)
    print('block dates', block_dates)
    procedure_list = []
    for block_date in block_dates: 
        for room in block_rooms:
            daily_block_data = block_data[(block_data['blockDate'] == block_date) &
                                    (block_data['room'] == room)]
            for x in range(daily_block_data.shape[0]):
                # print(daily_block_data.columns)
                curRow = daily_block_data.iloc[x]
                npis = getOwnerNPIs (block_owner, curRow['flexId'],num_npis)
                if selectAll: 
                    block_stats = get_all_block_stats(curRow,unit, procedure_data,npis,block_date,room,block_stats,procedure_list)
                    block_stats,procedure_list = get_in_room_block_stats(curRow,unit,procedure_data,npis,block_date,room,block_stats,procedure_list)
                    block_stats, procedure_list = get_out_room_block_stats(curRow,unit,procedure_data,npis,block_date,room,block_stats,procedure_list)
                elif checkSelectedNPIs(npis, selectedNPIs):
                    block_stats = get_all_block_stats(curRow,unit, procedure_data,npis,block_date,room,block_stats,procedure_list)
                    block_stats,procedure_list = get_in_room_block_stats(curRow,unit,procedure_data,npis,block_date,room,block_stats,procedure_list)
                    block_stats, procedure_list = get_out_room_block_stats(curRow,unit,procedure_data,npis,block_date,room,block_stats,procedure_list)

    
    block_stats=pad_block_data(block_stats,start_date,unit)
    
    return block_stats, procedure_list





def remove_block_weekends(procedure_date, data):
    # procedure_date = get_procedure_date(start_date)
    month_dates = all_dates_current_month(procedure_date.month, procedure_date.year)
    for date in month_dates: 
        procedure_date = get_procedure_date(date).date()
        if ((procedure_date.isoweekday()==6) | (procedure_date.isoweekday() == 7)):
            data = data[data['blockDate'] != procedure_date]
            continue
    return data



def get_filtered_procedures(procedures, npi_list): 
    return procedures[procedures['NPI'].isin(npi_list)]


procedureList =[]

def getEndDate(startDate):
    if startDate.month == 12:
        next_month = 1
        next_year = startDate.year +1
    else:
        next_month = startDate.month +1
        next_year = startDate.year
    return date(next_year, next_month,1)



@app.route('/blocks', methods=['POST'])
def get_block_data_async():
    unit = get_data(request.json, "unit")
    selectAll = get_data(request.json, "selectAll")
    curDate = get_data(request.json, "startDate")
    print('curdate',curDate)
    startDate = get_procedure_date(curDate).date()
    # print(request)
    selectedProviders  = get_data(request.json, "selectedProviders")
    # procedures = dataFrameLookup[unit]
    procedures = getPTProcedures(startDate, unit,block_templates)
    # print('block cols', block_no_release['blockType'])
    roomLists = [jriRooms,stmSTORRooms,MTORRooms]
    block_no_release,block_schedule = get_block_schedule(startDate, block_templates,roomLists, manual_release)
    if not(selectAll):
        procedures = get_filtered_procedures(procedures, selectedProviders)
    block_stats,procList = get_block_stats(block_no_release,block_owner,procedures, unit,num_npis,startDate,selectAll,selectedProviders)
    return json.dumps({'grid':get_block_report_hours(block_stats),'details':procList}), 200


@app.route('/stats', methods=['POST'])
def get_surgeon_stats_async():
    unit = get_data(request.json, "unit")
    npi = int(get_data(request.json, "NPI"))
    name = get_data(request.json, "name")
    # print('name', name, 'npi',npi)
    return get_stats(unit,name, npi), 200


@app.route('/calendar', methods=['POST'])
def get_calendar_async():
    # print(request.json)
    date_requested = get_data(request.json, "date")
    unit = get_data(request.json, "unit")
    data = dataFrameLookup[unit]
    return get_monthly_utilization(date_requested,unit,data), 200


@app.route('/grid', methods=['POST'])
def get_grid_async():
    date_requested = get_data(request.json, "date")
    unit = get_data(request.json, "unit")
    data = dataFrameLookup[unit]
    return get_daily_room_utilization(unit, date_requested, data), 200

@app.route('/details', methods=['POST'])
def get_details_async():
    date_requested = get_data(request.json, "date")
    unit = get_data(request.json, "unit")
    room = get_data(request.json,"room")
    prime_time_hours = get_data(request.json, "primeTime")
    data = dataFrameLookup[unit]
    block_details = get_block_details_data(room,date_requested,block_schedule)
    room_details = get_room_details(unit, date_requested, room, data,prime_time_hours['start'], prime_time_hours['end'])
    return json.dumps({'room':room_details, 'block':block_details}), 200


@app.route('/surgeon', methods=['GET'])
def get_surgeon_lists_async():
    jriList = get_providers('BH JRI')
    stmSTORList = get_providers('STM ST OR')
    mtORList = get_providers('MT OR')
    return json.dumps({'BH JRI': jriList,
                        'STM ST OR': stmSTORList,
                        'MT OR': mtORList}), 200

@app.route('/pt_hours', methods=['POST'])
def get_pt_hours_async():
    pt_hours = {}
    prime_time_hours = get_data(request.json, "primeTime")
    unit = get_data(request.json, "unit")
    curDate = get_data(request.json, "startDate")
    startDate = get_procedure_date(curDate).date()
    procedures = getPTProcedures(startDate, unit,block_templates)
    print('curDate', curDate)
    pt_hours['surgeryInfo'] = get_unit_report_hours(get_prime_time_procedure_hours(procedures, prime_time_hours['start'], prime_time_hours['end'],curDate))
    pt_hours = pad_data(pt_hours,unit, curDate)
    return json.dumps (pt_hours), 200




app.run(host='0.0.0.0', port=5001)