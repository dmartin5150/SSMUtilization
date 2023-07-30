import pandas as pd;
from datetime import date, timedelta;
from calendar import Calendar
from utilities import create_zulu_datetime_from_string, convert_zulu_to_central_time_from_date, get_date_from_datetime,cast_to_cst
from utilities import get_block_date_with_timezone,get_procedure_date

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




def create_monthly_block_schedule(curMonth, block_templates,curTemplates,roomLists, releaseData,block_change_dates):
    block_schedule = pd.DataFrame(columns=block_search_cols)
    curWOM = 1
    c = Calendar()
    first_day_of_month = True
    for d in [x for x in c.itermonthdates(2023, curMonth) if x.month == curMonth]:
        if first_day_of_month:
            curTemplates = update_block_templates_from_date(block_templates, d)
        if d in block_change_dates:
            # print('date change',d)
            curTemplates = update_block_templates_from_date(block_templates, d)
        curDOW = d.isoweekday()
        for roomList in roomLists: 
            for room in roomList:
                curData = curTemplates[(curTemplates['room'] == room) & (curTemplates['dow']== curDOW) &
                                        ((curTemplates['wom1'] == curWOM) | (curTemplates['wom2'] == curWOM ) |
                                        (curTemplates['wom3'] == curWOM) | (curTemplates['wom4'] == curWOM)  |
                                        (curTemplates['wom5'] == curWOM))].copy()
                if curData.empty:
                    continue 
                curData['blockDate'] =d
                kurtz = curData[curData['blockName'].str.contains('Kurtz')]
                # if not kurtz.empty:
                #     print(d, curDOW, curWOM,room)
                #     print(curData[['blockName','start_date','end_date','start_time','end_time','dow','wom1','wom2','wom3','wom4','wom5']])
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


def get_start_end_dates_from_templates(templates):
    start_dates = set(templates['start_date'])
    end_dates = set(templates['end_date'])
    # print('start_dates', start_dates.shape)
    # print('end_date', end_dates.shape)
    resulting_list = list(start_dates)
    resulting_list.extend(x for x in end_dates if x not in resulting_list)
    return resulting_list

def update_block_templates_from_date(block_templates, curDate):
    return block_templates[(block_templates['start_date'] <= curDate) & 
                           (block_templates['end_date'] > curDate)]


def get_block_schedule(startDate,endDate, block_templates,roomLists): 
    final_block_schedule = pd.DataFrame()
    final_no_release_schedule = pd.DataFrame()
    manual_release = get_manual_release()
    block_change_dates = get_start_end_dates_from_templates(block_templates)
    for curMonth in range(startDate.month, endDate.month):
        curTemplates = update_block_templates_from_date(block_templates, startDate)
        print('month', curMonth)
        cur_no_release, cur_block_schedule = create_monthly_block_schedule(curMonth,block_templates, curTemplates,roomLists, manual_release,block_change_dates)
        final_block_schedule = pd.concat([final_block_schedule, cur_block_schedule])
        final_no_release_schedule = pd.concat([final_no_release_schedule, cur_no_release])
        # final_no_release_schedule.append(cur_no_release)
    return final_no_release_schedule, final_block_schedule


def get_block_schedule_from_date(start_date, end_date, block_schedule, unit):
    return block_schedule[(block_schedule['blockDate']>= start_date) & (block_schedule['blockDate'] < end_date) &
                                (block_schedule['unit']== unit)]

def update_time_dates_from_file(block_schedule):
    block_schedule['start_time'] = block_schedule['start_time'].apply(lambda x: get_block_date_with_timezone(x))
    block_schedule['end_time'] = block_schedule['end_time'].apply(lambda x: get_block_date_with_timezone(x))
    block_schedule['start_date'] = block_schedule['start_date'].apply(lambda x: get_procedure_date(x))
    block_schedule['end_date'] = block_schedule['end_date'].apply(lambda x: get_procedure_date(x))
    block_schedule['blockDate'] = block_schedule['blockDate'].apply(lambda x: get_procedure_date(x))
    block_schedule['releaseDate'] = block_schedule['releaseDate'].apply(lambda x: get_procedure_date(x))
    return block_schedule


def get_schedule_from_file(filename):
    block_schedule = pd.read_csv(filename)
    block_schedule = update_time_dates_from_file(block_schedule)
    return block_schedule

   
   