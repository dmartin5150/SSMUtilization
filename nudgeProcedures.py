from unitData2 import get_unit_data_from_file
import pandas as pd 
from datetime import date
from utilities import get_procedure_date

jriData = get_unit_data_from_file('jri_gen_data.csv')
STMSTORData  = get_unit_data_from_file('stm_gen_data.csv')
MTORData = get_unit_data_from_file('mt_gen_data.csv')
CSCData = get_unit_data_from_file('csc_gen_data.csv')
STORData = get_unit_data_from_file('stor_gen_data.csv')
dataFrameLookup = {'BH JRI': jriData, 'STM ST OR': STMSTORData, 'MT OR': MTORData, 'BH CSC': CSCData, 'ST OR':STORData}


def getNudgeProcedureData(curRow,curDate, unit, nudgeProcedures):


    procedureList = dataFrameLookup[unit]
    curNpi = curRow['npi']
    curRoom = curRow['room']
    curProcedures = procedureList[(procedureList['NPI'] == curNpi) & (procedureList['procedureDate'] == curDate) &
                                  (procedureList['room'] != curRoom)]
    if not curProcedures.empty:
        for x in range(curProcedures.shape[0]):
            curProc = curProcedures.iloc[x]
            nudgeProcedures = nudgeProcedures.append({'flexId':curRow['flexId'],'unit':unit,'procDate':curDate,'block room': curRoom, 'proc room': curProc['room'],'startTime':str(curProc['startTime']),'endTime':str(curProc['endTime']), 'fullName':curProc['fullName']}, ignore_index=True)
    return nudgeProcedures


def getNudgeProcedures(units, nudgeBlocks):
    nudgeProcedures = pd.DataFrame()
    blockDates = nudgeBlocks['blockDate'].to_list()
    print('')
    for curDate in blockDates:
        curBlocks = nudgeBlocks[(nudgeBlocks['blockDate'] == curDate)]
        for x in range(curBlocks.shape[0]):
            for unit in units: 
                # print('in unit', unit, curDate)
                curRow = curBlocks.iloc[x]
                nudgeProcedures = getNudgeProcedureData(curRow,curDate, unit, nudgeProcedures)
    nudgeProcedures['procDate'] = nudgeProcedures['procDate'].apply(lambda x: get_procedure_date(x).date())
    nudgeProcedures = nudgeProcedures[nudgeProcedures['procDate']>= date.today()]
    nudgeProcedures['procDate'] = nudgeProcedures['procDate'].apply(lambda x: str(x))
    return nudgeProcedures



