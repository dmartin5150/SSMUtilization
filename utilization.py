import pandas as pd;
from datetime import date, timedelta, datetime, timezone;
import calendar;
import json;
import pytz;
from flask import Flask, flash, request, redirect, render_template, send_from_directory,abort
from flask_cors import CORS
from calendar import Calendar, monthrange
import re

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



def get_procedure_date_without_time(dt):
    return datetime.date(dt)

def get_procedure_date(dt):
    # print('date', dt)
    return datetime.strptime(dt, '%Y-%m-%d')

def get_block_date_with_time(dt):
    return datetime.strptime(dt, '%Y-%m-%dT%H:%M:%S.%f%z')



# block_data = pd.read_csv("blockslots.csv",parse_dates=['frequencies[0].blockStartDate','frequencies[0].blockEndDate',
#                         'frequencies[1].blockEndDate','frequencies[2].blockEndDate','frequencies[0].blockStartTime',
#                         'frequencies[0].blockEndTime'])

block_data = pd.read_csv("blockslots.csv")

def get_num_frequencies(data):
    mylist = block_data.columns.tolist()
    r = re.compile(".+blockStartDate$")
    newlist = list(filter(r.match, mylist)) # Read Note below
    return len(newlist)


num_frequencies = get_num_frequencies(block_data)

def fill_column(colName, value,data):
    # print(colName)
    return data.fillna({colName:value})

def fill_empty_data(num_frequencies, data):
    for x in range(num_frequencies):
        data = fill_column(f'frequencies[{x}].dowApplied', -1,data)
        data = fill_column(f'frequencies[{x}].weeksOfMonth[0]',-1,data)
        data =fill_column(f'frequencies[{x}].weeksOfMonth[1]',-1,data)
        data =fill_column(f'frequencies[{x}].weeksOfMonth[2]',-1,data)
        data =fill_column(f'frequencies[{x}].weeksOfMonth[3]',-1,data)
        data =fill_column(f'frequencies[{x}].weeksOfMonth[4]',-1,data)
        data =fill_column(f'frequencies[{x}].blockStartDate',get_procedure_date('2000-1-1'),data)
        data =fill_column(f'frequencies[{x}].blockEndDate',get_procedure_date('2000-1-1'),data)
        data =fill_column(f'frequencies[{x}].blockStartTime',get_procedure_date('2000-1-1'),data)
        data =fill_column(f'frequencies[{x}].blockEndTime',get_procedure_date('2000-1-1'),data)
        data =fill_column(f'frequencies[{x}].state','Empty',data)
    return data



num_frequencies = get_num_frequencies(block_data)
block_data = fill_empty_data(num_frequencies, block_data)


block_data = block_data[block_data['ministry'] == 'TNNAS'].copy()

block_data = block_data[(block_data['room'].isin(jriRooms)) | (block_data['room'].isin(stmSTORRooms)) 
                        | (block_data['room'].isin(MTORRooms))].copy()

closed_rooms = block_data[(block_data['flexId'] == -1)]

block_data = block_data[(block_data['type'] == 'Surgeon') | (block_data['type'] == 'Surgical Specialty')
                        | (block_data['type'] == 'Surgeon Group')].copy()


block_search_cols = [ 'candidateId', 'market', 'ministry', 'hospital', 'unit', 'room',
       'name', 'releaseDays', 'type','dow','wom1','wom2', 'wom3','wom4','wom5','start_time','end_time',
       'start_date', 'end_date','state']




def update_block_schedule(index, freq, row, block_schedule):
    cur_index = len(block_schedule)
    block_schedule.loc[cur_index,'candidateId'] = row['candidateId']
    block_schedule.loc[cur_index,'market'] = row['market']
    block_schedule.loc[cur_index,'ministry'] = row['ministry']
    block_schedule.loc[cur_index,'hospital'] = row['hospital']
    block_schedule.loc[cur_index,'unit'] = row['unit']
    block_schedule.loc[cur_index,'room'] = row['room']
    block_schedule.loc[cur_index,'blockName'] = row['name']
    block_schedule.loc[cur_index,'releaseDays'] = row['releaseDays']
    block_schedule.loc[cur_index,'dow'] = row[f'frequencies[{freq}].dowApplied']
    block_schedule.loc[cur_index,'wom1'] = row[f'frequencies[{freq}].weeksOfMonth[0]']
    block_schedule.loc[cur_index,'wom2'] = row[f'frequencies[{freq}].weeksOfMonth[1]']
    block_schedule.loc[cur_index,'wom3'] = row[f'frequencies[{freq}].weeksOfMonth[2]']
    block_schedule.loc[cur_index,'wom4'] = row[f'frequencies[{freq}].weeksOfMonth[3]']
    block_schedule.loc[cur_index,'wom5'] = row[f'frequencies[{freq}].weeksOfMonth[4]']
    block_schedule.loc[cur_index, 'start_time']= row[f'frequencies[{freq}].blockStartTime']
    block_schedule.loc[cur_index, 'end_time']= row[f'frequencies[{freq}].blockEndTime']
    block_schedule.loc[cur_index, 'start_date']= row[f'frequencies[{freq}].blockStartDate']
    block_schedule.loc[cur_index, 'end_date']= row[f'frequencies[{freq}].blockEndDate']
    block_schedule.loc[cur_index, 'state']= row[f'frequencies[{freq}].state']
    return block_schedule


