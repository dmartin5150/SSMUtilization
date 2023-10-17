import pandas as pd;
from datetime import date, datetime
from flask import Flask, flash, request, redirect, render_template, send_from_directory,abort
from flask_cors import CORS
import json
# test 

from facilityconstants import jriRooms, stmSTORRooms,MTORRooms,orLookUp,CSCRooms,STORRooms
from utilities import get_procedure_date
from blockData import create_block_data
from blockTemplates import get_block_templates_from_file, create_block_templates
from blockSchedule import get_schedule_from_file,create_block_schedules
from gridBlockSchedule import get_grid_block_schedule_from_file,create_grid_block_schedule
from blockOwner import get_num_npis,create_block_owner
from unitData2 import get_unit_data_from_file,create_unit_data,get_soft_block_data_from_file
from blockStats import  get_block_stats_procs_from_file,get_cum_block_stats_and_procs,get_filtered_block_stats
from blockStats import convert_npis_to_int_from_file,get_block_filtered_by_date,get_block_summary, create_block_summary
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
from blockStats import get_block_report_hours,add_block_date,get_cum_block_stats_with_dates,get_block_id_owner_from_file 
from blockProcedureList import get_filtered_proc_list
from openTimes import create_future_open_times,get_future_open_times_from_file,get_open_times
from findroom import create_procedure_stats, get_room_stats_from_file,create_roomstats_summary,get_room_no_surgeon,get_room_stats
from surgeonStats import createSurgeonProcedureStats

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

startDate = get_procedure_date('2023-11-1').date()
endDate = get_procedure_date('2023-12-1').date()
grid_block_schedule = pd.DataFrame()
block_no_release = pd.DataFrame()
block_schedule = pd.DataFrame()
block_owner = pd.DataFrame()
jriData = pd.DataFrame()
STMSTORData = pd.DataFrame()
MTORData = pd.DataFrame()
dataFrameLookup = {}
softBlockLookUp = {}
roomStatsLookUp = {}
num_npis = get_num_npis(block_owner)
cum_block_stats = {}
cum_block_procs = {}
future_open_times = pd.DataFrame()
block_id_owners = pd.DataFrame()


if (timestamp != saved_timestamp):
    block_templates = get_block_templates_from_file("blockTemplates.csv")
    grid_block_schedule = get_grid_block_schedule_from_file('grid_block_schedule.csv')
    block_no_release =  get_schedule_from_file('block_no_release.csv')
    block_schedule =  get_schedule_from_file('block_release_schedule.csv')
    block_owner = pd.read_csv('block_owner_gen.csv')
    jriData = get_unit_data_from_file('jri_gen_data.csv')
    jriSoftBlocks = get_soft_block_data_from_file('jri_soft_block.csv')
    jriRoomStats = get_room_stats_from_file('jriRoomStats.csv')

    STMSTORData  = get_unit_data_from_file('stm_gen_data.csv')
    procDate =  datetime.strptime('2023-09-05', '%Y-%m-%d').date()
    print('STMSTOR proc', STMSTORData[(STMSTORData['procedureDtNoTime'] == procDate)][['room', 'procedureName','procedureDtNoTime']])
    STMSoftBlocks = get_soft_block_data_from_file('stm_soft_block.csv')
    STMSTORRoomStats = get_room_stats_from_file('stmSTORRoomStats.csv')
    MTORData = get_unit_data_from_file('mt_gen_data.csv')
    MTSoftBlocks = get_soft_block_data_from_file('mt_soft_block.csv')
    MTORRoomStats = get_room_stats_from_file('MTORRoomStats.csv')
    CSCData = get_unit_data_from_file('csc_gen_data.csv')
    CSCSoftBlocks = get_soft_block_data_from_file('csc_soft_block.csv')
    CSCRoomStats = get_room_stats_from_file('CSCRoomStats.csv')
    STORData = get_unit_data_from_file('stor_gen_data.csv')
    STORSoftBlocks = get_soft_block_data_from_file('stor_soft_block.csv')
    STORRoomStats = get_room_stats_from_file('STORRoomStats.csv')
    # print('softBlock', CSCSoftBlocks)
    dataFrameLookup = {'BH JRI': jriData, 'STM ST OR': STMSTORData, 'MT OR': MTORData, 'BH CSC': CSCData, 'ST OR':STORData}
    softBlockLookup = {'BH JRI': jriSoftBlocks, 'STM ST OR': STMSoftBlocks, 'MT OR':MTSoftBlocks, 'BH CSC': CSCSoftBlocks, 'ST OR':STORSoftBlocks }
    roomStatsLookUp = {'BH JRI': jriRoomStats, 'STM ST OR': STMSTORRoomStats, 'MT OR': MTORRoomStats, 'BH CSC':CSCRoomStats, 'ST OR':STORRoomStats}
    num_npis = get_num_npis(block_owner)
    cum_block_stats, cum_block_procs = get_block_stats_procs_from_file(startDate,endDate)
    block_id_owners = get_block_id_owner_from_file()
    future_open_times = get_future_open_times_from_file('opentime.csv')
    get_room_no_surgeon(roomStatsLookUp['BH JRI'], future_open_times, get_procedure_date('2023-09-16').date(), 'BH JRI', 'ARTHROPLASTY TOTAL KNEE BILATERAL')

