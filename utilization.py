import pandas as pd;
from datetime import date, timedelta, datetime, timezone;
import calendar;
import json;
import pytz;
from flask import Flask, flash, request, redirect, render_template, send_from_directory,abort
from flask_cors import CORS


app = Flask(__name__)
CORS(app)
app.secret_key = "seamless care" # for encrypting the session
app.config['CORS_HEADERS'] = 'Content-Type'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024




units = ['BH JRI','STM ST OR', 'MT OR']
jriRooms = ['BH JRI 02','BH JRI 03','BH JRI 04','BH JRI 05','BH JRI 06','BH JRI 07','BH JRI 08','BH JRI 09']
stmSTORRooms = ['STM ST OR 01','STM ST OR 02','STM ST OR 03','STM ST OR 04','STM ST OR 05',
                'STM ST OR 06','STM ST OR 07','STM ST OR 08','STM ST OR 09','STM ST OR 10',
                'STM ST OR 11','STM ST OR 12','STM ST OR 14','STM ST OR 15','STM ST OR 16',
                'STM ST OR 17','STM ST OR 18','STM ST OR Hybrid']
MTORRooms = ['MT Cysto','MT OR 01','MT OR 02','MT OR 03','MT OR 04','MT OR 05','MT OR 06',
             'MT OR 07','MT OR 08','MT OR 09','MT OR 10','MT OR 11','MT OR 12','MT OR 14',
             'MT OR 15','MT OR 16','MT OR 17']

orLookUp = {'BH JRI': jriRooms,'STM ST OR':stmSTORRooms, 'MT OR': MTORRooms}

primetime_minutes_per_room = 600

def getUnitData(filename):
    dataCols = ['procedures[0].primaryNpi','startTime','endTime','duration','procedureDate',
            'room','procedures[0].procedureName','unit']
    names = ['NPI', 'startTime', 'endTime', 'duration', 'procedureDate', 'room', 'procedureName','unit']
    baseData = pd.read_csv(filename, usecols=dataCols,parse_dates=['procedureDate','startTime', 'endTime'])
    baseData.rename(columns={'procedures[0].primaryNpi':'NPI','procedures[0].procedureName':'procedureName'}, inplace=True)

    surgeons = pd.read_csv('Surgeons.csv')
    dataWithSurgeonNames = baseData.merge(surgeons, left_on='NPI', right_on='npi')
    # need to create date column without timestamp
    dataWithSurgeonNames['new_procedureDate'] = pd.to_datetime(dataWithSurgeonNames['procedureDate']).dt.tz_convert(None)

    #convert Zulu Time
    dataWithSurgeonNames['local_start_time'] = dataWithSurgeonNames['startTime'].apply(lambda x: x.replace(tzinfo=timezone.utc).astimezone(pytz.timezone("US/Central")))
    dataWithSurgeonNames['local_end_time'] = dataWithSurgeonNames['endTime'].apply(lambda x: x.replace(tzinfo=timezone.utc).astimezone(pytz.timezone("US/Central")))

    #remove soft blocks
    dataWithSurgeonNames = dataWithSurgeonNames[dataWithSurgeonNames['npi'] != 0]
    return dataWithSurgeonNames

jriData = getUnitData('JRIData.csv')
STMSTORData = getUnitData('STMSTORData.csv')
MTORData = getUnitData('MTORData.csv')
dataFrameLookup = {'BH JRI': jriData, 'STM ST OR': STMSTORData, 'MT OR': MTORData}
def formatMinutes(minutes):
       h, m = divmod(minutes, 60)
       return '{:d} hours {:02d} minutes'.format(int(h), int(m))

def formatProcedureTimes(date):
    return date.strftime("%I:%M %p")


def all_dates_current_month(month,year):
    number_of_days = calendar.monthrange(year, month)[1]
    first_date = date(year, month, 1)
    last_date = date(year, month, number_of_days)
    delta = last_date - first_date
    return [(first_date + timedelta(days=i)).strftime('%Y-%m-%d') for i in range(delta.days + 1)]



def get_procedure_date(date):
    return datetime.strptime(date, '%Y-%m-%d')

def get_procedure_data_with_time(time):
    return datetime.strptime(date, '%Y-%m-%d %H:%M:%S')

def getDailyUtilization(unit, date,data, prime_minutes_per_room):

    prime_minutes = len(orLookUp[unit]) * prime_minutes_per_room
    procedure_date = get_procedure_date(date)
    # print('data', data)
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
            print('in coninue loop')
            continue
        # print('in loop', date)
        daily_utilization = getDailyUtilization(unit, date,data,primetime_minutes_per_room)
        utilization.append({'date':date, 'display':str(int(daily_utilization)) + '%'})
    utilization = pad_calendar_data(utilization)
    return json.dumps(utilization)


