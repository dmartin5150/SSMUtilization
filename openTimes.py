from facilityconstants import orLookUp, units
import pandas as pd
from datetime import date, timedelta,datetime
from blockpseudoschedule import create_pseudo_schedule
import pytz
from utilities import formatProcedureTimes,get_procedure_date,formatMinutes

open_time_cols = ['name', 'proc_date','local_start_time','local_end_time','room','unused_block_minutes','formated_minutes','open_type']

def get_cur_procs(cur_date, room, procs):
    return procs[(procs['procedureDtNoTime'] ==cur_date) & (procs['room'] == room)]


def get_blocks(cur_date, room, block_schedule):
    return block_schedule[(block_schedule['blockDate'] ==cur_date) & (block_schedule['room'] == room)]

def remove_procedures(unused_time, procedures):
    start_times = procedures['local_start_time'].apply(lambda x:formatProcedureTimes(x)).to_list()
    return unused_time[~unused_time['local_start_time'].isin(start_times)]


def get_filtered_procedures(procs, start, end):
    return procs[((procs['local_start_time'] >= start) & (procs['local_start_time'] < end)) |
                  (procs['local_end_time'] > start) & (procs['local_end_time'] < end)]



def get_unused_times(unused_time, curDate, procedures,curBlock, room,open_type):
    ref_start = 0
    ref_end = 0
    name = ''
    if (open_type == 'BLOCK'):
        ref_start = curBlock['start_time']
        ref_end = curBlock['end_time']
        name = curBlock['blockName']
        
    else:
        ref_start = datetime(curDate.year,curDate.month,curDate.day,int(7),int(0),0).astimezone(pytz.timezone("US/Central"))
        ref_end = datetime(curDate.year,curDate.month,curDate.day,int(16),int(0),0).astimezone(pytz.timezone("US/Central"))
        name = 'OPEN'

    filtered_procedures = get_filtered_procedures(procedures, ref_start,ref_end)

    if (filtered_procedures.shape[0] == 0):
        time_difference = (ref_end - ref_start).seconds/60
        formatted_start = formatProcedureTimes(ref_start)
        formatted_end = formatProcedureTimes(ref_end)
        formatted_time = formatMinutes(time_difference)
        unused_time = unused_time.append({'name':name,'proc_date':str(curDate),'local_start_time':str(formatted_start),'local_end_time':str(formatted_end),'room':room,'unused_block_minutes':time_difference,'formated_minutes':formatted_time,'open_type':open_type},ignore_index=True) 
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
                    unused_time = unused_time.append({'name':name,'proc_date':str(curDate),'local_start_time':str(formatted_start),'local_end_time':str(formatted_end),'room':room,'unused_block_minutes':time_difference,'formated_minutes':formatted_time,'open_type':open_type},ignore_index=True) 
                    
        else:
            if (start_time > ref_start):
                time_difference = (start_time - filtered_procedures['local_end_time'][ind - 1]).seconds/60
                formatted_time = formatMinutes(time_difference)
                formatted_start = formatProcedureTimes(filtered_procedures['local_end_time'][ind - 1])
                formatted_end = formatProcedureTimes(start_time)
                unused_time = unused_time.append({'name':name,'proc_date':str(curDate),'local_start_time':str(formatted_start),'local_end_time':str(formatted_end),'room':room,'unused_block_minutes':time_difference,'formated_minutes':formatted_time,'open_type':open_type},ignore_index=True) 

        formatted_time = formatMinutes(duration)
        formatted_start = formatProcedureTimes(start_time)
        formatted_end = formatProcedureTimes(end_time)
        unused_time = unused_time.append({'name':name,'proc_date':str(curDate),'local_start_time':str(formatted_start),'local_end_time':str(formatted_end),'room':room,'unused_block_minutes':duration,'formated_minutes':formatted_time,'open_type':open_type},ignore_index=True) 

        if ind == len(filtered_procedures.index)-1:
            if end_time < ref_end:  
                time_difference = (ref_end - end_time).seconds/60
                formatted_time = formatMinutes(time_difference)
                formatted_start = formatProcedureTimes(end_time)
                formatted_end = formatProcedureTimes(ref_end)
                unused_time = unused_time.append({'name':name,'proc_date':str(curDate),'local_start_time':str(formatted_start),'local_end_time':str(formatted_end),'room':room,'unused_block_minutes':time_difference,'formated_minutes':formatted_time,'open_type':open_type},ignore_index=True) 

    unused_time = remove_procedures(unused_time,filtered_procedures)
    return unused_time



def combine_blocks_and_procs(curProcs, blocks,start_date,room):
    return curProcs.append({'local_start_time': blocks['start_time'], 'local_end_time':blocks['end_time']}, ignore_index=True)



def update_block_dates(block_date, blocks):
    for row in range(blocks.shape[0]):
        curRow = blocks.iloc[row]
        ref_start = curRow['start_time']
        ref_end = curRow['end_time']
        blocks['start_time'] =  datetime(block_date.year,block_date.month,block_date.day,ref_start.hour,ref_start.minute,0).astimezone(pytz.timezone("US/Central"))
        blocks['end_time'] = datetime(block_date.year,block_date.month,block_date.day,ref_end.hour,ref_end.minute,0).astimezone(pytz.timezone("US/Central"))
    return blocks


def get_future_open_times(start_date, end_date, procedures,room, block_schedule):
    unused_time =pd.DataFrame(columns=open_time_cols)
    delta = timedelta(days=1)
    blank_block = pd.DataFrame()
    print(block_schedule.columns)
    while start_date <= end_date:
        curProcs = get_cur_procs(start_date,room,procedures)
        curProcs = create_pseudo_schedule(curProcs)
        blocks = get_blocks(start_date,room,block_schedule)
        if (blocks.shape[0] != 0):
            blocks = update_block_dates(start_date, blocks.copy())
            for row in range(blocks.shape[0]):
                unused_time = get_unused_times(unused_time, start_date, curProcs,blocks.iloc[row], room,'BLOCK')
                curProcs = combine_blocks_and_procs(curProcs,blocks.iloc[row],start_date,room)
                curProcs = curProcs.sort_values(by=['local_start_time'])
                curProcs = create_pseudo_schedule(curProcs)    
        unused_time = get_unused_times(unused_time, start_date, curProcs,blank_block, room,'OPEN')
        print('unused time', unused_time)
        start_date += delta
    return unused_time



