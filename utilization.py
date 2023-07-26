import pandas as pd;
from datetime import date, timedelta, datetime, timezone;
import calendar;
import json;
import pytz;
from flask import Flask, flash, request, redirect, render_template, send_from_directory,abort
from flask_cors import CORS
from calendar import Calendar, monthrange
import re

from dailyUtilization import get_daily_room_utilization
from providers import get_providers
from facilityconstants import jriRooms, stmSTORRooms,MTORRooms
from utilities import get_procedure_date,get_procedure_date_with_time,create_zulu_datetime_from_string,convert_zulu_to_central_time_from_date,get_date_from_datetime
from blockData import get_block_data
from blockTemplates import get_block_templates
from blockSchedule import get_block_schedule,get_block_schedule_from_date
from gridBlockSchedule import get_grid_block_schedule
from blockProcedureList import get_filtered_proc_list
from blockDetails import get_block_details_data
from blockOwner import get_block_owner,get_num_npis
from unitData2 import get_unit_data
from primeTimeProcedures import getPTProcedures, get_filtered_procedures,getEndDate
from roomDetails import get_room_details
from padData import pad_data
from blockStats import get_block_stats, get_block_report_hours,get_filtered_block_stats
from surgeonStats import get_surgeon_stats
from primeTimePTHoursOpt import get_prime_time_procedure_hours,get_unit_report_hours
from blockFiles import get_file_timestamp,file_exists,get_saved_timestamp,write_time_stamp



app = Flask(__name__)
CORS(app)
app.secret_key = "seamless care" # for encrypting the session
app.config['CORS_HEADERS'] = 'Content-Type'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024



timestamp = get_file_timestamp("blockslots.csv")
write_time_stamp('blocktimestamp.txt',timestamp)
saved_timestamp =''
if file_exists('blocktimestamp.txt'):
    saved_timestamp = get_saved_timestamp('blocktimestamp.txt')
print('saved time stamp', saved_timestamp)

if (timestamp == saved_timestamp):
    print('timestamps match')
else:
    print('timestamps dont match')

block_data = pd.read_csv("blockslots.csv")
block_data = get_block_data(block_data)
block_templates = get_block_templates(block_data)
startDate = get_procedure_date('2023-7-1').date()
endDate = get_procedure_date('2023-9-1').date()
roomLists = [jriRooms,stmSTORRooms,MTORRooms]
block_no_release, block_schedule = get_block_schedule(startDate,endDate, block_templates,roomLists) 

grid_block_schedule = get_grid_block_schedule(startDate,endDate,roomLists,block_schedule)  
block_owner = pd.read_csv("blockowners.csv")
block_owner = get_block_owner(block_owner)
print ('block_owner', block_owner['ownerId'].drop_duplicates().shape)




jriData = get_unit_data('JRIData.csv',grid_block_schedule)
STMSTORData = get_unit_data('STMSTORData.csv',grid_block_schedule)
MTORData = get_unit_data('MTORData.csv',grid_block_schedule)
dataFrameLookup = {'BH JRI': jriData, 'STM ST OR': STMSTORData, 'MT OR': MTORData}



def get_data(request, string):
    data_requested = request[string]
    return data_requested


@app.route('/blocks', methods=['POST'])
def get_block_data_async():
    unit = get_data(request.json, "unit")
    selectAll = get_data(request.json, "selectAll")
    curDate = get_data(request.json, "startDate")
    print('curdate',curDate)
    startDate = get_procedure_date(curDate).date()
    selectedProviders  = get_data(request.json, "selectedProviders")
    print('getting pt procedures')
    procedures = getPTProcedures(startDate,dataFrameLookup[unit])
    print ('getting num npis')
    num_npis = get_num_npis(block_owner)
    # print('getting room lis')
    # roomLists = [jriRooms,stmSTORRooms,MTORRooms]
    print('getting endate')
    endDate = getEndDate(startDate)
    block_schedule = get_block_schedule_from_date(startDate, endDate, block_no_release,unit)
    # print('getting schedule')
    # block_no_release,block_schedule = get_block_schedule(startDate,endDate, block_templates,roomLists)
    # if not(selectAll):
    #     procedures = get_filtered_procedures(procedures, selectedProviders)
    # block_stats,procList = get_block_stats(block_no_release,block_owner,procedures, unit,num_npis,curDate,selectAll,selectedProviders)
    block_stats,newProcList = get_block_stats(block_schedule,block_owner,procedures, unit,num_npis,curDate,selectAll,selectedProviders)
    print ('stats',block_stats.columns)
    
    if not(selectAll):
        block_stats, flexIds =  get_filtered_block_stats(selectedProviders,block_stats.copy(),curDate,unit)
        # print('flexIds', flexIds)
        newProcList = get_filtered_proc_list(flexIds, startDate, endDate, newProcList)
        # print(newProcList)
    return json.dumps({'grid':get_block_report_hours(block_stats),'details':newProcList}), 200


@app.route('/stats', methods=['POST'])
def get_surgeon_stats_async():
    unit = get_data(request.json, "unit")
    npi = int(get_data(request.json, "NPI"))
    name = get_data(request.json, "name")
    # print('name', name, 'npi',npi)
    return get_surgeon_stats(unit,name, npi,dataFrameLookup), 200


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
    jriList = get_providers('BH JRI',dataFrameLookup)
    stmSTORList = get_providers('STM ST OR',dataFrameLookup)
    mtORList = get_providers('MT OR',dataFrameLookup)
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
    # procedures = getPTProcedures(startDate, unit,block_templates)
    procedures = getPTProcedures(startDate,dataFrameLookup[unit])
    print('curDate', curDate)
    pt_hours['surgeryInfo'] = get_unit_report_hours(get_prime_time_procedure_hours(procedures, prime_time_hours['start'], prime_time_hours['end'],curDate))
    pt_hours = pad_data(pt_hours,unit, curDate)
    return json.dumps (pt_hours), 200



app.run(host='0.0.0.0', port=5001)