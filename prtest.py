import pandas as pd
from unitData2 import get_unit_data_from_file
from utilities import get_procedure_date,get_text_of_time
from datetime import date
import datetime
from openpyxl import load_workbook

writer = pd.ExcelWriter('kyzer.xlsx')
kyzerDates = []
today = date.today()
kyzerDuration = pd.DataFrame()
print(today)
CSCData = get_unit_data_from_file('csc_gen_data.csv')

kyzer = CSCData[(CSCData['NPI'] == 1669448593) & (CSCData['procedureDtNoTime'] >= today)]
openTimes = pd.read_csv('opentime.csv')
cscOpenTimes = openTimes[(openTimes['unit'] == 'BH CSC') & (openTimes['open_type'] == 'OPEN')]
cscSoftTimes = openTimes[(openTimes['unit'] == 'BH CSC') & (openTimes['open_type'] == 'SOFT')]
cscOpenTimes['proc_date'] = cscOpenTimes['proc_date'].apply(lambda x: get_procedure_date(x).date())
cscOpenTimes['dow'] = cscOpenTimes['proc_date'].apply(lambda x: x.isoweekday())
cscSoftTimes['proc_date'] = cscSoftTimes['proc_date'].apply(lambda x: get_procedure_date(x).date())
cscSoftTimes['dow'] = cscSoftTimes['proc_date'].apply(lambda x: x.isoweekday())
kyzerDates = kyzer['procedureDtNoTime'].drop_duplicates().to_list()
kyzerDuration = kyzer.copy()
kyzerDuration['duration'] = kyzer.apply(lambda row: row['local_end_time'] - row['local_start_time'], axis=1)
kyzerDuration['duration'] = kyzerDuration['duration'].apply(lambda x: x.total_seconds()/60)
kyzerAveDuration =75
kyzerOpenTimes = cscOpenTimes[(cscOpenTimes['proc_date'].isin(kyzerDates))]
kyzerSoftTimes = cscSoftTimes[(cscSoftTimes['proc_date'].isin(kyzerDates))]
kyzerOpenTimes = kyzerOpenTimes[kyzerOpenTimes['unused_block_minutes'] >= kyzerAveDuration]
cscOpenWednesdays = cscOpenTimes[(cscOpenTimes['dow'] == 3) & (cscOpenTimes['proc_date'] > today) & (cscOpenTimes['unused_block_minutes'] >= kyzerAveDuration)]
cscSoftWednesdays = cscSoftTimes[(cscSoftTimes['dow'] == 3) & (cscSoftTimes['proc_date'] > today) & (cscSoftTimes['unused_block_minutes'] >= kyzerAveDuration)]


print('start time', kyzerOpenTimes['local_start_time'])


def convertdfColumnToString(df, columnName):
    df[columnName] = df[columnName].apply(lambda x: str(x))
    return df

def convertDatesToString(curProcs):
    curProcs = convertdfColumnToString(curProcs,'procedureDtNoTime')
    curProcs['local_start_time'] = curProcs['local_start_time'].apply(lambda x: get_text_of_time(x))
    curProcs['local_end_time'] = curProcs['local_end_time'].apply(lambda x: get_text_of_time(x))
    return curProcs

def convertOpenDatesToString(curProcs):
    curProcs = convertdfColumnToString(curProcs,'proc_date')
    return curProcs

