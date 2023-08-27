import pandas as pd
from datetime import date, timedelta,datetime
from utilities import create_date_with_time,get_text_of_time

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


def compare_soft_and_open_times(soft_start_time, soft_end_time, open_start_time, open_end_time,curIndex, unusedTime):
    if (open_end_time <= soft_start_time):
        return
    if (open_start_time >= soft_end_time):
        return 
    if ((open_start_time == soft_start_time) & (open_end_time <= soft_end_time)):
        update_open_time_with_column('release_date', curIndex, 'REMOVE',unusedTime)
        print('adding remove')
    if ((open_start_time == soft_start_time) & (open_end_time > soft_end_time)):  
        replacement_value = get_text_of_time(soft_end_time)
        update_open_time_with_column('local_start_time', curIndex, replacement_value,unusedTime)
        print('changing local_start 1')
    if ((open_start_time  < soft_start_time) & (open_end_time > soft_start_time) & (open_end_time <= soft_end_time)):
        replacement_value = get_text_of_time(soft_start_time)
        update_open_time_with_column('local_end_time', curIndex, replacement_value,unusedTime)
        print('changing local_end 1')
    if ((open_start_time  < soft_start_time) & (open_end_time > soft_start_time) & (open_end_time > soft_end_time)):
        replacement_value = get_text_of_time(soft_start_time)
        update_open_time_with_column('local_end_time', curIndex, replacement_value,unusedTime)
        print('changing local_end 2')
        # create new open time with start time soft end time and end time at open end time
    if ((open_start_time > soft_start_time) & (open_end_time <= soft_end_time)):
        update_open_time_with_column('release_date', curIndex, 'REMOVE',unusedTime)
        print('adding remove')
    if ((open_start_time > soft_start_time) & (open_end_time > soft_end_time)):
        replacement_value = get_text_of_time(soft_end_time)
        update_open_time_with_column('local_start_time 2', curIndex, replacement_value, unusedTime)
        print('changing local_start')

    



def change_open_times(soft_date, softBlockRow, openIndexes, unusedTime):
    print('entering change open times')
    soft_start_time = softBlockRow['local_start_time']
    soft_end_time = softBlockRow['local_end_time']
    print('open indexes', openIndexes)
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
                change_open_times(start_date, soft_blocks.iloc[block_row], openIndexes, unused_time)
        start_date += delta

    return unused_time