def create_block_templates(block_data):
    block_data.reset_index(inplace=True)
    num_rows = block_data.shape[0]
    index= 0
    block_schedule = pd.DataFrame(columns=block_search_cols)
    for x in range(num_rows):
        cur_row = block_data.iloc[x]
        for freq in range (num_frequencies):
            if cur_row[f'frequencies[{freq}].dowApplied'] == -1:
                break
            block_schedule = update_block_schedule(index, freq, cur_row, block_schedule)
            index += 1
    return block_schedule[(block_schedule['state'] != 'COMPLETE')]

block_templates = create_block_templates(block_data)


closed_rooms = create_block_templates(closed_rooms)
closed_rooms.to_csv('closedrooms.csv')




block_search_cols = [ 'candidateId', 'market', 'ministry', 'hospital', 'unit', 'room',
       'blockName', 'releaseDays', 'type','dow','wom1','wom2', 'wom3','wom4','wom5','start_time','end_time']


manual_release_cols = ['ministry', 'slotId', 'startDtTm','endDtTm']
manual_release = pd.read_csv('blockrelease.csv', usecols=manual_release_cols, parse_dates=['startDtTm','endDtTm'])
manual_release['blockDate'] = manual_release['startDtTm'].apply(lambda x: x.date())
manual_release = manual_release[(manual_release['ministry'] == 'TNNAS')]
manual_release.to_csv('manualRelease.csv')

def getReleaseDate(curday, td):
    day = curday - timedelta(days=td)
    # print(day, type(day))
    return day

def updateAutoRelease(releaseDay):
    return releaseDay <= date.today()

def updateManualRelease(blockDate, slotId,releaseStatus, releaseData):
    curData = pd.DataFrame(columns=manual_release_cols )
    if releaseStatus:
        return True
    curData = releaseData[(releaseData['blockDate'] == blockDate) & (releaseData['slotId']== slotId)]
    return not(curData.empty)




def get_block_schedule(startDate, data,roomLists, releaseData):

    block_schedule = pd.DataFrame(columns=block_search_cols)
    curWOM = 1
    c = Calendar()
    first_day_of_month = True
    for d in [x for x in c.itermonthdates(2023, startDate.month) if x.month == startDate.month]:
        curDOW = d.isoweekday()
        for roomList in roomLists: 
            for room in roomList:
                curData = data[(data['room'] == room) & (data['dow']== curDOW) &
                                        ((data['wom1'] == curWOM) | (data['wom2'] == curWOM ) |
                                        (data['wom3'] == curWOM) | (data['wom4'] == curWOM)  |
                                        (data['wom5'] == curWOM))].copy()
                if curData.empty:
                    continue 
                curData['blockDate'] = d
                block_schedule = block_schedule.append(curData)
        if ((d.isoweekday() == 6) & (first_day_of_month)):
            curWOM = 1
            first_day_of_month = False
        elif (d.isoweekday() == 6):
            curWOM +=1


    block_schedule['releaseDays'] = block_schedule['releaseDays'].apply(lambda x: x/1440)
    block_schedule['releaseDate'] = block_schedule.apply(lambda row: getReleaseDate(row['blockDate'],row['releaseDays']),axis=1)
    block_schedule['releaseDate'] = pd.to_datetime(block_schedule['releaseDate'], format='%Y-%m-%d')
    block_schedule['releaseStatus'] = block_schedule.apply(lambda row: updateAutoRelease(row['releaseDate']), axis=1)
    block_schedule['autorelease'] = block_schedule.apply(lambda row: updateAutoRelease(row['releaseDate']), axis=1)
    block_schedule['releaseStatus'] = block_schedule.apply(lambda row: updateManualRelease(row['blockDate'], row['candidateId'],row['releaseStatus'],releaseData),axis=1)
    block_schedule['manualRelease'] =block_schedule.apply(lambda row: updateManualRelease(row['blockDate'], row['candidateId'],row['releaseStatus'],releaseData),axis=1)
    # block_schedule.to_csv('blockSchedule.csv')
    # return block_schedule
    return block_schedule[block_schedule['releaseStatus'] == False]







grid_block_data_cols = ['room', 'blockDate', 'block_status']

