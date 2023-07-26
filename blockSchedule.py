import pandas as pd;
from datetime import date, timedelta;
from calendar import Calendar
from utilities import create_zulu_datetime_from_string, convert_zulu_to_central_time_from_date, get_date_from_datetime,cast_to_cst

block_search_cols = [ 'candidateId', 'market', 'ministry', 'hospital', 'unit', 'room','flexId',
       'blockName', 'releaseDays', 'type','dow','wom1','wom2', 'wom3','wom4','wom5','start_time','end_time']

manual_release_cols = ['ministry', 'slotId', 'startDtTm','endDtTm']


def convert_manual_release_datetime_strings_to_dates(manual_release):
    manual_release['blockDate'] = manual_release['startDtTm'].apply(lambda x: create_zulu_datetime_from_string(x))
    return manual_release


def convert_manual_release_datetime_to_central_time(manual_release):
    manual_release['blockDate'] = manual_release['blockDate'].apply(lambda x: convert_zulu_to_central_time_from_date(x))
    return manual_release

def cast_manual_release_datetime_to_central_time(manual_release):
    manual_release['blockDate'] = manual_release['blockDate'].apply(lambda x: cast_to_cst(x))
    return manual_release

def convert_start_end_datetime_to_date_only(manual_release):
    manual_release['blockDate'] = manual_release['blockDate'].apply(lambda x: get_date_from_datetime(x))
    return manual_release


def get_manual_release():
   
    manual_release = pd.read_csv('blockrelease.csv', usecols=manual_release_cols)
    manual_release = convert_manual_release_datetime_strings_to_dates(manual_release)
    manual_release =  cast_manual_release_datetime_to_central_time(manual_release)
    manual_release = convert_start_end_datetime_to_date_only(manual_release)
    manual_release = manual_release[(manual_release['ministry'] == 'TNNAS')]
    return manual_release

def getReleaseDate(curday, td):
    day = curday - timedelta(days=td)
    return day

def updateAutoRelease(releaseDay):
    return releaseDay.date() <= date.today()

def updateManualRelease(blockDate, slotId,releaseStatus, releaseData):
    curData = pd.DataFrame(columns=manual_release_cols )
    if releaseStatus:
        return True
    curData = releaseData[(releaseData['blockDate'] == blockDate) & (releaseData['slotId']== slotId)]
    return not(curData.empty)




def create_monthly_block_schedule(curMonth, data,roomLists, releaseData):
    block_schedule = pd.DataFrame(columns=block_search_cols)
    curWOM = 1
    c = Calendar()
    first_day_of_month = True
    for d in [x for x in c.itermonthdates(2023, curMonth) if x.month == curMonth]:
        curDOW = d.isoweekday()
        for roomList in roomLists: 
            for room in roomList:
                curData = data[(data['room'] == room) & (data['dow']== curDOW) &
                                        ((data['wom1'] == curWOM) | (data['wom2'] == curWOM ) |
                                        (data['wom3'] == curWOM) | (data['wom4'] == curWOM)  |
                                        (data['wom5'] == curWOM))].copy()
                if curData.empty:
                    continue 
                curData['blockDate'] = d
                block_schedule = block_schedule.append(curData)
        if ((d.isoweekday() == 6) & (first_day_of_month)):
            curWOM = 1
            first_day_of_month = False
        elif (d.isoweekday() == 6):
            curWOM +=1

    block_no_release = block_schedule
    block_schedule['releaseDays'] = block_schedule['releaseDays'].apply(lambda x: x/1440)
    block_schedule['releaseDate'] = block_schedule.apply(lambda row: getReleaseDate(row['blockDate'],row['releaseDays']),axis=1)
    block_schedule['releaseDate'] = pd.to_datetime(block_schedule['releaseDate'], format='%Y-%m-%d')
    block_schedule['releaseStatus'] = block_schedule.apply(lambda row: updateAutoRelease(row['releaseDate']), axis=1)
    block_schedule['autorelease'] = block_schedule.apply(lambda row: updateAutoRelease(row['releaseDate']), axis=1)
    block_schedule['releaseStatus'] = block_schedule.apply(lambda row: updateManualRelease(row['blockDate'], row['candidateId'],row['releaseStatus'],releaseData),axis=1)
    block_schedule['manualRelease'] =block_schedule.apply(lambda row: updateManualRelease(row['blockDate'], row['candidateId'],row['releaseStatus'],releaseData),axis=1)
    return block_no_release, block_schedule[block_schedule['releaseStatus'] == False]

def get_block_schedule(startDate,endDate, data,roomLists): 
    final_block_schedule = pd.DataFrame()
    final_no_release_schedule = pd.DataFrame()
    manual_release = get_manual_release()
    for curMonth in range(startDate.month, endDate.month):
        print('month', curMonth)
        cur_no_release, cur_block_schedule = create_monthly_block_schedule(curMonth, data,roomLists, manual_release)
        final_block_schedule = pd.concat([final_block_schedule, cur_block_schedule])
        final_no_release_schedule = pd.concat([final_no_release_schedule, cur_no_release])
        # final_no_release_schedule.append(cur_no_release)
    return final_no_release_schedule, final_block_schedule


def get_block_schedule_from_date(start_date, end_date, block_schedule, unit):
    return block_schedule[(block_schedule['blockDate']>= start_date) & (block_schedule['blockDate'] < end_date) &
                                (block_schedule['unit']== unit)]

   
   