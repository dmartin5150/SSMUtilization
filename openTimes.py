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
    print('type', block_schedule.iloc[0]['blockDate'],type(block_schedule.iloc[0]['blockDate']))
    print(cur_date, type(cur_date))

    return block_schedule[(block_schedule['blockDate'] ==cur_date) & (block_schedule['room'] == room)]

def remove_procedures(unused_time, procedures):
    print('in remove procedures')
    start_times = procedures['local_start_time'].apply(lambda x:formatProcedureTimes(x)).to_list()
    print('start times', start_times)
    return unused_time[~unused_time['local_start_time'].isin(start_times)]


def get_unused_times(unused_time, curDate, procedures,curBlock, room,open_type):
    ref_start = 0
    ref_end = 0
    name = ''
    if (open_type == 'BLOCK'):
        # print('curblock', curBlock)
        ref_start = curBlock['start_time']
        ref_end = curBlock['end_time']
        name = curBlock['blockName']
        
    else:
        ref_start = datetime(curDate.year,curDate.month,curDate.day,int(7),int(0),0).astimezone(pytz.timezone("US/Central"))
        ref_end = datetime(curDate.year,curDate.month,curDate.day,int(16),int(0),0).astimezone(pytz.timezone("US/Central"))
        name = 'OPEN'



    if (procedures.shape[0] == 0):
        time_difference = (ref_end - ref_start).seconds/60
        formatted_start = formatProcedureTimes(ref_start)
        formatted_end = formatProcedureTimes(ref_end)
        formatted_time = formatMinutes(time_difference)
        unused_time = unused_time.append({'name':name,'proc_date':str(curDate),'local_start_time':str(formatted_start),'local_end_time':str(formatted_end),'room':room,'unused_block_minutes':time_difference,'formated_minutes':formatted_time,'open_type':open_type},ignore_index=True) 
        return unused_time


    procedures = procedures.sort_values(by=['local_start_time'])
    print('procedures', procedures)
    print('ref start', ref_start)
    print('ref end', ref_end)
    procedures.reset_index(drop=True, inplace=True)

    for ind in procedures.index:
        start_time = procedures['local_start_time'][ind]
        end_time = procedures['local_end_time'][ind]
        duration = (end_time - start_time).seconds/60
        # print('start', start_time, 'end', end_time)
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
                    # print ('ut', unused_time)
        else:
            if (start_time > ref_start):
                time_difference = (start_time - procedures['local_end_time'][ind - 1]).seconds/60
                formatted_time = formatMinutes(time_difference)
                formatted_start = formatProcedureTimes(procedures['local_end_time'][ind - 1])
                formatted_end = formatProcedureTimes(start_time)
                unused_time = unused_time.append({'name':name,'proc_date':str(curDate),'local_start_time':str(formatted_start),'local_end_time':str(formatted_end),'room':room,'unused_block_minutes':time_difference,'formated_minutes':formatted_time,'open_type':open_type},ignore_index=True) 
                # print('time difference', time_difference)
                # print ('ut', unused_time)
        formatted_time = formatMinutes(duration)
        formatted_start = formatProcedureTimes(start_time)
        formatted_end = formatProcedureTimes(end_time)
        unused_time = unused_time.append({'name':name,'proc_date':str(curDate),'local_start_time':str(formatted_start),'local_end_time':str(formatted_end),'room':room,'unused_block_minutes':duration,'formated_minutes':formatted_time,'open_type':open_type},ignore_index=True) 
        # print('time difference', duration)
        # print ('ut', unused_time)
        if ind == len(procedures.index)-1:
            if end_time < ref_end:  
                time_difference = (ref_end - end_time).seconds/60
                formatted_time = formatMinutes(time_difference)
                formatted_start = formatProcedureTimes(end_time)
                formatted_end = formatProcedureTimes(ref_end)
                unused_time = unused_time.append({'name':name,'proc_date':str(curDate),'local_start_time':str(formatted_start),'local_end_time':str(formatted_end),'room':room,'unused_block_minutes':time_difference,'formated_minutes':formatted_time,'open_type':open_type},ignore_index=True) 
                print('time difference', time_difference)
                # print ('ut', unused_time)

    unused_time = remove_procedures(unused_time,procedures)
    return unused_time



def combine_blocks_and_procs(curProcs, unused_blocks,start_date,room):
    curBlocks = unused_blocks[(unused_blocks['proc_date']== start_date) & (unused_blocks['room']== room) & (unused_blocks['open_type']== 'BLOCK')][['local_start_time','local_end_time']]
    return pd.concat([curProcs,curBlocks])




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
            for row in range(blocks.shape[0]):
                unused_time = get_unused_times(unused_time, start_date, curProcs,blocks.iloc[row], room,'BLOCK')
                curProcs = combine_blocks_and_procs(curProcs, unused_time,start_date,room)
                curProcs = create_pseudo_schedule(curProcs)        
        unused_time = get_unused_times(unused_time, start_date, curProcs,blank_block, room,'OPEN')
        print('unused', unused_time)
        start_date += delta
    return unused_time



