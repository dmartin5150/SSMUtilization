from facilityconstants import orLookUp, units
import pandas as pd
from datetime import date, timedelta,datetime
from blockpseudoschedule import create_pseudo_schedule
import pytz
from utilities import formatProcedureTimes,get_procedure_date,formatMinutes, get_date_range_with_date,get_procedure_date, get_block_date_with_timezone
from softblocks import update_block_times_from_softblocks, update_open_times_from_softblocks


open_time_cols = ['openTimeName', 'proc_date','local_start_time','local_end_time','unit', 'room','unused_block_minutes','formatted_minutes','open_type','release_date', 'open_start_time','block_id']

def get_cur_procs(cur_date, room, procs):
    return procs[(procs['procedureDtNoTime'] ==cur_date) & (procs['room'] == room)].sort_values(by='ptStart')


def get_blocks(cur_date, room, block_schedule):
    return block_schedule[(block_schedule['blockDate'] ==cur_date) & (block_schedule['room'] == room)]

def remove_procedures(unused_time, procedures):
    start_times = procedures['local_start_time'].apply(lambda x:formatProcedureTimes(x)).to_list()
    return unused_time[~unused_time['local_start_time'].isin(start_times)]


def get_filtered_procedures(procs, start, end):
    return procs[((procs['local_start_time'] >= start) & (procs['local_start_time'] < end)) |
                  (procs['local_end_time'] > start) & (procs['local_end_time'] < end)]



