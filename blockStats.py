import pandas as pd 
from utilities import get_time
from blockOwner import get_owner_npis, check_selected_npis
from blockRoomStats import get_all_block_stats, get_in_room_block_stats,get_out_room_block_stats
from padData import pad_block_data


block_stats_cols = ['id', 'blockDate','unit', 'room', 'utilization', 'bt_minutes', 'nbt_minutes','total_minutes', 'type','blockType']

def get_blocks_from_unit(block_schedule, unit):
    return block_schedule[block_schedule['unit'] == unit]


def update_block_times(data):
    data['blockStartTime'] = data.apply(lambda row: get_time(row['blockDate'], row['start_time']), axis=1)
    data['blockEndTime'] = data.apply(lambda row: get_time(row['blockDate'], row['end_time']), axis=1)
    return data


def get_block_dates (block_schedule):
    return block_schedule['blockDate'].drop_duplicates().sort_values().tolist()

def get_block_rooms (block_schedule):
    return block_schedule['room'].drop_duplicates().sort_values().tolist()






def get_block_stats(block_schedule, block_owner, procedure_data,unit,num_npis,start_date,selectAll, selectedNPIs):
    block_stats = pd.DataFrame(columns=block_stats_cols)
    
    # print('blockStats cols',block_stats.columns)
    block_data = get_blocks_from_unit(block_schedule,unit)
    block_data = update_block_times(block_data.copy())
    block_dates = get_block_dates(block_data)
    block_rooms = get_block_rooms(block_data)

    procedure_list = []
    for block_date in block_dates: 
        for room in block_rooms:
            daily_block_data = block_data[(block_data['blockDate'] == block_date) &
                                    (block_data['room'] == room)]
            for x in range(daily_block_data.shape[0]):
                curRow = daily_block_data.iloc[x]
                npis = get_owner_npis (block_owner, curRow['flexId'],num_npis)
                if selectAll: 
                    block_stats = get_all_block_stats(curRow,unit, procedure_data,npis,block_date,room,block_stats,procedure_list)
                    block_stats,procedure_list = get_in_room_block_stats(curRow,unit,procedure_data,npis,block_date,room,block_stats,procedure_list)
                    block_stats, procedure_list = get_out_room_block_stats(curRow,unit,procedure_data,npis,block_date,room,block_stats,procedure_list)
                elif check_selected_npis(npis, selectedNPIs):
                    block_stats = get_all_block_stats(curRow,unit, procedure_data,npis,block_date,room,block_stats,procedure_list)
                    block_stats,procedure_list = get_in_room_block_stats(curRow,unit,procedure_data,npis,block_date,room,block_stats,procedure_list)
                    block_stats, procedure_list = get_out_room_block_stats(curRow,unit,procedure_data,npis,block_date,room,block_stats,procedure_list)

    
    block_stats=pad_block_data(block_stats,start_date,unit)
    
    return block_stats, procedure_list