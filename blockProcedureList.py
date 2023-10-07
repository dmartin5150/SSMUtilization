import pandas as pd
from utilities import formatProcedureTimes,get_block_date_with_time,get_procedure_date
from datetime import date;


def updateProcedureLists(curRow,unit,room, block_date, procedures,roomType,procList):
        procedures['procedureDtNoTime']= procedures['procedureDtNoTime'].apply(lambda x: x.strftime("%Y-%m-%d"))
        procedures['local_start_time']= procedures['local_start_time'].apply(lambda x: formatProcedureTimes(x))
        procedures['local_end_time']=procedures['local_end_time'].apply(lambda x: formatProcedureTimes(x))
        localProcList =[]
        bt='ALL'
        weekday = block_date.isoweekday()
        for x in range(procedures.shape[0]):
            procedureRow = procedures.iloc[x]
            if(room == procedureRow.room):
                bt = 'IN'
            else: 
                bt = 'OUT'
            curProcedure = {'fullName':procedureRow.fullName, 'procedureDtNoTime':procedureRow.procedureDtNoTime,
                       'unit':procedureRow.unit, 'procedureName':procedureRow.procedureName,'NPI': str(procedureRow.NPI),
                       'local_start_time':procedureRow.local_start_time, 'local_end_time':procedureRow.local_end_time,
                       'room':procedureRow.room, 'type':bt}
            localProcList.append(curProcedure)
        blockObj ={'blockId': str(curRow['flexId']), 'blockName':curRow['blockName'], 'room':room,'unit':unit,
                   'weekday':weekday, 'blockDate':block_date.strftime("%Y-%m-%d"), 'type': bt, 'procs':localProcList,'blockType': curRow['blockType'],
                   'start_time':str(formatProcedureTimes(curRow['start_time'])),'end_time':str(formatProcedureTimes(curRow['end_time'])),
                   'blockName':curRow['blockName'],
                    'releaseDate':date.strftime(curRow['releaseDate'],"%m-%d-%Y") }

        procList.append(blockObj)
        return procList


def get_filtered_proc_list(flexIds, start_date, end_date, procList):
    filtered_list = []
    # print('start date', start_date)
    # print('end date', end_date)
    # print('proc list', procList)
    # print('flexIds', flexIds)
    for flexId in flexIds: 
        curList = [x for x in procList if ((x['blockId'] == str(int(flexId))) & (get_procedure_date(x['blockDate']).date()>= start_date) &
                                           (get_procedure_date(x['blockDate']).date() < end_date))] 
        # print('curList', curList)
        filtered_list.extend(curList)
    # print('filtered list', filtered_list)
    return filtered_list
        