def get_grid_block_schedule(roomLists, block_schedule):
    grid_block_data = pd.DataFrame(columns=grid_block_data_cols)
    c = Calendar()
    index = 0
    # print('rooms', block_schedule['room'])
    for d in [x for x in c.itermonthdates(2023, startDate.month) if x.month == startDate.month]:
        for roomList in roomLists:
            for room in roomList: 
                block_data = block_schedule[(block_schedule['room'] == room) & (block_schedule['blockDate'] == d) ]
                # block_data = block_schedule[(block_schedule['room'] == room)]
                if block_data.empty:
                    grid_block_data.loc[index]= [room, d, False]
                else: 
                    grid_block_data.loc[index]=[room, d, True]
                index +=1
    return grid_block_data
                    



startDate = get_procedure_date('2023-7-1').date()
roomLists = [jriRooms,stmSTORRooms,MTORRooms]

block_schedule = get_block_schedule(startDate, block_templates,roomLists, manual_release)
block_schedule.to_csv('julyBlock.csv')

# print(block_schedule.to_csv('blockSchedule.csv'))
# print(block_schedule.dtypes)
# print('block schedule', block_schedule)
closed_room_schedule = get_block_schedule(startDate, closed_rooms,roomLists, manual_release)
closed_room_schedule['closed'] = True
closed_abbreviated = closed_room_schedule[['room','blockDate', 'closed']]
block_with_closed_schedule = block_schedule.merge(closed_abbreviated, left_on=['blockDate','room'], right_on=['blockDate','room'])

# print(block_schedule['start_date'])

grid_block_schedule = get_grid_block_schedule(roomLists,block_schedule)
grid_block_schedule.to_csv('gridblock.csv')
# print(grid_block_schedule['block_status'].drop_duplicates())

# print('name', block_schedule['blockName'])

def formatProcedureTimes(date):
    # print('date', date, type(date))
    # return date
    return date.strftime("%I:%M %p")

def printType(date):
    # print('data type',date,  type(date))
    return date


def get_block_details_data(room, blockDate, data):
    curDate = get_procedure_date(blockDate).date()
    # print('curDate', type(curDate))
    block_data = data[(data['room'] == room) & (data['blockDate'] == curDate)]
    # print('now')
    # print(block_data)
    if block_data.empty:
        return []
    else:
      return[{'name': row.blockName, 'startTime':str(formatProcedureTimes(get_block_date_with_time(row.start_time))),'endTime':str(formatProcedureTimes(get_block_date_with_time(row.end_time))),'releaseDate':date.strftime(row.releaseDate,"%m-%d-%Y")} for index, row in block_data.iterrows()]  


# block_date = get_procedure_date('2023-6-20').date()


def getUnitData(filename):
    dataCols = ['procedures[0].primaryNpi','startTime','endTime','duration','procedureDate',
            'room','procedures[0].procedureName','unit']
    names = ['NPI', 'startTime', 'endTime', 'duration', 'procedureDate', 'room', 'procedureName','unit']
    baseData = pd.read_csv(filename, usecols=dataCols,parse_dates=['procedureDate','startTime', 'endTime'])
    baseData.rename(columns={'procedures[0].primaryNpi':'NPI','procedures[0].procedureName':'procedureName'}, inplace=True)

    surgeons = pd.read_csv('Surgeons.csv')
    dataWithSurgeonNames = baseData.merge(surgeons, left_on='NPI', right_on='npi')

    #only select SSM units 
    dataWithSurgeonNames = dataWithSurgeonNames[(dataWithSurgeonNames['room'].isin(jriRooms)) | (dataWithSurgeonNames['room'].isin(stmSTORRooms)) 
                        | (dataWithSurgeonNames['room'].isin(MTORRooms))]

    # need to create date column without timestamp
    dataWithSurgeonNames['new_procedureDate'] = pd.to_datetime(dataWithSurgeonNames['procedureDate']).dt.tz_convert(None)
    dataWithSurgeonNames['procedureDtNoTime'] = dataWithSurgeonNames['procedureDate'].apply(lambda x: x.date())

    #add procedure date without time for block information
    dataWithSurgeonNames['blockDate'] = dataWithSurgeonNames['new_procedureDate'].apply(lambda x: x.date())
    #add block status to procedure room/date
    # print('pre', dataWithSurgeonNames['blockDate'])
    dataWithSurgeonNames= dataWithSurgeonNames.merge(grid_block_schedule,how='left', left_on=['blockDate','room'], right_on=['blockDate','room'])


    #convert Zulu Time
    dataWithSurgeonNames['local_start_time'] = dataWithSurgeonNames['startTime'].apply(lambda x: x.replace(tzinfo=timezone.utc).astimezone(pytz.timezone("US/Central")))
    dataWithSurgeonNames['local_end_time'] = dataWithSurgeonNames['endTime'].apply(lambda x: x.replace(tzinfo=timezone.utc).astimezone(pytz.timezone("US/Central")))

    #remove soft blocks
    dataWithSurgeonNames = dataWithSurgeonNames[dataWithSurgeonNames['npi'] != 0]
    return dataWithSurgeonNames

