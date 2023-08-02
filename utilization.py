import pandas as pd;

from flask import Flask, flash, request, redirect, render_template, send_from_directory,abort
from flask_cors import CORS
import json

from facilityconstants import jriRooms, stmSTORRooms,MTORRooms,orLookUp
from utilities import get_procedure_date
from blockData import create_block_data
from blockTemplates import get_block_templates_from_file, create_block_templates
from blockSchedule import get_schedule_from_file,create_block_schedules
from gridBlockSchedule import get_grid_block_schedule_from_file,create_grid_block_schedule
from blockOwner import get_num_npis,create_block_owner
from unitData2 import get_unit_data_from_file,create_unit_data
from blockStats import  get_block_stats_props_from_file,get_cum_block_stats_and_procs,get_filtered_block_stats
from blockStats import convert_npis_to_int_from_file,get_block_filtered_by_date,get_block_summary
from blockFiles import get_file_timestamp,file_exists,get_saved_timestamp,write_time_stamp,write_block_json
from padData import pad_data
from primeTimePTHoursOpt import get_prime_time_procedure_hours,get_unit_report_hours,get_prime_time_procedures_from_range
from primeTimePTHoursOpt import get_total_pt_minutes,get_pt_totals
from primeTimeProcedures import getPTProcedures,getEndDate,getPTProceduresWithRange,getfilteredPTProcedures,getfilteredRoomPTProcedures
from providers import get_providers
from roomDetails import get_room_details
from blockDetails import get_block_details_data
from dailyUtilization import get_daily_room_utilization
from surgeonStats import get_surgeon_stats
from blockStats import get_block_report_hours,add_block_date,get_cum_block_stats_with_dates
from blockProcedureList import get_filtered_proc_list



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

block_templates = pd.DataFrame()

startDate = get_procedure_date('2023-3-1').date()
endDate = get_procedure_date('2023-9-1').date()
grid_block_schedule = pd.DataFrame()
block_no_release = pd.DataFrame()
block_schedule = pd.DataFrame()
block_owner = pd.DataFrame()
jriData = pd.DataFrame()
STMSTORData = pd.DataFrame()
MTORData = pd.DataFrame()
dataFrameLookup = {}
num_npis = get_num_npis(block_owner)
cum_block_stats = {}
cum_block_procs = {}

if (timestamp == saved_timestamp):
    block_templates = get_block_templates_from_file("blockTemplates.csv")
    grid_block_schedule = get_grid_block_schedule_from_file('grid_block_schedule.csv')
    block_no_release =  get_schedule_from_file('block_no_release.csv')
    block_schedule =  get_schedule_from_file('block_release_schedule.csv')
    block_owner = pd.read_csv('block_owner_gen.csv')
    jriData = get_unit_data_from_file('jri_gen_data.csv')
    STMSTORData = get_unit_data_from_file('stm_gen_data.csv')
    MTORData = get_unit_data_from_file('mt_gen_data.csv')
    dataFrameLookup = {'BH JRI': jriData, 'STM ST OR': STMSTORData, 'MT OR': MTORData}
    num_npis = get_num_npis(block_owner)
    cum_block_stats, cum_block_procs = get_block_stats_props_from_file(startDate,endDate)

else:
    block_data = create_block_data("blockslots.csv")
    block_templates = create_block_templates(block_data, 'blockTemplates.csv')
    roomLists = [jriRooms,stmSTORRooms,MTORRooms]
    
    block_no_release, block_schedule =  create_block_schedules(startDate, endDate,block_templates, roomLists,'block_release_schedule.csv', 'block_no_release.csv')
    grid_block_schedule = create_grid_block_schedule(startDate, endDate, roomLists, block_schedule, 'grid_block_schedule.csv')
    block_owner = create_block_owner("blockowners.csv", 'block_owner_gen.csv')


    jriData = create_unit_data('JRIData.csv',grid_block_schedule,'jri_gen_data.csv')
    STMSTORData = create_unit_data('STMSTORData.csv',grid_block_schedule,'stm_gen_data.csv')
    MTORData = create_unit_data('MTORData.csv',grid_block_schedule,'mt_gen_data.csv')
    dataFrameLookup = {'BH JRI': jriData, 'STM ST OR': STMSTORData, 'MT OR': MTORData}
    num_npis = get_num_npis(block_owner)
    cum_block_stats, cum_block_procs = get_cum_block_stats_and_procs(startDate,endDate,block_owner, dataFrameLookup,block_no_release,num_npis)



def get_data(request, string):
    data_requested = request[string]
    return data_requested


