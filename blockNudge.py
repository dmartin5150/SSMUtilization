import pandas as pd
from monthlyBlockStats import getNudgeBlockData, getSummaryMonthlyBlocks
from monthlyOpenTimes import get_monthly_unused_block, getSurgeonList
from nudgeProcedures import getNudgeProcedures
from datetime import date
from utilities import get_procedure_date


units = ['BH JRI','STM ST OR', 'MT OR','BH CSC','ST OR']
months = ['7','8','9','10']



elite = pd.read_csv('TNNAS  Surgeons - Elite.csv')
toa = pd.read_csv('TNNAS  Surgeons - TOA.csv')
howell_allen = pd.read_csv('TNNAS  Surgeons - Howell Allen.csv')
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


def writeDataToSheet(sheetName,blockData,startRow,writer):
    if (startRow == 0):
        blockData.to_excel(writer, sheet_name=sheetName, index=False)
    else:
        blockData.to_excel(writer, sheet_name=sheetName, startrow= startRow , index=False)




fileName = 'toa.xlsx'
writer = pd.ExcelWriter(fileName, engine='xlsxwriter')
monthly_block_data,daily_block_data = getNudgeBlockData(units, months, toa)
surgeonList,flexIdList = getSurgeonList(monthly_block_data.copy())
monthlySummary = monthly_block_data[['TOA Surgeon','utilization','month']].sort_values(by=['TOA Surgeon','month'])
writeDataToSheet('Monthly',monthlySummary,0,writer)
flexIds = monthly_block_data['flexId'].drop_duplicates().to_list()
unused_times = get_monthly_unused_block(flexIds, months)
print('unused time', unused_times.columns)
procedures = getNudgeProcedures(units, daily_block_data)
procedures['procDate'] = procedures['procDate'].apply(lambda x: get_procedure_date(x).date())
surgeonHeading = pd.DataFrame()
surgeonHeading = surgeonHeading.append({'Surgeon':'test'}, ignore_index=True)
blockHeading = pd.DataFrame()
blockHeading = blockHeading.append({'Block Definition':''}, ignore_index=True)
dailyBlockHeading = pd.DataFrame()
dailyBlockHeading = dailyBlockHeading.append({'Daily Block Data':''}, ignore_index=True)
procedureHeading = pd.DataFrame()
procedureHeading = procedureHeading.append({'Procedures performed in different room':''}, ignore_index=True)
openTimeHeading = pd.DataFrame()
openTimeHeading = openTimeHeading.append({'Open Times':''}, ignore_index=True)
daily_block_data['blockDate'] = daily_block_data['blockDate'].apply(lambda x: get_procedure_date(x).date())
dailySummary = daily_block_data[(daily_block_data['blockDate'] >= date.today())]
dailySummary = dailySummary[['flexId', 'room','blockDate','startTime','endTime','releaseDate','utilization']].drop_duplicates()
for surgeon, flexId in zip(surgeonList, flexIdList):
    currentExcelRow = 0
    currentWorksheet = surgeon
    surgeonHeading.iloc[0]['Surgeon'] = surgeon
    writeDataToSheet(currentWorksheet,surgeonHeading,currentExcelRow,writer)
    currentExcelRow = currentExcelRow + 3
    curDailyData = dailySummary[dailySummary['flexId'] == flexId]
    blockDates = curDailyData['blockDate'].drop_duplicates().to_list()
    for blockDate in blockDates:
        blockDailyData = curDailyData[curDailyData['blockDate'] == blockDate]
        writeDataToSheet(currentWorksheet,blockDailyData,currentExcelRow,writer)
        currentExcelRow = 2 + currentExcelRow + blockDailyData.shape[0]
        curBlockProcData = procedures[(procedures['flexId'] == flexId) & (procedures['procDate'] == blockDate)].drop_duplicates()
        if (curBlockProcData.empty):
            continue
        writeDataToSheet(currentWorksheet,procedureHeading,currentExcelRow,writer)
        currentExcelRow = currentExcelRow + 2
        writeDataToSheet(currentWorksheet,curBlockProcData,currentExcelRow,writer)
        currentExcelRow = 2 + currentExcelRow + curBlockProcData.shape[0]
        curUnusedTimes = unused_times[(unused_times['flexId'] == flexId) & (unused_times['proc_date'] == blockDate)].drop_duplicates()
        if (curUnusedTimes.empty):
            continue
        print('cur unused times', curUnusedTimes)
        writeDataToSheet(currentWorksheet,openTimeHeading,currentExcelRow,writer)
        currentExcelRow = currentExcelRow + 2
        writeDataToSheet(currentWorksheet,curUnusedTimes,currentExcelRow,writer)
        currentExcelRow = 2 + currentExcelRow + curUnusedTimes.shape[0]
writer.save()

