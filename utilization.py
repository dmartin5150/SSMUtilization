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
from utilities import formatProcedureTimes, formatMinutes,all_dates_current_month,get_procedure_date
from blockData import get_block_data
from blockTemplates import get_block_templates
from blockSchedule import get_block_schedule
from gridBlockSchedule import get_grid_block_schedule
from blockDetails import get_block_details_data
from blockOwner import get_block_owner,get_num_npis
from unitData import get_unit_data
from primeTimeProcedures import getPTProcedures
from roomDetails import get_room_details
from padData import pad_data
from blockStats import get_block_stats, get_block_report_hours
from surgeonStats import get_surgeon_stats
from primeTimeProcedureHours import get_prime_time_procedure_hours,get_unit_report_hours


app = Flask(__name__)
CORS(app)
app.secret_key = "seamless care" # for encrypting the session
app.config['CORS_HEADERS'] = 'Content-Type'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024



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


def get_filtered_procedures(procedures, npi_list): 
    return procedures[procedures['NPI'].isin(npi_list)]





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
    num_npis = get_num_npis(block_owner)
    roomLists = [jriRooms,stmSTORRooms,MTORRooms]
    block_no_release,block_schedule = get_block_schedule(startDate, block_templates,roomLists)
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
    return get_surgeon_stats(unit,name, npi,dataFrameLookup), 200


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