jriData = getUnitData('JRIData.csv')
# print(jriData['block_status'].drop_duplicates())
STMSTORData = getUnitData('STMSTORData.csv')
MTORData = getUnitData('MTORData.csv')
# print('jri', jriData.shape)
# print('st',STMSTORData.shape)
# print('MT', MTORData.shape)
dataFrameLookup = {'BH JRI': jriData, 'STM ST OR': STMSTORData, 'MT OR': MTORData}

def formatMinutes(minutes):
       h, m = divmod(minutes, 60)
       return '{:d} hours {:02d} minutes'.format(int(h), int(m))




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


def remove_weekend(data, procedure_date):
    return (data[data['procedureDate'] != procedure_date])


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
        procedure_date = get_procedure_date(date)
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



def get_room_details(unit, selected_date, room,data,pt_start, pt_end):
    details = []
    pt_start_data = pt_start.split(':')
    pt_end_data = pt_end.split(':')
    # print(pt_end)
    procedure_date = get_procedure_date(selected_date)
    room_data = data[(data['new_procedureDate'] == procedure_date) & (data['room'] == room)].sort_values(by=['startTime'])

    prime_time_start= datetime(procedure_date.year,procedure_date.month,procedure_date.day,int(pt_start_data[0]),int(pt_start_data[1]),0).astimezone(pytz.timezone("US/Central"))
    prime_time_end= datetime(procedure_date.year,procedure_date.month,procedure_date.day,int(pt_end_data[0]),int(pt_end_data[1]),0).astimezone(pytz.timezone("US/Central"))
    room_data.reset_index(drop=True, inplace=True)
    for ind in room_data.index:
        surgeon = room_data['fullName'][ind]
        npi = room_data['NPI'][ind]
        start_time = room_data['local_start_time'][ind]
        end_time = room_data['local_end_time'][ind]
        duration = room_data['duration'][ind]
        procedure_name = room_data['procedureName'][ind]
        # print(ind)
        if ind == 0:
            if (start_time > prime_time_start):
                if (start_time > prime_time_end):
                    time_difference = (prime_time_end - prime_time_start).seconds/60
                else:
                    time_difference = (start_time - prime_time_start).seconds/60
                if time_difference > 15:
                    formatted_time = formatMinutes(time_difference)
                    formatted_start = formatProcedureTimes(prime_time_start)
                    if (start_time > prime_time_end):
                        formatted_end = formatProcedureTimes(prime_time_end)
                    else:
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
        details.append({'id': str(npi), 'col1':str(surgeon),'col2':str(procedure_name),'col3':str(formatted_start),'col4':str(formatted_end),'col5':str(formatted_time)})
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
        
    return details


        
# print(get_room_details('BH JRI', '2023-06-07','BH JRI 03'))

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
                              'unit': row.unit,'NPI': row.NPI,'procedureDate': str(get_procedure_date_with_time(str(row.new_procedureDate))), 
                              'room': row.room, 'prime_time_minutes': row.prime_time_minutes,'non_prime_time_minutes':row.non_prime_time_minutes },
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
    print('data types', data.dtypes)
    print('pre', data.shape)
    data = data[(data['procedureDtNoTime']>= start_date) & (data['procedureDtNoTime'] < end_date)]
    print('post', data.shape)
    return data.copy()


def get_prime_time_procedure_hours(unit, prime_time_start_time, prime_time_end_time,start_date):
    data = getProcedures(unit,start_date)
    data = remove_weekends(start_date, data)
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
    # print(request.json)
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
    prime_time_hours = get_data(request.json, "primeTime")
    data = dataFrameLookup[unit]
    block_details = get_block_details_data(room,date_requested,block_schedule)
    room_details = get_room_details(unit, date_requested, room, data,prime_time_hours['start'], prime_time_hours['end'])
    return json.dumps({'room':room_details, 'block':block_details}), 200


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
    unit = get_data(request.json, "unit")
    start_date = get_procedure_date('2023-7-1').date()
    block_schedule = get_block_schedule(start_date, block_templates,roomLists, manual_release)
    pt_hours['surgeryInfo'] = get_unit_report_hours(get_prime_time_procedure_hours(unit, prime_time_hours['start'], prime_time_hours['end'],'2023-7-1'))

    # print('pt hours', pt_hours['surgeryInfo'])
    pt_hours = pad_data(pt_hours,unit, '2023-7-1')
    # print('pt hours', pt_hours['surgeryInfo'])
    return json.dumps (pt_hours), 200




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