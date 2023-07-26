import pandas as pd 
from utilities import get_time
from blockOwner import get_owner_npis, check_selected_npis
from blockRoomStats import get_all_block_stats, get_in_room_block_stats,get_out_room_block_stats
from padData import pad_block_data
import pytz
from datetime import date, time,datetime, timezone;


block_stats_cols = ['id', 'blockDate','unit', 'room', 'utilization', 'bt_minutes', 'nbt_minutes','total_minutes', 'type','blockType','blockStartTime','blockEndTime','npis']

def get_blocks_from_unit(block_schedule, unit):
    return block_schedule[block_schedule['unit'] == unit]






def update_block_times(data):
    # print('blockstarttime','date', type(data.iloc[0]['blockDate']),'time', data.iloc[0]['end_time'])
    timezone = pytz.timezone("US/Central")
    data['blockStartTime'] = data.apply(lambda row: timezone.localize(datetime.combine(date(row['blockDate'].year, row['blockDate'].month, row['blockDate'].day), 
                          time(row['start_time'].hour, row['start_time'].minute,row['start_time'].second))), axis=1)
    
    data['blockEndTime'] = data.apply(lambda row: timezone.localize(datetime.combine(date(row['blockDate'].year, row['blockDate'].month, row['blockDate'].day), 
                          time(row['end_time'].hour, row['end_time'].minute,row['end_time'].second))),axis=1)
    print('after', data.iloc[0]['blockEndTime'])
    return data



# def update_block_times(data):
#     print('blockstarttime','date', type(data.iloc[0]['blockDate']),'time', data.iloc[0]['start_time'])
#     data['blockStartTime'] = data.apply(lambda row: get_time(row['blockDate'], row['start_time']), axis=1)
#     data['blockEndTime'] = data.apply(lambda row: get_time(row['blockDate'], row['end_time']), axis=1)
#     return data

def filterBlockRow(row, surgeon_list):
    return any(x in surgeon_list for x in row['npis'])


def get_filtered_block_stats(surgeon_list, block_stats,start_date, unit):
    block_stats['keep'] = block_stats.apply(lambda row: filterBlockRow(row, surgeon_list),axis=1)
    block_stats = block_stats[block_stats['keep']]
    block_stats.drop(['keep'], axis=1, inplace=True)
    print('block stats pre', block_stats)
    block_stats = pad_block_data(block_stats,start_date,unit)
    return block_stats




def get_block_dates (block_schedule):
    return block_schedule['blockDate'].drop_duplicates().sort_values().tolist()

def get_block_rooms (block_schedule):
    return block_schedule['room'].drop_duplicates().sort_values().tolist()


def get_block_report_hours(data):
    block_report_hours = [{'id':str(row.id), 'blockDate':row.blockDate.strftime("%Y-%m-%d"),'unit':row.unit,
                                    'room':row.room, 'utilization':row.utilization,'bt_minutes':str(row.bt_minutes),
                                    'nbt_minutes':str(row.nbt_minutes),'total_minutes':str(row.total_minutes),
                                    'type':row.type,'blockType':row.blockType} for index, row in data.iterrows()] 
    return block_report_hours



def get_block_stats(block_schedule, block_owner, procedure_data,unit,num_npis,start_date,selectAll, selectedNPIs):
    block_stats = pd.DataFrame(columns=block_stats_cols)
    

    print('getting data')
    block_data = get_blocks_from_unit(block_schedule,unit)
    block_data = update_block_times(block_data.copy())
    block_dates = get_block_dates(block_data)
    block_rooms = get_block_rooms(block_data)
    print('got data')
    
    procedure_list = []
    for block_date in block_dates: 
        for room in block_rooms:
            daily_block_data = block_data[(block_data['blockDate'] == block_date) &
                                    (block_data['room'] == room)]
            for x in range(daily_block_data.shape[0]):
                curRow = daily_block_data.iloc[x]
                npis = get_owner_npis (block_owner, curRow['flexId'],num_npis)
                # if selectAll: 
                block_stats = get_all_block_stats(curRow,unit, procedure_data,npis,block_date,room,block_stats,procedure_list)
                block_stats,procedure_list = get_in_room_block_stats(curRow,unit,procedure_data,npis,block_date,room,block_stats,procedure_list)
                block_stats, procedure_list = get_out_room_block_stats(curRow,unit,procedure_data,npis,block_date,room,block_stats,procedure_list)
                # elif check_selected_npis(npis, selectedNPIs):
                #     block_stats = get_all_block_stats(curRow,unit, procedure_data,npis,block_date,room,block_stats,procedure_list)
                #     block_stats,procedure_list = get_in_room_block_stats(curRow,unit,procedure_data,npis,block_date,room,block_stats,procedure_list)
                #     block_stats, procedure_list = get_out_room_block_stats(curRow,unit,procedure_data,npis,block_date,room,block_stats,procedure_list)

    
    block_stats=pad_block_data(block_stats,start_date,unit)
    
    return block_stats, procedure_list