curRow=0
firstPass = True
openHeading = pd.DataFrame([{'OPEN TIMES': ''}])
softHeading = pd.DataFrame([{'SOFT BlOCKS': ''}])
proceduresHeading = pd.DataFrame([{'Scheduled Procedures': ''}])
mainHeading = pd.DataFrame([{'Unit':'', 'Room':'','Procedure Name':'','Procedure Date':'','Start Time':'','End Time':''}])
for curDate in kyzerDates:
    if (firstPass):
        mainHeading.to_excel(writer, 'procedures',startrow=curRow, index=False, header=True) 
    curProcs = kyzer[kyzer['procedureDtNoTime'] == curDate][['unit','room','procedureName','procedureDtNoTime','local_start_time','local_end_time']]
    curProcs = convertDatesToString(curProcs)
    curRow += 2
    proceduresHeading.to_excel(writer, 'procedures',startrow=curRow +1, index=False, header=True)
    curRow += 2
    curProcs.to_excel(writer, 'procedures',startrow=curRow +1, index=False, header=False)
    firstPass = False
    curOpenTimes = kyzerOpenTimes[kyzerOpenTimes['proc_date'] == curDate][['unit','room','open_type','proc_date','local_start_time','local_end_time']]
    curOpenTimes = convertOpenDatesToString(curOpenTimes)
    curRow += curProcs.shape[0] + 1
    print('row', curRow)
    if (curOpenTimes.shape[0] > 0):
        openHeading.to_excel(writer,'procedures', startrow=curRow + 2, index=False, header=True)
        curRow += 2
        curOpenTimes.to_excel(writer,'procedures', startrow=curRow + 2, index=False, header=False)
        curRow += curOpenTimes.shape[0]
    

    curSoftTimes = kyzerSoftTimes[kyzerSoftTimes['proc_date'] == curDate][['unit','room','open_type','proc_date','local_start_time','local_end_time']]
    curSoftTimes = convertOpenDatesToString(curSoftTimes)
    curRow += curProcs.shape[0] + 1
    print('row', curRow)
    if (curSoftTimes.shape[0] >0):
        softHeading.to_excel(writer,'procedures', startrow=curRow + 2, index=False, header=True)
        curRow += 2
        curSoftTimes.to_excel(writer,'procedures', startrow=curRow + 2, index=False, header=False)
        curRow += curSoftTimes.shape[0]



openWedHeading = pd.DataFrame([{'Unit':'', 'Room':'','Procedure Name':'','Procedure Date':'','Start Time':'','End Time':'','Duration':''}])

openHeading.to_excel(writer,'Open Wednesday Times', startrow=1, index=False, header=True)
filteredWednesdays = cscOpenWednesdays[['unit','room','open_type','proc_date','local_start_time','local_end_time','formatted_minutes']].sort_values(by=['proc_date','room'])
openWedDates = filteredWednesdays['proc_date'].drop_duplicates().to_list()
curRow = 3
curDatedf = pd.DataFrame([{'Date':''}])
for wedDate in openWedDates:
    curDatedf.iloc[0]['Date'] = wedDate
    curDatedf.to_excel(writer,'Open Wednesday Times', startrow=curRow, index=False, header=False)
    curRow += 2
    curWednesday = filteredWednesdays[filteredWednesdays['proc_date'] == wedDate]
    curWednesday.to_excel(writer,'Open Wednesday Times', startrow=curRow, index=False, header=False)
    curRow += curWednesday.shape[0] + 1


softHeading.to_excel(writer,'Soft Block Wednesday Times', startrow=1, index=False, header=True)
filteredSoftWednesdays = cscSoftWednesdays[['unit','room','open_type','proc_date','local_start_time','local_end_time','formatted_minutes']].sort_values(by=['proc_date','room'])
softWedDates = filteredSoftWednesdays['proc_date'].drop_duplicates().to_list()
curRow = 3
curDatedf = pd.DataFrame([{'Date':''}])
for wedDate in softWedDates:
    curDatedf.iloc[0]['Date'] = wedDate
    curDatedf.to_excel(writer,'Soft Block Wednesday Times', startrow=curRow, index=False, header=False)
    curRow += 2
    curWednesday = filteredSoftWednesdays[filteredSoftWednesdays['proc_date'] == wedDate]
    curWednesday.to_excel(writer,'Soft Block Wednesday Times', startrow=curRow, index=False, header=False)
    curRow += curWednesday.shape[0] + 1


writer.close()