def get_unused_times(unused_time, curDate, procedures,curBlock,unit, room,open_type):
    ref_start = 0
    ref_end = 0
    name = ''
    if (open_type == 'BLOCK'):
        ref_start = curBlock['start_time']
        ref_end = curBlock['end_time']
        name = curBlock['blockName']
        release_date = curBlock['releaseDate'].date()
        block_id = curBlock['flexId']
        if ('CLOSED' in curBlock['blockName']):
            open_type = 'CLOSED'
    else:
        ref_start = datetime(curDate.year,curDate.month,curDate.day,int(7),int(0),0).astimezone(pytz.timezone("US/Central"))
        ref_end = datetime(curDate.year,curDate.month,curDate.day,int(16),int(0),0).astimezone(pytz.timezone("US/Central"))
        name = 'OPEN'
        release_date = 'NA'
        block_id = 'NA'

    filtered_procedures = get_filtered_procedures(procedures, ref_start,ref_end)
    # print('ref start', ref_start)
    # print('ref end', ref_end)
    if (filtered_procedures.shape[0] == 0):
        time_difference = (ref_end - ref_start).seconds/60
        formatted_start = formatProcedureTimes(ref_start)
        formatted_end = formatProcedureTimes(ref_end)
        formatted_time = formatMinutes(time_difference)
        row_to_add = pd.DataFrame([{'openTimeName':name,'proc_date':str(curDate),'local_start_time':str(formatted_start),'local_end_time':str(formatted_end),'unit':unit,'room':room,'unused_block_minutes':time_difference,'formatted_minutes':formatted_time,'open_type':open_type,'release_date':release_date, 'open_start_time': ref_start, 'block_id':block_id}])
        unused_time = pd.concat([unused_time, row_to_add])
        # unused_time = unused_time.append({'openTimeName':name,'proc_date':str(curDate),'local_start_time':str(formatted_start),'local_end_time':str(formatted_end),'unit':unit,'room':room,'unused_block_minutes':time_difference,'formatted_minutes':formatted_time,'open_type':open_type,'release_date':release_date, 'open_start_time': ref_start, 'block_id':block_id},ignore_index=True) 
        return unused_time


    filtered_procedures = filtered_procedures.sort_values(by=['local_start_time'])
    filtered_procedures.reset_index(drop=True, inplace=True)


    for ind in filtered_procedures.index:
        start_time = filtered_procedures['local_start_time'][ind]
        end_time = filtered_procedures['local_end_time'][ind]
        duration = (end_time - start_time).seconds/60 
        if ind == 0:
            if (start_time > ref_start):
                if (start_time > ref_end):
                    time_difference = (ref_end - ref_start).seconds/60
                else:
                    time_difference = (start_time - ref_start).seconds/60
                    formatted_time = formatMinutes(time_difference)
                    formatted_start = formatProcedureTimes(ref_start)
                    if (start_time > ref_end):
                        formatted_end = formatProcedureTimes(ref_end)
                    else:
                        formatted_end = formatProcedureTimes(start_time)
                    row_to_add = pd.DataFrame([{'openTimeName':name,'proc_date':str(curDate),'local_start_time':str(formatted_start),'local_end_time':str(formatted_end),'unit':unit, 'room':room,'unused_block_minutes':time_difference,'formatted_minutes':formatted_time,'open_type':open_type,'release_date':release_date, 'open_start_time':ref_start, 'block_id':block_id}])
                    unused_time= pd.concat([unused_time,row_to_add])
                    # unused_time = unused_time.append({'openTimeName':name,'proc_date':str(curDate),'local_start_time':str(formatted_start),'local_end_time':str(formatted_end),'unit':unit, 'room':room,'unused_block_minutes':time_difference,'formatted_minutes':formatted_time,'open_type':open_type,'release_date':release_date, 'open_start_time':ref_start, 'block_id':block_id},ignore_index=True) 
                    
        else:
            if (start_time > ref_start):
                time_difference = (start_time - filtered_procedures['local_end_time'][ind - 1]).seconds/60
                formatted_time = formatMinutes(time_difference)
                formatted_start = formatProcedureTimes(filtered_procedures['local_end_time'][ind - 1])
                formatted_end = formatProcedureTimes(start_time)
                row_to_add = pd.DataFrame([{'openTimeName':name,'proc_date':str(curDate),'local_start_time':str(formatted_start),'local_end_time':str(formatted_end),'unit':unit,'room':room,'unused_block_minutes':time_difference,'formatted_minutes':formatted_time,'open_type':open_type,'release_date':release_date, 'open_start_time': filtered_procedures['local_end_time'][ind - 1], 'block_id': block_id}])
                unused_time = pd.concat([unused_time, row_to_add])
                # unused_time = unused_time.append({'openTimeName':name,'proc_date':str(curDate),'local_start_time':str(formatted_start),'local_end_time':str(formatted_end),'unit':unit,'room':room,'unused_block_minutes':time_difference,'formatted_minutes':formatted_time,'open_type':open_type,'release_date':release_date, 'open_start_time': filtered_procedures['local_end_time'][ind - 1], 'block_id': block_id},ignore_index=True)



        if ind == len(filtered_procedures.index)-1:
            if end_time < ref_end:  
                time_difference = (ref_end - end_time).seconds/60
                formatted_time = formatMinutes(time_difference)
                formatted_start = formatProcedureTimes(end_time)
                formatted_end = formatProcedureTimes(ref_end)
                row_to_add = pd.DataFrame([{'openTimeName':name,'proc_date':str(curDate),'local_start_time':str(formatted_start),'local_end_time':str(formatted_end),'unit':unit,'room':room,'unused_block_minutes':time_difference,'formatted_minutes':formatted_time,'open_type':open_type,'release_date':release_date, 'open_start_time': end_time, 'block_id':block_id}])
                unused_time = pd.concat([unused_time, row_to_add])
                # unused_time = unused_time.append({'openTimeName':name,'proc_date':str(curDate),'local_start_time':str(formatted_start),'local_end_time':str(formatted_end),'unit':unit,'room':room,'unused_block_minutes':time_difference,'formatted_minutes':formatted_time,'open_type':open_type,'release_date':release_date, 'open_start_time': end_time, 'block_id':block_id},ignore_index=True) 

    return unused_time



def combine_blocks_and_procs(curProcs, blocks,start_date,room):
    row_to_add = pd.DataFrame([{'local_start_time': blocks['start_time'], 'local_end_time':blocks['end_time']}])
    return pd.concat([curProcs, row_to_add])
    # return curProcs.append({'local_start_time': blocks['start_time'], 'local_end_time':blocks['end_time']}, ignore_index=True)







def update_block_dates(block_date, curRow):
    ref_start = curRow['start_time']
    ref_end = curRow['end_time']
    curRow['start_time'] =  datetime(block_date.year,block_date.month,block_date.day,ref_start.hour,ref_start.minute,0).astimezone(pytz.timezone("US/Central"))
    curRow['end_time'] = datetime(block_date.year,block_date.month,block_date.day,ref_end.hour,ref_end.minute,0).astimezone(pytz.timezone("US/Central"))
    return curRow

def add_all_blocks(blocks, curProcs):
    for row in range(blocks.shape[0]): 
        curRow = blocks.iloc[row]
        row_to_add = pd.DataFrame([{'local_start_time':curRow['start_time'], 'local_end_time':curRow['end_time']}])
        curProcs = pd.concat([curProcs,row_to_add])
        # curProcs = curProcs.append({'local_start_time':curRow['start_time'], 'local_end_time':curRow['end_time']}, ignore_index=True)
    return curProcs