def get_daily_room_utilization(unit, selected_date,data):
    utilization = []
    procedure_date = get_procedure_date(selected_date)
    rooms = orLookUp[unit]
    for room in rooms:
        room_utlization = get_daily_utilization_per_room(room, procedure_date,data,primetime_minutes_per_room)
        utilization.append({'id':room,'name':room,'property':str(int(room_utlization)) + '%'})
    return json.dumps(utilization)



def get_room_details(unit, selected_date, room,data):
    details = []
    procedure_date = get_procedure_date(selected_date)
    room_data = data[(data['new_procedureDate'] == procedure_date) & (data['room'] == room)].sort_values(by=['startTime'])
    prime_time_start= datetime(procedure_date.year,procedure_date.month,procedure_date.day,7,30,0).astimezone(pytz.timezone("US/Central"))
    prime_time_end= datetime(procedure_date.year,procedure_date.month,procedure_date.day,17,00,0).astimezone(pytz.timezone("US/Central"))
    room_data.reset_index(drop=True, inplace=True)
    for ind in room_data.index:
        surgeon = room_data['fullName'][ind]
        start_time = room_data['local_start_time'][ind]
        end_time = room_data['local_end_time'][ind]
        duration = room_data['duration'][ind]
        procedure_name = room_data['procedureName'][ind]
        # print(ind)
        if ind == 0:
            if (start_time > prime_time_start):
                time_difference = (start_time - prime_time_start).seconds/60
                if time_difference > 15:
                    formatted_time = formatMinutes(time_difference)
                    formatted_start = formatProcedureTimes(prime_time_start)
                    formatted_end = formatProcedureTimes(start_time)
                    details.append({'id': str(ind + 0.5), 'col1':'Open Time','col2':'','col3':str(formatted_start),'col4':str(formatted_end),'col5':str(formatted_time)}) 
        else:
            if (start_time > prime_time_start):
                time_difference = (start_time - room_data['local_end_time'][ind - 1]).seconds/60
                if time_difference > 15:
                    formatted_time = formatMinutes(time_difference)
                    formatted_start = formatProcedureTimes(room_data['local_end_time'][ind - 1])
                    formatted_end = formatProcedureTimes(start_time)
                    details.append({'id': str(ind + 0.5), 'col1':'Open Time','col2':'','col3':str(formatted_start),'col4':str(formatted_end),'col5':str(formatted_time)}) 
        formatted_time = formatMinutes(duration)
        formatted_start = formatProcedureTimes(start_time)
        formatted_end = formatProcedureTimes(end_time)
        details.append({'id': str(ind), 'col1':str(surgeon),'col2':str(procedure_name),'col3':str(formatted_start),'col4':str(formatted_end),'col5':str(formatted_time)})
        if ind == len(room_data.index)-1:
            # print('end time', end_time)
            # print('prime time', prime_time_end)
            if end_time < prime_time_end:  
                time_difference = (prime_time_end - end_time).seconds/60
                if time_difference > 15:
                    formatted_time = formatMinutes(time_difference)
                    formatted_start = formatProcedureTimes(end_time)
                    formatted_end = formatProcedureTimes(prime_time_end)
                    details.append({'id':str(ind + 0.75),'col1':'Open Time','col2':'','col3':str(formatted_start), 'col4':str(formatted_end),'col5':str(formatted_time)})
        
    return json.dumps(details)


        
# print(get_room_details('BH JRI', '2023-06-07','BH JRI 03'))

def get_data(request, string):
    data_requested = request[string]
    return data_requested

def get_providers(unit):
    data = dataFrameLookup[unit]
    data = data[data['NPI'] != 0]
    providers = data[['fullName','NPI']].copy()
    providers = providers.drop_duplicates().sort_values(by=['fullName'])
    surgeon_list = [{'id': row.NPI, 'name':row.fullName, 'selected':True} for index, row in providers.iterrows() ] 
    return surgeon_list


unit_report_hours_cols = ['duration', 'unit', 'procedureName', 'NPI', 'room', 'procedureDate',
       'startTime', 'endTime', 'name', 'lastName', 'npi', 'fullName',
       'new_procedureDate', 'local_start_time', 'local_end_time',
       'prime_time_minutes','non_prime_time_minutes']

