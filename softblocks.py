import pandas as pd
from datetime import date, timedelta,datetime
from utilities import create_date_with_time, formatProcedureTimes, formatMinutes

def get_soft_blocks(start_date, softBlocks, room):
    if (softBlocks.shape[0] == 0):
        return pd.DataFrame()
    return softBlocks[(softBlocks['room'] == room) & (softBlocks['proc_date'] == start_date)]

def get_open_times(start_date, openTimes, room):
    curTimes = openTimes[(openTimes['room'] == room) & (openTimes['proc_date'] == str(start_date)) &
                         (openTimes['open_type'] == 'OPEN')]
    if (curTimes.shape[0] == 0):
        return []
    else:
        return curTimes.index.tolist()
    
def get_soft_block_indexes(start_date, unused_time, room):
    curTimes = unused_time[(unused_time['room'] == room) & (unused_time['proc_date'] == str(start_date)) & 
                            (unused_time['open_type'] == 'SOFT')]
    if (curTimes.shape[0] == 0):
        return []
    else:
       return curTimes.index.tolist() 
    
def  get_block_times(start_date, block_schedule, room):
    return block_schedule[(block_schedule['blockDate'] == str(start_date)) & (block_schedule['room'] == room)]
                          

def update_open_time_with_column(column_name, data_index, updated_value, data):
    data.iloc[data_index,data.columns.get_loc(column_name)] = updated_value


def add_open_time(name, block_type,unit,room, block_date, start_time, end_time, release_date, unusedTime):
        curIndex = len(unusedTime.index)
        formatted_start = formatProcedureTimes(start_time)
        formatted_end = formatProcedureTimes(end_time)
        time_difference = (end_time - start_time).seconds/60
        formatted_time = formatMinutes(time_difference)
        unusedTime.loc[curIndex]=[name,str(block_date), formatted_start,formatted_end, unit,room,time_difference,formatted_time,block_type, release_date]
        return curIndex


def compare_soft_and_open_times(soft_start_time, soft_end_time, open_start_time, open_end_time,curIndex, unusedTime):
    create_new_block = False
    if (open_end_time <= soft_start_time):
        return create_new_block
    if (open_start_time >= soft_end_time):
        return create_new_block
    if ((open_start_time == soft_start_time) & (open_end_time <= soft_end_time)):
        update_open_time_with_column('release_date', curIndex, 'REMOVE',unusedTime)
        print('adding remove')
    if ((open_start_time == soft_start_time) & (open_end_time > soft_end_time)):  
        formatted_start = formatProcedureTimes(soft_end_time)
        time_difference = (open_end_time - soft_end_time ).seconds/60
        formatted_time = formatMinutes(time_difference)
        update_open_time_with_column('local_start_time', curIndex, formatted_start, unusedTime)
        update_open_time_with_column('unused_block_minutes', curIndex, time_difference, unusedTime)
        update_open_time_with_column('formatted_minutes', curIndex, formatted_time, unusedTime)
        print('changing local_start 1')
    if ((open_start_time  < soft_start_time) & (open_end_time > soft_start_time) & (open_end_time <= soft_end_time)):
        formatted_end = formatProcedureTimes(soft_start_time)
        time_difference = (soft_start_time - open_start_time).seconds/60
        formatted_time = formatMinutes(time_difference)
        update_open_time_with_column('local_end_time', curIndex, formatted_end,unusedTime)
        update_open_time_with_column('unused_block_minutes', curIndex, time_difference, unusedTime)
        update_open_time_with_column('formatted_minutes', curIndex, formatted_time, unusedTime)
        print('changing local_end 1')
    if ((open_start_time  < soft_start_time) & (open_end_time > soft_start_time) & (open_end_time > soft_end_time)):
        formatted_end = formatProcedureTimes(soft_start_time)
        time_difference = (soft_start_time - open_start_time).seconds/60
        formatted_time = formatMinutes(time_difference)
        update_open_time_with_column('local_end_time', curIndex, formatted_end,unusedTime)
        update_open_time_with_column('unused_block_minutes', curIndex, time_difference, unusedTime)
        update_open_time_with_column('formatted_minutes', curIndex, formatted_time, unusedTime)
        print('changing local_end 2')
        # create new open time with start time soft end time and end time at open end time 
        create_new_block = True
 
    if ((open_start_time > soft_start_time) & (open_end_time <= soft_end_time)):
        update_open_time_with_column('release_date', curIndex, 'REMOVE',unusedTime)
        print('adding remove')
    if ((open_start_time > soft_start_time) & (open_end_time > soft_end_time)):
        formatted_start = formatProcedureTimes(soft_end_time)
        time_difference = (open_end_time-soft_end_time).seconds/60
        formatted_time = formatMinutes(time_difference)
        update_open_time_with_column('local_start_time', curIndex, formatted_start, unusedTime)
        update_open_time_with_column('unused_block_minutes', curIndex, time_difference, unusedTime)
        update_open_time_with_column('formatted_minutes', curIndex, formatted_time, unusedTime)
        print('changing local_start')
    return create_new_block
    

    



