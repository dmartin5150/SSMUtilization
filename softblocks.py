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
    if (open_end_time <= soft_start_time):
        return
    if (open_start_time >= soft_end_time):
        return 
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
    if ((open_start_time > soft_start_time) & (open_end_time <= soft_end_time)):
        update_open_time_with_column('release_date', curIndex, 'REMOVE',unusedTime)
        print('adding remove')
    if ((open_start_time > soft_start_time) & (open_end_time > soft_end_time)):
        formatted_start = formatProcedureTimes(soft_end_time)
        time_difference = (open_end_time-soft_end_time).seconds/60
        formatted_time = formatMinutes(time_difference)
        update_open_time_with_column('local_start_time 2', curIndex, formatted_end, unusedTime)
        update_open_time_with_column('unused_block_minutes', curIndex, time_difference, unusedTime)
        update_open_time_with_column('formatted_minutes', curIndex, formatted_time, unusedTime)
        print('changing local_start')

    



def change_open_times(soft_date, softBlockRow, openIndexes, unusedTime,unit,room):
    print('entering change open times')
    soft_start_time = softBlockRow['local_start_time']
    soft_end_time = softBlockRow['local_end_time']
    print('open indexes', openIndexes)
    add_open_time('SOFT BLOCK', 'SOFT',unit,room, soft_date, soft_start_time, soft_end_time, "NA", unusedTime)   
    for curIndex in openIndexes:
        openTime = unusedTime.iloc[curIndex]
        print('open time before', openTime)
        print('curIndex', curIndex)
        open_start_time_text = openTime['local_start_time']
        open_end_time_text = openTime['local_end_time']
        print('open type', openTime['open_type'])
        print('end time', open_end_time_text)
        # print('local end time',open_end_time_text)
        open_start_time = create_date_with_time(soft_date, open_start_time_text)
        open_end_time = create_date_with_time(soft_date, open_end_time_text)
        # print('open start time', open_start_time, 'type', type(open_start_time))
        # print('open end time', open_end_time, 'type', type(open_end_time))
        compare_soft_and_open_times(soft_start_time, soft_end_time, open_start_time, open_end_time,curIndex, unusedTime)
        # print('open start', open_start_time)
        # print('open end', open_end_time)
        print('opentime after', unusedTime.iloc[curIndex])
           

def update_open_times_from_softblocks(start_date, end_date, unit, room, softBlockLookup, unused_time):
    delta = timedelta(days=1)
    blank_block = pd.DataFrame()
    # print('lookup ', softBlockLookup)
    while start_date <= end_date:
        print('open time dates', start_date)
        print('ROOM', room)
        if ((start_date.isoweekday() == 6) | (start_date.isoweekday() == 7)):
            start_date += delta
            continue
        soft_blocks = get_soft_blocks(start_date, softBlockLookup[unit], room)
        # print('update open times', unused_time)
        # print('soft blocks', soft_blocks)
        openIndexes = get_open_times(start_date, unused_time, room)
        if ((soft_blocks.shape[0] != 0) & (len(openIndexes) != 0)):
            print('in soft blocks', soft_blocks[['local_start_time','local_end_time']])
            for block_row in range(soft_blocks.shape[0]):
                print('block row', block_row)
                change_open_times(start_date, soft_blocks.iloc[block_row], openIndexes, unused_time, unit, room)
        start_date += delta

    return unused_time