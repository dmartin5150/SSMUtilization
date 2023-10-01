import pandas as pd
from monthlyBlockStats import getNudgeBlockData, getSummaryMonthlyBlocks
from monthlyOpenTimes import get_monthly_unused_block, getSurgeonList
from nudgeProcedures import getNudgeProcedures
from datetime import date
from utilities import get_procedure_date,convert_zulu_to_central_time_from_date,create_zulu_datetime_from_string,create_zulu_datetime_from_string_format2
from utilities import get_text_of_time,get_block_date_with_timezone


units = ['BH JRI','STM ST OR', 'MT OR','BH CSC','ST OR']
months = ['7','8','9','10']



elite = pd.read_csv('TNNAS  Surgeons - Elite.csv')
toa = pd.read_csv('TNNAS  Surgeons - TOA.csv')
howell_allen = pd.read_csv('TNNAS  Surgeons - Howell Allen.csv')
rutherford = pd.read_csv('Rutherford Block.csv')
all_blocks = pd.DataFrame()

block_owners = pd.read_csv('block_id_owners.csv')
elite_npi = elite['NPI']
# print(elite_npi)

elite_blocks = block_owners.merge(elite_npi, how='inner', left_on='npi', right_on='NPI')
# print(elite_blocks)

howell_allen_npi = howell_allen['NPI']

howell_allen_blocks = block_owners.merge(howell_allen_npi, how='inner', left_on='npi', right_on='NPI')
# print(howell_allen_blocks)

toa_npi = toa['NPI']

toa_blocks = block_owners.merge(toa_npi, how='inner', left_on='npi', right_on='NPI')
# print(toa_blocks)

all_blocks = pd.concat([elite_blocks, howell_allen_blocks])
all_blocks = pd.concat([all_blocks, toa_blocks ])
all_npis = all_blocks['NPI']
# print(all_blocks)


def writeDataToSheet(sheetName,blockData,startRow,writer,indexValue):
    if (startRow == 0):
        blockData.to_excel(writer, sheet_name=sheetName, index=indexValue)
    else:
        blockData.to_excel(writer, sheet_name=sheetName, startrow= startRow , index=indexValue)

def changeMonth(curMonth):
    if (curMonth == 6):
        return 'June'
    elif(curMonth == 7):
        return 'July'
    elif(curMonth == 8):
        return 'August'
    elif(curMonth == 9):
        return 'September'
    elif(curMonth == 10):
        return 'October'

def convertDate(x):
    if not isinstance(x,str): 
        return get_procedure_date(x).date()
    return x

fileName = 'toa.xlsx'
writer = pd.ExcelWriter(fileName, engine='xlsxwriter')
monthly_block_data,daily_block_data = getNudgeBlockData(units, months, toa)
# print('got montly data')
surgeonList,flexIdList = getSurgeonList(monthly_block_data.copy())
monthlySummary = monthly_block_data[['TOA Surgeon','utilization','month']].sort_values(by=['TOA Surgeon','month']).drop_duplicates()
monthlySummary['monthName'] = monthly_block_data['month'].apply(lambda x: changeMonth(x))

