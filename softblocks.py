import pandas as pd
from datetime import date, timedelta,datetime


def get_soft_blocks(start_date, softBlocks, room):
    # print('GET SOFT BLOCKS', softBlocks)
    if (softBlocks.shape[0] == 0):
        return pd.DataFrame()
    return softBlocks[(softBlocks['room'] == room) & (softBlocks['proc_date'] == start_date)]

def get_open_times(start_date, openTimes, room):
    print('open times', openTimes)
    curTimes = openTimes[(openTimes['room'] == room) & (openTimes['proc_date'] == str(start_date))]
    if (curTimes.shape[0] == 0):
        return []
    else:
        return curTimes.index.tolist()


def change_open_times(softBlockRow, openIndexes, unusedTime):
    print('unused time 1', unusedTime)
    softStartTime = softBlockRow['local_start_time']
    softEndTime = softBlockRow['local_end_time']
    print('soft start', softStartTime)
    print('soft end time', softEndTime)
    for curIndex in openIndexes:
        print('cur index', curIndex)
        # print('open time', openTime)
        print('unused time 2', unusedTime)
        openTime = unusedTime.iloc[curIndex]
        openStart = openTime['local_start_time']
        openEnd = openTime['local_end_time']
        print('open start', openStart)
        print('open end', openEnd)
        

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
        print('unused time 4', unused_time)
        openIndexes = get_open_times(start_date, unused_time, room)
        if ((soft_blocks.shape[0] != 0) & (len(openIndexes) != 0)):
            for block_row in range(soft_blocks.shape[0]):
                print('block row', block_row)
                unused_time = change_open_times(soft_blocks.iloc[block_row], openIndexes, unused_time)
        start_date += delta

    return unused_time