else:
    print('generating data')
    block_data = create_block_data("blockslots.csv")
    print('block_data', block_data.columns)
    block_templates = create_block_templates(block_data, 'blockTemplates.csv')
    print('block templates', block_templates.columns)
    roomLists = [jriRooms,stmSTORRooms,MTORRooms,CSCRooms,STORRooms]
    print('getting block schedule')
    block_no_release, block_schedule =  create_block_schedules(startDate, endDate,block_templates, roomLists,'block_release_schedule.csv', 'block_no_release.csv')
    print('block schedule', block_schedule.columns)
    print('getting block owners')
    grid_block_schedule = create_grid_block_schedule(startDate, endDate, roomLists, block_schedule, 'grid_block_schedule.csv')
    block_owner = create_block_owner("blockowners.csv", 'block_owner_gen.csv')

    print('getting unit data')
    jriData, jriSoftBlocks = create_unit_data('JRIData.csv',grid_block_schedule,'jri_gen_data.csv','jri_soft_block.csv')
    jriRoomStats = create_procedure_stats(jriData.copy(),jriRooms,'jriRoomStats.csv')
    STMSTORData, STMSoftBlocks = create_unit_data('STMSTORData.csv',grid_block_schedule,'stm_gen_data.csv', 'stm_soft_block.csv')
    procDate =  datetime.strptime('2023-09-05', '%Y-%m-%d').date()
    print('STMSTOR proc', STMSTORData[(STMSTORData['procedureName'].str.contains('CRANIOTOMY'))][['room', 'procedureName','procedureDtNoTime', 'procedureDate']])
    STMSTORRoomStats = create_procedure_stats(STMSTORData.copy(),stmSTORRooms,'stmSTORRoomStats.csv')
    MTORData, MTSoftBlocks = create_unit_data('MTORData.csv',grid_block_schedule,'mt_gen_data.csv', 'mt_soft_block.csv')
    MTORRoomStats = create_procedure_stats(MTORData.copy(),MTORRooms,'MTORRoomStats.csv')
    CSCData, CSCSoftBlocks = create_unit_data('CSCData.csv',grid_block_schedule,'csc_gen_data.csv', 'csc_soft_block.csv')
    CSCRoomStats = create_procedure_stats(CSCData.copy(),CSCRooms,'CSCRoomStats.csv')
    STORData, STORSoftBlocks = create_unit_data('STORData.csv',grid_block_schedule,'stor_gen_data.csv','stor_soft_block.csv')
    STORRoomStats = create_procedure_stats(STORData.copy(),STORRooms, 'STORRoomStats.csv')
    dataFrameLookup = {'BH JRI': jriData, 'STM ST OR': STMSTORData, 'MT OR': MTORData, 'BH CSC': CSCData, 'ST OR':STORData}
    softBlockLookup = {'BH JRI': jriSoftBlocks, 'STM ST OR': STMSoftBlocks, 'MT OR':MTSoftBlocks, 'BH CSC': CSCSoftBlocks, 'ST OR':STORSoftBlocks }
    roomStatsLookUp = {'BH JRI': jriRoomStats, 'STM ST OR': STMSTORRoomStats, 'MT OR': MTORRoomStats, 'BH CSC':CSCRoomStats, 'ST OR':STORRoomStats}
    num_npis = get_num_npis(block_owner)
    print('getting block stats')
    
    print('block no release ', block_no_release)
    cum_block_stats, cum_block_procs,block_id_owners = get_cum_block_stats_and_procs(startDate,endDate,block_owner, dataFrameLookup,block_no_release,num_npis)
    print('getting open times')
    future_start_date = get_procedure_date('2023-10-1').date()
    print('block columns', block_schedule.columns)
    future_open_times = create_future_open_times(future_start_date, dataFrameLookup,softBlockLookup, block_schedule,'opentime.csv')


