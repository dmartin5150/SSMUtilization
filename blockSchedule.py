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
    # print('curday', curday, 'td',td)
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

def remove_overlapping_blocks(blocks):
    updated_blocks = pd.DataFrame(columns=block_search_cols)
    not_overlapped = pd.DataFrame(columns=block_search_cols)
    curBlocks = pd.DataFrame(columns=block_search_cols)
    # print(blocks.columns)
    blockNames = blocks[blocks.duplicated(['blockName'],keep=False)]['blockName'].drop_duplicates().values.tolist()

    for name in blockNames:
        curBlocks = blocks[(blocks['blockName'] == name)].reset_index(drop=True)
        # print('pre', curBlocks)
        updated_block = curBlocks.iloc[0].copy()
        # print('updated block', updated_block)
        for curIndex in range(1,curBlocks.shape[0]):
            cur_block = curBlocks.iloc[curIndex]
            if (cur_block['start_time'] < updated_block['start_time']):
                updated_block['start_time'] = cur_block['start_time']
            if (cur_block['end_time'] > updated_block['end_time']):
                updated_block['end_time'] = cur_block['end_time']
        # print('appending block', updated_block)
        row_to_append = pd.DataFrame([cur_block])
        updated_blocks= pd.concat([updated_blocks,row_to_append])
        # print('post', updated_blocks)
    not_overlapped = blocks[~blocks.duplicated(['blockName'],keep=False)]
    # print('not_overlapped', not_overlapped)
    if not not_overlapped.empty:
        updated_blocks = pd.concat([updated_blocks, not_overlapped])
    # print('updated_blocks', updated_blocks)
    return updated_blocks

    
        


            
            
            


def create_monthly_block_schedule(curMonth, block_templates,curTemplates,roomLists, releaseData,block_change_dates):
    block_schedule = pd.DataFrame(columns=block_search_cols)
    curWOM = 1
    start_day = 0
    c = Calendar()
    first_day_of_month = True
    # print('closed blocks', block_templates[block_templates['flexId'] == -1])
    testDate = get_procedure_date('2023-10-31').date()
    # print('in Create monthly block scheduled')
    # print("I********")
    # print(curMonth)
    # print(curTemplates[curTemplates['flexId'] == 112103])
    for d in [x for x in c.itermonthdates(2023, curMonth) if x.month == curMonth]:
        if (first_day_of_month):
            curWOM = 1
            if((d.isoweekday() == 6) | (d.isoweekday() == 7)):
                start_day = 1
            else:
                first_day_of_month = False
                start_day = d.isoweekday()
        else:
            if(d.isoweekday() == start_day):
                curWOM += 1
        # print('day ', d, 'WOM h', curWOM)
        # print(curTemplates[curTemplates['flexId'] == 112103])
        # print('day ', d)
        if (d == testDate):
            print('Day is 10/31')
            print('WOM', curWOM, "dow",d.isoweekday())
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
                # print('date', d, 'curWOM', curWOM,'dow', curDOW)
                if (curData.shape[0] > 1):
                    # print(d, curDOW, curWOM,room)
                    # print(curData[curData.duplicated(['blockName'],keep=False)])
                    curData = remove_overlapping_blocks(curData)    
                if (block_schedule.shape[0] == 0):
                    block_schedule = curData
                else:
                    block_schedule = block_schedule.reset_index(drop=True)
                    block_schedule = pd.concat([block_schedule,curData])
                
                # grayson = curData[curData['flexId'] == 112103]
                # if not closed.empty:
                #     print(d, curDOW, curWOM,room)
                #     print(curData[['blockName','start_date','end_date','start_time','end_time','dow','wom1','wom2','wom3','wom4','wom5']])
                # grayson = curData[curData['blockName'].str.contains('Grayson')]
                # if not grayson.empty:
                #     print('FOUND Grayson')
                #     print(d, curDOW, curWOM,room)
                #     print(curData[['blockName','start_date','end_date','start_time','end_time','dow','wom1','wom2','wom3','wom4','wom5']])
                #     curData.to_csv('curBlockScheduleData', curData)
                #     block_schedule.to_csv('curblockschedule.csv')
                # block_schedule = block_schedule.append(curData)
                # block_schedule = block_schedule.reset_index()


        

    block_no_release = block_schedule
    block_schedule.to_csv('curblockschedule.csv')

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

def addWeekday(block_schedule):
    block_schedule['weekday'] = block_schedule['blockDate'].apply(lambda x: x.isoweekday())
    return block_schedule


def get_block_schedule(startDate,endDate, block_templates,roomLists): 
    final_block_schedule = pd.DataFrame()
    final_no_release_schedule = pd.DataFrame()
    manual_release = get_manual_release()
    block_change_dates = get_start_end_dates_from_templates(block_templates)
    for curMonth in range(startDate.month, endDate.month):
        curTemplates = update_block_templates_from_date(block_templates, startDate)
        # print('month', curMonth)
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
    block_schedule['blockDate'] = block_schedule['blockDate'].apply(lambda x: x.date())
    block_schedule['releaseDate'] = block_schedule['releaseDate'].apply(lambda x: get_procedure_date(x))
    return block_schedule


def get_schedule_from_file(filename):
    block_schedule = pd.read_csv(filename)
    block_schedule = update_time_dates_from_file(block_schedule)
    # print('block schedule', type(block_schedule.iloc[0]['blockDate']))
    return block_schedule

def create_block_schedules(startDate, endDate,block_templates, roomLists,bs_ouput_filename, bnr_output_filename):
    block_no_release, block_schedule = get_block_schedule(startDate,endDate, block_templates,roomLists) 
    # print('CLOSED BLOCKS', block_no_release[(block_no_release['unit']== 'BH JRI') & (block_no_release['flexId'] == -1)])
    block_no_release = block_no_release.drop_duplicates(subset=['blockName','unit','room','start_time','end_time','blockDate'])
    block_schedule = block_schedule.drop_duplicates(subset=['blockName','unit','room','start_time','end_time','blockDate'])
    block_no_release.to_csv(bnr_output_filename,index=False)
    block_schedule.to_csv(bs_ouput_filename,index=False)
    return block_no_release, block_schedule

   
   