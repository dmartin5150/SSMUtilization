import pandas as pd;
from datetime import date, timedelta;
from calendar import Calendar


block_search_cols = [ 'candidateId', 'market', 'ministry', 'hospital', 'unit', 'room','flexId',
       'blockName', 'releaseDays', 'type','dow','wom1','wom2', 'wom3','wom4','wom5','start_time','end_time']

manual_release_cols = ['ministry', 'slotId', 'startDtTm','endDtTm']

def get_manual_release():
   
    manual_release = pd.read_csv('blockrelease.csv', usecols=manual_release_cols, parse_dates=['startDtTm','endDtTm'])
    manual_release['blockDate'] = manual_release['startDtTm'].apply(lambda x: x.date())
    manual_release = manual_release[(manual_release['ministry'] == 'TNNAS')]
    manual_release.to_csv('manualRelease.csv')
    return manual_release

def getReleaseDate(curday, td):
    day = curday - timedelta(days=td)
    return day

def updateAutoRelease(releaseDay):
    return releaseDay <= date.today()

def updateManualRelease(blockDate, slotId,releaseStatus, releaseData):
    curData = pd.DataFrame(columns=manual_release_cols )
    if releaseStatus:
        return True
    curData = releaseData[(releaseData['blockDate'] == blockDate) & (releaseData['slotId']== slotId)]
    return not(curData.empty)




def create_block_schedule(startDate, data,roomLists, releaseData):

    block_schedule = pd.DataFrame(columns=block_search_cols)
    curWOM = 1
    c = Calendar()
    first_day_of_month = True
    for d in [x for x in c.itermonthdates(2023, startDate.month) if x.month == startDate.month]:
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
    # block_schedule.to_csv('blockSchedule.csv')
    # return block_schedule
    return block_no_release, block_schedule[block_schedule['releaseStatus'] == False]

def get_block_schedule(startDate, data,roomLists): 
    manual_release = get_manual_release()
    return create_block_schedule(startDate,data,roomLists,manual_release)