monthlySummary = monthlySummary.pivot(index='TOA Surgeon', columns='monthName', values='utilization')
monthlySummary = monthlySummary[['July','August','September','October']]
# newMonthlySummary = monthlySummary.copy()
# print('new', newMonthlySummary[['July','August','September','October']])
writeDataToSheet('Monthly',monthlySummary,0,writer, True)
flexIds = monthly_block_data['flexId'].drop_duplicates().to_list()
unused_times = get_monthly_unused_block(flexIds, months)
print('unused times', unused_times.columns)
procedures = getNudgeProcedures(units, daily_block_data)
# procedures['procedureDate'] = procedures['procedureDate'].apply(lambda x: get_procedure_date(x).date())
surgeonHeading = pd.DataFrame()
surgeonHeading = surgeonHeading.append({'Surgeon':'test'}, ignore_index=True)
blockHeading = pd.DataFrame()
blockHeading = blockHeading.append({'Block Definition':''}, ignore_index=True)
dailyBlockHeading = pd.DataFrame()
dailyBlockHeading = dailyBlockHeading.append({'Block Date':''}, ignore_index=True)
procedureHeading = pd.DataFrame()
procedureHeading = procedureHeading.append({'Procedures performed in different room':''}, ignore_index=True)
openTimeHeading = pd.DataFrame()
openTimeHeading = openTimeHeading.append({'Unused Block Times':''}, ignore_index=True)
daily_block_data['blockDate'] = daily_block_data['blockDate'].apply(lambda x: get_procedure_date(x).date())
daily_block_data.to_csv('dailyblockdata.csv')
dailySummary = daily_block_data[(daily_block_data['blockDate'] >= date.today())]
dailySummary.rename(columns={'room':'Room','blockDate':'Block Date', 'start_time':'Start Time', 'end_time':'End Time','releaseDate':'Release Date'}, inplace=True)
dailySummary = dailySummary[['flexId', 'Room','Block Date','Start Time','End Time','Release Date']].drop_duplicates()
# print('flex list', flexIdList)
for surgeon, flexId in zip(surgeonList, flexIdList):
    currentExcelRow = 0
    currentWorksheet = surgeon
    surgeonHeading.iloc[0]['Surgeon'] = surgeon
    writeDataToSheet(currentWorksheet,surgeonHeading,currentExcelRow,writer,False)
    currentExcelRow = currentExcelRow + 3
    curDailyData = dailySummary[dailySummary['flexId'] == flexId]
    blockDates = curDailyData['Block Date'].drop_duplicates().to_list()
    for blockDate in blockDates:
        print('blockDate', blockDate)
        dailyBlockHeading.iloc[0]= blockDate
        writeDataToSheet(currentWorksheet,dailyBlockHeading,currentExcelRow,writer,False)
        currentExcelRow = currentExcelRow + 3
        blockDailyData = curDailyData[curDailyData['Block Date'] == blockDate][['Room', 'Block Date','Start Time', 'End Time','Release Date']]
        blockDailyData['Start Time'] = blockDailyData['Start Time'].apply(lambda x: get_block_date_with_timezone(x))
        blockDailyData['Start Time'] = blockDailyData['Start Time'].apply(lambda x: get_text_of_time(x))
        blockDailyData['End Time'] = blockDailyData['End Time'].apply(lambda x: get_block_date_with_timezone(x))
        blockDailyData['End Time'] = blockDailyData['End Time'].apply(lambda x: get_text_of_time(x))
        writeDataToSheet(currentWorksheet,blockDailyData,currentExcelRow,writer,False)
        currentExcelRow = 2 + currentExcelRow + blockDailyData.shape[0]
        # procedures['procDate'] = procedures['procDate'].apply(lambda x:convertDate(x) )
        # print('TYPE DATE', type(blockDate), type(procedures.iloc[0]['procDate']))
        curBlockProcData = procedures[(procedures['flexId'] == flexId) & (procedures['procDate'] == str(blockDate))].drop_duplicates()
        # curBlockProcData = procedures[(procedures['flexId'] == flexId)].drop_duplicates()
        # print(procedures['flexId'].to_list())
        if (flexId == 535003):
            print('FOUND IT')
            # print(curBlockProcData)
        if (not curBlockProcData.empty):
            writeDataToSheet(currentWorksheet,procedureHeading,currentExcelRow,writer,False)
            currentExcelRow = currentExcelRow + 2
            print('COLUMNS', curBlockProcData.columns)
            curBlockProcData.rename(columns={'block room':'Block Room', 'proc room':'Procedure Room','startTime':'Start Time','endTime':'End Time'},inplace=True)
            curBlockProcData['Start Time'] = curBlockProcData['Start Time'].apply(lambda x:create_zulu_datetime_from_string_format2(x))
            curBlockProcData['End Time'] = curBlockProcData['End Time'].apply(lambda x:create_zulu_datetime_from_string_format2(x))
            print('type of curblock', type(curBlockProcData.iloc[0]['Start Time']),curBlockProcData.iloc[0]['Start Time'])
            curBlockProcData['Start Time'] = curBlockProcData['Start Time'].apply(lambda x:get_text_of_time(convert_zulu_to_central_time_from_date(x)))
            curBlockProcData['End Time'] = curBlockProcData['End Time'].apply(lambda x:get_text_of_time((convert_zulu_to_central_time_from_date(x))))
            curBlockProcData = curBlockProcData[['Block Room', 'Procedure Room', 'Start Time', 'End Time']].drop_duplicates()
            writeDataToSheet(currentWorksheet,curBlockProcData,currentExcelRow,writer,False)
            currentExcelRow = 2 + currentExcelRow + curBlockProcData.shape[0]
        curUnusedTimes = unused_times[(unused_times['block_id'] == flexId) & (unused_times['proc_date'] == blockDate)].drop_duplicates()
        if (not curUnusedTimes.empty):
            curUnusedTimes.rename(columns={'room':'Room', 'openTimeName':'Block Name','local_start_time':'Start Time','local_end_time':'End Time','formatted_minutes':'Unused Time'},inplace=True)
            # print(curUnusedTimes.columns)
            # curUnusedTimes['Start Time']= curUnusedTimes['Start Time'].apply(lambda x: get_block_date_with_timezone(x))
            # curUnusedTimes['Start Time']= curUnusedTimes['Start Time'].apply(lambda x: get_text_of_time(x))
            # curUnusedTimes['End Time'] = curUnusedTimes['End Time'].apply(lambda x: get_block_date_with_timezone(x))
            # curUnusedTimes['End Time'] = curUnusedTimes['End Time'].apply(lambda x: get_text_of_time(x))
            curUnusedTimes = curUnusedTimes[['Room','Block Name','Start Time','End Time','Unused Time']]
            writeDataToSheet(currentWorksheet,openTimeHeading,currentExcelRow,writer,False)
            currentExcelRow = currentExcelRow + 2
            writeDataToSheet(currentWorksheet,curUnusedTimes,currentExcelRow,writer,False)
            currentExcelRow = 2 + currentExcelRow + curUnusedTimes.shape[0]
writer.save()