@app.route('/utilSummary', methods=['POST'])
def get_util_summary_async():
    unit = get_data(request.json, "unit")
    curStartDate = get_data(request.json, "startDate")
    curStartDate = get_procedure_date(curStartDate).date()
    curEndDate = get_data(request.json, 'endDate')
    curEndDate = get_procedure_date(curEndDate).date()
    selectedProviders  = get_data(request.json, "selectedProviders")
    selectedProviders = [int(i) for i in selectedProviders]
    print('selected providers', selectedProviders)
    selectAll = get_data(request.json, "selectAll")
    selectedRooms = get_data(request.json, "selectedRooms")
    roomSelectionOption = get_data(request.json,'roomSelectionOption')
    prime_time_hours = get_data(request.json, "primeTime")
    # total_pt_minutes = get_data(request.json, "totalPTMinutes")
    procedures = getPTProceduresWithRange(curStartDate,curEndDate, dataFrameLookup[unit])
    print('procedures1', procedures)
    if not selectAll:
        procedures = getfilteredPTProcedures(procedures, selectedProviders)
        print('procedures2', procedures)
    procedures = getfilteredRoomPTProcedures(procedures, roomSelectionOption, selectedRooms)
    # print('procedures3', procedures)
    total_pt_minutes = get_total_pt_minutes(orLookUp[unit],procedures['room'], prime_time_hours,roomSelectionOption,selectedRooms,curStartDate, curEndDate)
    ptHours = get_prime_time_procedures_from_range(procedures, prime_time_hours['start'], prime_time_hours['end'])
    pt_totals = get_pt_totals(ptHours,total_pt_minutes,curStartDate,curEndDate,roomSelectionOption,prime_time_hours)
    return json.dumps(pt_totals), 200


@app.route('/blocktotals', methods=['POST'])
def get_block_totals_async():
    unit = get_data(request.json, "unit")
    selectAll = get_data(request.json, "selectAll")
    curStartDate = get_data(request.json, "startDate")
    curEndDate = get_data(request.json, "endDate")
    curStartDate = get_procedure_date(curStartDate).date()
    curEndDate = get_procedure_date(curEndDate).date()
    selectedProviders  = get_data(request.json, "selectedProviders")
    block_data_string = f"{startDate.month}_{startDate.year}_{unit}"
    print('selected provider', selectedProviders)
    # print('keys', cum_block_stats.keys())
    block_stats = get_cum_block_stats_with_dates(curStartDate,curEndDate,unit,cum_block_stats)
    # block_stats = cum_block_stats[block_data_string]
    # block_stats = add_block_date(block_stats)
    # print('block stats pre', block_stats)
    # block_stats = get_block_filtered_by_date(curStartDate, curEndDate, block_stats)
    print('block stats post', block_stats['npis'])
    print('got block stats')
    if not(selectAll):
        block_stats, flexIds =  get_filtered_block_stats(selectedProviders,block_stats.copy(),startDate,unit)
    block_stats = get_block_filtered_by_date(curStartDate, curEndDate, block_stats,selectAll)
    block_totals = get_block_summary(block_stats)
    return json.dumps(block_totals), 200




@app.route('/blocks', methods=['POST'])
def get_block_data_async():
    unit = get_data(request.json, "unit")
    selectAll = get_data(request.json, "selectAll")
    curDate = get_data(request.json, "startDate")
    startDate = get_procedure_date(curDate).date()
    selectedProviders  = get_data(request.json, "selectedProviders")
    # procedures = getPTProcedures(startDate,dataFrameLookup[unit])
    # num_npis = get_num_npis(block_owner)
    block_data_string = f"{startDate.month}_{startDate.year}_{unit}"
    block_stats = cum_block_stats[block_data_string]
    newProcList = cum_block_procs[block_data_string]
    endDate = getEndDate(startDate)
    
    if not(selectAll):
        block_stats, flexIds =  get_filtered_block_stats(selectedProviders,block_stats.copy(),startDate,unit)
        newProcList = get_filtered_proc_list(flexIds, startDate, endDate, newProcList)
    print('block columns', block_stats.columns)
    return json.dumps({'grid':get_block_report_hours(block_stats),'details':newProcList}), 200


@app.route('/stats', methods=['POST'])
def get_surgeon_stats_async():
    unit = get_data(request.json, "unit")
    npi = int(get_data(request.json, "NPI"))
    name = get_data(request.json, "name")
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
    procedures = getPTProcedures(startDate,dataFrameLookup[unit])
    print('procedures', procedures.columns)
    pt_hours['surgeryInfo'] = get_unit_report_hours(get_prime_time_procedure_hours(procedures, prime_time_hours['start'], prime_time_hours['end'],curDate))
    pt_hours = pad_data(pt_hours,unit, curDate)
    return json.dumps (pt_hours), 200



app.run(host='0.0.0.0', port=5001)