def get_data(request, string):
    data_requested = request[string]
    return data_requested



@app.route('/openrooms')
def get_open_rooms_asnyc():
    unit = get_data(request.json, "unit")
    curStartDate = get_data(request.json, "startDate")
    curStartDate = get_procedure_date(curStartDate).date()
    procedure_name = get_data(request.json, "procedureName")
    room_stats = roomStatsLookUp[unit]
    open_rooms = get_room_no_surgeon(room_stats, future_open_times, curStartDate, unit, procedure_name)
    return json.dumps(get_room_stats(open_rooms)), 200

@app.route('/roomstats', methods=['POST'])
def get_room_stats_async():
    unit = get_data(request.json, "unit")
    roomStats = roomStatsLookUp[unit]
    roomStatsSummary = create_roomstats_summary(roomStats)
    print('summary', roomStatsSummary)
    return json.dumps(roomStatsSummary), 200


@app.route('/opentimes', methods=['POST'])
def get_open_times_async():
    unit = get_data(request.json, "unit")
    curStartDate = get_data(request.json, "startDate")
    curStartDate = get_procedure_date(curStartDate).date()
    return json.dumps(get_open_times(unit, curStartDate,future_open_times)), 200


@app.route('/utilSummary', methods=['POST'])
def get_util_summary_async():
    unit = get_data(request.json, "unit")
    curStartDate = get_data(request.json, "startDate")
    curStartDate = get_procedure_date(curStartDate).date()
    curEndDate = get_data(request.json, 'endDate')
    curEndDate = get_procedure_date(curEndDate).date()
    selectedProviders  = get_data(request.json, "selectedProviders")
    selectedProviders = [int(i) for i in selectedProviders]
    # print('selected providers', selectedProviders)
    selectAll = get_data(request.json, "selectAll")
    selectedRooms = get_data(request.json, "selectedRooms")
    roomSelectionOption = get_data(request.json,'roomSelectionOption')
    prime_time_hours = get_data(request.json, "primeTime")
    procedures = getPTProceduresWithRange(curStartDate,curEndDate, dataFrameLookup[unit])
    if not selectAll:
        procedures = getfilteredPTProcedures(procedures, selectedProviders)
    procedures = getfilteredRoomPTProcedures(procedures, roomSelectionOption, selectedRooms)
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
    block_data_string = f"{startDate.month}_{startDate.year}_{unit}"
    block_stats = cum_block_stats[block_data_string]
    block_stats = get_cum_block_stats_with_dates(curStartDate,curEndDate,unit,cum_block_stats)
    
    if not(selectAll):
        block_stats, flexIds =  get_filtered_block_stats(selectedProviders,block_stats.copy(),startDate,unit)
    block_stats = get_block_filtered_by_date(curStartDate, curEndDate, block_stats,selectAll)
    block_totals = create_block_summary(block_stats)
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
    # print('blocks stats in blocks',block_stats)
    endDate = getEndDate(startDate)
    newProcList = cum_block_procs[block_data_string]
    test_date = get_procedure_date('2023-8-1').date()
    # print('test date blocks', block_stats[block_stats['blockDate'] == test_date]['npis'].drop_duplicates())
    # print('block start, block end', startDate, endDate)
    if not(selectAll):
        print('In not select all')
        block_stats, flexIds =  get_filtered_block_stats(selectedProviders,block_stats.copy(),startDate,unit)
        newProcList = get_filtered_proc_list(flexIds, startDate, endDate, newProcList)
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
    print('getting details')
    data = dataFrameLookup[unit]
    block_details = get_block_details_data(room,date_requested,block_schedule)
    print('block details', block_details)
    room_details = get_room_details(unit, date_requested, room, data,prime_time_hours['start'], prime_time_hours['end'])
    return json.dumps({'room':room_details, 'block':block_details}), 200



@app.route('/surgeon', methods=['GET'])
def get_surgeon_lists_async():
    jriList = get_providers('BH JRI',dataFrameLookup)
    stmSTORList = get_providers('STM ST OR',dataFrameLookup)
    mtORList = get_providers('MT OR',dataFrameLookup)
    cscORList = get_providers('BH CSC',dataFrameLookup)
    stORList = get_providers('ST OR', dataFrameLookup)
    return json.dumps({'BH JRI': jriList,
                        'STM ST OR': stmSTORList,
                        'MT OR': mtORList,
                        'BH CSC':cscORList,
                        'ST OR':stORList}), 200

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