def change_open_times(soft_date, softBlockRow, openIndexes, unusedTime,unit,room):
    recheck_blocks = False
    # print('entering change open times')
    soft_start_time = softBlockRow['local_start_time']
    soft_end_time = softBlockRow['local_end_time']
    # print('open indexes', openIndexes)
    add_open_time('SOFT BLOCK', 'SOFT',unit,room, soft_date, soft_start_time, soft_end_time, "NA", unusedTime)   
    for curIndex in openIndexes:
        openTime = unusedTime.iloc[curIndex]
        # print('open time before', openTime)
        # print('curIndex', curIndex)
        open_start_time_text = openTime['local_start_time']
        open_end_time_text = openTime['local_end_time']
        # print('open type', openTime['open_type'])
        # print('end time', open_end_time_text)
        open_start_time = create_date_with_time(soft_date, open_start_time_text)
        open_end_time = create_date_with_time(soft_date, open_end_time_text)
        if(compare_soft_and_open_times(soft_start_time, soft_end_time, open_start_time, open_end_time,curIndex, unusedTime)):
            # print('creating new open block', soft_date, room, soft_end_time, open_end_time )
            add_open_time('OPEN', 'OPEN',unit,room, soft_date, soft_end_time, open_end_time, "NA", unusedTime)  
            recheck_blocks = True
        # print('opentime after', unusedTime.iloc[curIndex])
    return recheck_blocks

 





def change_soft_block_from_block(soft_date, blockRow, soft_block_indexes, unusedTime,unit,room):
    recheck_blocks = False
    print('entering change open times')
    block_start_time = blockRow['start_time']
    block_end_time = blockRow['end_time']
    print('soft block indexes', soft_block_indexes)
    for curIndex in soft_block_indexes:
        openTime = unusedTime.iloc[curIndex]
        print('open time before', openTime)
        print('curIndex', curIndex)
        open_start_time_text = openTime['local_start_time']
        open_end_time_text = openTime['local_end_time']
        open_start_time = create_date_with_time(soft_date, open_start_time_text)
        open_end_time = create_date_with_time(soft_date, open_end_time_text)
        if(compare_soft_and_open_times(block_start_time, block_end_time, open_start_time, open_end_time,curIndex, unusedTime)):
            print('creating new Soft block', soft_date, room, block_end_time, open_end_time )
            add_open_time('SOFT BLOCK', 'SOFT',unit,room, soft_date, block_end_time, open_end_time, "NA", unusedTime)  
            recheck_blocks = True
        print('opentime after', unusedTime.iloc[curIndex])
    return recheck_blocks 

def update_open_times_from_softblocks(start_date, end_date, unit, room, softBlockLookup, unused_time):
    delta = timedelta(days=1)
    while start_date <= end_date:
        repeat_block = False
        print('open time dates', start_date)
        print('ROOM', room)
        if ((start_date.isoweekday() == 6) | (start_date.isoweekday() == 7)):
            start_date += delta
            continue
        soft_blocks = get_soft_blocks(start_date, softBlockLookup[unit], room)
        openIndexes = get_open_times(start_date, unused_time, room)
        if ((soft_blocks.shape[0] != 0) & (len(openIndexes) != 0)):
            # print('in soft blocks', soft_blocks[['local_start_time','local_end_time']])
            for block_row in range(soft_blocks.shape[0]):
                # print('block row', block_row)
                repeat_block = (change_open_times(start_date, soft_blocks.iloc[block_row], openIndexes, unused_time, unit, room))
        if (repeat_block):
            continue
        start_date += delta

    return unused_time[unused_time['release_date'] != 'REMOVE']

def update_block_times_from_softblocks(start_date, end_date, unit, room,block_schedule, unused_time):
    delta = timedelta(days=1)
    while start_date <= end_date:
        repeat_block = False
        print('block-softblock times', start_date)
        print('ROOM', room)
        if ((start_date.isoweekday() == 6) | (start_date.isoweekday() == 7)):
            start_date += delta
            continue
        soft_block_indexes = get_soft_block_indexes(start_date, unused_time, room)
        blocks  = get_block_times(start_date, block_schedule, room)
        if ((blocks.shape[0] != 0) & (len(soft_block_indexes) != 0)):
            print('in blocks', blocks[['start_time','end_time']])
            for block_row in range(blocks.shape[0]):
                print('block row', block_row)
                repeat_block = (change_soft_block_from_block(start_date, blocks.iloc[block_row], soft_block_indexes, unused_time, unit, room))
        if (repeat_block):
            continue
        start_date += delta

    return unused_time