def get_future_open_times(start_date, end_date, procedures,unit, room, block_schedule,unused_time):

    delta = timedelta(days=1)
    blank_block = pd.DataFrame()
    while start_date <= end_date:
        if ((start_date.isoweekday() == 6) | (start_date.isoweekday() == 7)):
            start_date += delta
            continue
        curProcs = get_cur_procs(start_date,room,procedures)

        curProcs = create_pseudo_schedule(curProcs)
        blocks = get_blocks(start_date,room,block_schedule.copy())
        if (blocks.shape[0] != 0):
            blocks = blocks.apply(lambda row: update_block_dates(start_date, row), axis=1)
            block_procs = curProcs.copy()
            for row in range(blocks.shape[0]):
                unused_time = get_unused_times(unused_time, start_date, block_procs,blocks.iloc[row],unit, room,'BLOCK')
                block_procs = combine_blocks_and_procs(block_procs,blocks.iloc[row],start_date,room)
                block_procs = block_procs.sort_values(by=['local_start_time'])
                block_procs = create_pseudo_schedule(block_procs)  
            curProcs = add_all_blocks(blocks,curProcs)
            curProcs = curProcs.sort_values(by=['local_start_time'])
            # print('added blocks')
            # print('procs', curProcs)
            curProcs = create_pseudo_schedule(curProcs)  
        # print('pseudoschedule', curProcs)
        unused_time = get_unused_times(unused_time, start_date, curProcs,blank_block, unit, room,'OPEN')
        # print('unused time', unused_time)
        start_date += delta
    return unused_time

def update_dates_from_file(future_open_times):
    future_open_times['proc_date'] = future_open_times['proc_date'].apply(lambda x:get_procedure_date(x).date())
    future_open_times['open_start_time'] = future_open_times['open_start_time'].apply(lambda x: get_block_date_with_timezone(x) )
    return future_open_times

def update_dates(future_open_times):
    future_open_times['proc_date'] = future_open_times['proc_date'].apply(lambda x:get_procedure_date(x).date())
    return future_open_times

def create_future_open_times(start_date, dataFrameLookup,softBlockLookup, block_schedule,filename):
    if (start_date.day != 1):
        start_date = date(start_date.year, start_date.month, 1)
    start_date, end_date = get_date_range_with_date(start_date,3)
    unused_time =pd.DataFrame(columns=open_time_cols)
    for unit in units:
        for room in orLookUp[unit]:
            # print(room)
            unused_time = get_future_open_times(start_date, end_date, dataFrameLookup[unit],unit, room, block_schedule,unused_time)
            # print('soft block open')
            unused_time = update_open_times_from_softblocks(start_date, end_date, unit, room, softBlockLookup, unused_time) 
            # print('block soft block open') 
            unused_time = update_block_times_from_softblocks(start_date, end_date, unit, room, block_schedule, unused_time) 
            unused_time = unused_time.sort_values(['proc_date'])
    unused_time = unused_time.drop_duplicates()
    unused_time.to_csv(filename)
    unused_time = update_dates(unused_time)
    return unused_time



def get_future_open_times_from_file(filename):
    future_open_times = pd.read_csv(filename,dtype={'release_date':str})
    future_open_times = update_dates_from_file(future_open_times)
    # print(future_open_times['release_date'])
    return future_open_times


def get_open_times(unit, start_date, open_times):
    if (start_date.day != 1):
        start_date = date(start_date.year, start_date.month, 1)
    start_date, end_date = get_date_range_with_date(start_date,1)
    # print('open time', type(open_times.iloc[0]['proc_date']), open_times.iloc[0]['proc_date'])
    selected_times = open_times[(open_times['unit'] == unit) & (open_times['proc_date'] >= start_date) & (open_times['proc_date'] <= end_date)]
    # print (selected_times['openTimeName'])
    future_open_times = [{'id': index,'unit': row.unit,'name':row.openTimeName, 'local_start_time':row.local_start_time, 'local_end_time':row.local_end_time,
                          'room':row.room, 'unused_block_minutes':row.unused_block_minutes, 'formatted_minutes':row.formatted_minutes, 
                          'open_type':row.open_type, 'proc_date': str(row.proc_date), 'release_date':str(row.release_date), 'open_start_time':row.open_start_time.strftime('%Y-%m-%dT%H:%M:%SZ')
                          } for index, row in selected_times.iterrows()] 
    return future_open_times