def get_unit_report_hours(data):
    # unit_report_hours = [{'id': index, 'duration':row.duration, 'unit': row.unit, 'procedureName': row.procedureName,
    #                       'NPI': row.NPI, 'room': row.room, 'procedureDate': row.procedureDate, 'startTime':row.startTime,
    #                       'endTime': row.endTime, 'fullName': row.fullName, 'new_procedureDate': row.new_procedureDate,
    #                       'local_start_time': row.local_start_time, 'local_end_time':row.local_end_time, 
    #                       'prime_time_minutes': row.prime_time_minutes, 'non_prime_time_minutes':row.non_prime_time_minutes
    #                       } for index, row in data.iterrows()] 
    unit_report_hours = [{'id': index,
                          'calendar': {
                              'unit': row.unit,'NPI': row.NPI,'procedureDate': row.new_procedureDate, 
                              'prime_time_minutes': row.prime_time_minutes,'non_prime_time_minutes':row.non_prime_time_minutes },
                            'grid': {'unit': row.unit,'room': row.room, 'procedureDate': row.new_procedureDate,
                                     'prime_time_minutes': row.prime_time_minutes,'non_prime_time_minutes':row.non_prime_time_minutes },
                            'details': { 'fullName': row.fullName,'local_start_time': row.local_start_time,'local_end_time':row.local_end_time, 
                                        'procedureName': row.procedureName,'duration':row.duration}
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
    return data[data['procedureDate'] == date].sort_values(by=['local_start_time'])


def get_procedures_from_room(data, room):
    return data[data['room'] == room].sort_values(by=['local_start_time'])

def get_procedures_before_time(data, startTime):
    # print('pt start', startTime)
    # print(data['local_end_time'])
    # print (data['local_end_time'] < startTime)
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
    # print('early overlap', overlap_procedures)
    if (len(overlap_procedures) > 0): 
        for index, procedure in overlap_procedures.iterrows():
            # print('pt start', prime_time_start)
            # print('start_time', procedure['local_start_time'])
            # print('end time', procedure['local_end_time'])
            procedure['non_prime_time_minutes'] = (prime_time_start - procedure['local_start_time']).total_seconds()/60
            procedure['prime_time_minutes'] = (procedure['local_end_time'] - prime_time_start).total_seconds()/60
            hours= hours.append(procedure, ignore_index=True)
            # print('nt', procedure['non_prime_time_minutes'])
            # print( 'pt', procedure['prime_time_minutes'])
    return hours


def get_overlap_late_procedures(procedures, hours,prime_time_start, prime_time_end):
    overlap_procedures = get_procedures_overlap_late(procedures,prime_time_start, prime_time_end)
    # print('late overlap', overlap_procedures)
    if (len(overlap_procedures) > 0): 
        for index, procedure in overlap_procedures.iterrows():
            # print('pt end', prime_time_end)
            # print('start_time', procedure['local_start_time'])
            # print('end time', procedure['local_end_time'])
            procedure['prime_time_minutes'] = (prime_time_end - procedure['local_start_time']).total_seconds()/60
            procedure['non_prime_time_minutes'] = (procedure['local_end_time'] - prime_time_end).total_seconds()/60
            hours= hours.append(procedure, ignore_index=True)
            # print('nt', procedure['non_prime_time_minutes'])
            # print( 'pt', procedure['prime_time_minutes'])
    return hours

def get_early_procedures(procedures, hours, prime_time_start):
    early_procedures= get_procedures_before_time(procedures, prime_time_start)
    # print('early ', early_procedures)
    if (len(early_procedures) > 0): 
        for index, procedure in early_procedures.iterrows():
            # print('pt startt', prime_time_start)
            # print('start_time', procedure['local_start_time'])
            # print('end time', procedure['local_end_time'])
            procedure['non_prime_time_minutes'] = (procedure['local_end_time'] - procedure['local_start_time']).total_seconds()/60
            procedure['prime_time_minutes'] = 0
            hours= hours.append(procedure, ignore_index=True)
            # print('nt', procedure['non_prime_time_minutes'])
            # print( 'pt', procedure['prime_time_minutes'])
    return hours

def get_late_procedures(procedures, hours, prime_time_end):
    late_procedures= get_procedures_after_time(procedures, prime_time_end)
    # print('late ', late_procedures)
    if (len(late_procedures) > 0): 
        for index, procedure in late_procedures.iterrows():
            # print('pt end', prime_time_end)
            # print('start_time', procedure['local_start_time'])
            # print('end time', procedure['local_end_time'])
            procedure['non_prime_time_minutes'] = (procedure['local_end_time'] - procedure['local_start_time']).total_seconds()/60
            procedure['prime_time_minutes'] = 0
            hours= hours.append(procedure, ignore_index=True)
            # print('nt', procedure['non_prime_time_minutes'])
            # print( 'pt', procedure['prime_time_minutes'])
    return hours 


def get_prime_time_procedures(procedures, hours, prime_time_start, prime_time_end):
    prime_time_procedures= get_procedures_between_time(procedures,prime_time_start, prime_time_end)
    # print('pt procedures', prime_time_procedures)
    if (len(prime_time_procedures) > 0): 
        for index, procedure in prime_time_procedures.iterrows():
            # print('pt start', prime_time_start)
            # print('pt end', prime_time_end)
            # print('start_time', procedure['local_start_time'])
            # print('end time', procedure['local_end_time'])
            procedure['prime_time_minutes'] = (procedure['local_end_time'] - procedure['local_start_time']).total_seconds()/60
            procedure['non_prime_time_minutes'] = 0
            hours= hours.append(procedure, ignore_index=True)
            # print('nt', procedure['non_prime_time_minutes'])
            # print( 'pt', procedure['prime_time_minutes'])
    return hours 

def getProcedures(unit):
    data = dataFrameLookup[unit]
    data = data[data['room'].isin(orLookUp[unit])]
    return data.copy()


def get_prime_time_procedure_hours(unit, prime_time_start_time, prime_time_end_time):
    data = getProcedures(unit)
    prime_time_hours = pd.DataFrame(columns=prime_time_hours_cols)
    # print(prime_time_hours.columns)
    data['prime_time_minutes'] = 0
    data['non_prime_time_minutes'] = 0
    procedureDates = getProcedureDates(data)
    for procedure in procedureDates:
        # print(procedure)
        # new_date = procedureDates[0]
        prime_time_start, prime_time_end = getPrimeTimeWithDate(procedure, prime_time_start_time, prime_time_end_time)
        procedures = get_procedures_from_date(data, procedure)
        prime_time_hours = get_complete_overlap_procedures(procedures,prime_time_hours, prime_time_start, prime_time_end)
        prime_time_hours = get_overlap_early_procedures(procedures, prime_time_hours,prime_time_start, prime_time_end)
        prime_time_hours = get_overlap_late_procedures(procedures, prime_time_hours, prime_time_start, prime_time_end)
        prime_time_hours = get_early_procedures(procedures, prime_time_hours, prime_time_start)
        prime_time_hours = get_late_procedures(procedures,prime_time_hours, prime_time_end)
        prime_time_hours = get_prime_time_procedures(procedures, prime_time_hours, prime_time_start, prime_time_end)
    # print(prime_time_hours)
    return prime_time_hours


@app.route('/calendar', methods=['POST'])
def get_calendar():
    print(request.json)
    date_requested = get_data(request.json, "date")
    unit = get_data(request.json, "unit")
    data = dataFrameLookup[unit]
    return get_monthly_utilization(date_requested,unit,data), 200


@app.route('/grid', methods=['POST'])
def get_grid():
    date_requested = get_data(request.json, "date")
    unit = get_data(request.json, "unit")
    data = dataFrameLookup[unit]
    return get_daily_room_utilization(unit, date_requested, data), 200

@app.route('/details', methods=['POST'])
def get_details():
    date_requested = get_data(request.json, "date")
    unit = get_data(request.json, "unit")
    room = get_data(request.json,"room")
    data = dataFrameLookup[unit]
    return get_room_details(unit, date_requested, room, data), 200


@app.route('/surgeon', methods=['GET'])
def get_surgeon_lists():
    jriList = get_providers('BH JRI')
    stmSTORList = get_providers('STM ST OR')
    mtORList = get_providers('MT OR')
    return json.dumps({'BH JRI': jriList,
                        'STM ST OR': stmSTORList,
                        'MT OR': mtORList}), 200
# data = dataFrameLookup['MT OR']
# print(orLookUp['MT OR'])
# data = data[data['room'].isin(orLookUp['MT OR'])]
# print(data.shape)
@app.route('/pt_hours', methods=['POST'])
def get_pt_hours():
    pt_hours = {}
    prime_time_hours = get_data(request.json, "primeTime")
    print(prime_time_hours)
    return json.dumps({'response': 'got it'}), 200
    # for unit in units:
    #     pt_hours[unit] = get_unit_report_hours(get_prime_time_procedure_hours(unit, prime_time_hours['start'], prime_time_hours['end']))
    # return json.dumps (pt_hours), 200



# pt_hours={}
# for unit in units: 
# pt_hours['BH JRI'] = get_unit_report_hours(get_prime_time_procedure_hours('BH JRI', "7:30", "15:30"))
# print (pt_hours['BH JRI'][0]['details'])



# pt_hours = get_prime_time_procedure_hours('STM ST OR', "7:30", "15:30")
# pt_hours.to_csv('pt_hours-STMSTOR.csv')
# pt_hours_object = get_unit_report_hours(pt_hours)
# print(pt_hours_object)
# @app.route('/', methods=['GET'])
# def say_hello():
#     return json.dumps({'hello':'Hello'}), 200





app.run(host='0.0.0.0', port=5001)