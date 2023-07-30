from blockProcedures import get_all_block_procedures,get_in_room_block_procedures,get_out_room_block_procedures
from blockProcedureList import updateProcedureLists
from blockpseudoschedule import create_pseudo_schedule
from blockUsage import get_block_usage

def get_block_minutes(procedures,unit, data, block_date,room,block_stats,room_type,npis):
    pseudo_schedule = create_pseudo_schedule(procedures)
    bt_minutes, nbt_minutes, total_minutes = get_block_usage(pseudo_schedule, data['blockStartTime'], data['blockEndTime'],room_type,data['flexId'])
    if total_minutes == 0:
        utilization = '0%'
    else:
        utilization = str(round(bt_minutes/total_minutes*100,0)) +'%'
    block_stats.loc[len(block_stats.index)]=[data['flexId'],block_date,unit,room,utilization,bt_minutes, nbt_minutes, total_minutes, room_type,data['blockType'],'2023-1-1','2023-1-1',npis]

    return block_stats

def get_all_block_stats(curRow,unit, procedure_data,npis, block_date, room,block_stats,procList):
    curNpis = npis
    if len(npis) == 0:
        curNpis = '[0]'
    procedures = get_all_block_procedures(procedure_data,npis,block_date)
    procList = updateProcedureLists(curRow,unit,room, block_date, procedures.copy(),'ALL',procList)
    return get_block_minutes(procedures,unit, curRow, block_date,room,block_stats,'ALL',curNpis)

def get_in_room_block_stats(curRow,unit, procedure_data,npis, block_date, room,block_stats,procList):
    procedures = get_in_room_block_procedures(procedure_data,npis,block_date,room)
    return get_block_minutes(procedures,unit, curRow, block_date,room,block_stats,'IN',npis), procList 

def get_out_room_block_stats(curRow,unit, procedure_data,npis, block_date, room,block_stats,procList):
    procedures = get_out_room_block_procedures(procedure_data,npis,block_date,room)
    return get_block_minutes(procedures,unit, curRow, block_date,room,block_stats,'OUT',npis), procList  