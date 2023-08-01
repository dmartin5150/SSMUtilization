import pandas as pd 
from utilities import get_time,get_procedure_date
from blockOwner import get_owner_npis, check_selected_npis
from blockRoomStats import get_all_block_stats, get_in_room_block_stats,get_out_room_block_stats
from padData import pad_block_data
import pytz
from datetime import date, time,datetime, timezone;
from facilityconstants import units
from primeTimeProcedures import getPTProcedures,getEndDate
from blockSchedule import get_block_schedule,get_block_schedule_from_date
from blockFiles import write_block_json,read_block_json

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
    # print('after', data.iloc[0]['blockEndTime'])
    return data



# def update_block_times(data):
#     print('blockstarttime','date', type(data.iloc[0]['blockDate']),'time', data.iloc[0]['start_time'])
#     data['blockStartTime'] = data.apply(lambda row: get_time(row['blockDate'], row['start_time']), axis=1)
#     data['blockEndTime'] = data.apply(lambda row: get_time(row['blockDate'], row['end_time']), axis=1)
#     return data

def filterBlockRow(row, surgeon_list):
    return any(x in surgeon_list for x in row['npis'])


def get_filtered_block_stats(surgeon_list, block_stats,start_date, unit):
    # print('unique', block_stats['npis'].drop_duplicates())
    block_stats['keep'] = block_stats.apply(lambda row: filterBlockRow(row, surgeon_list),axis=1)
    # print('filtered block stats 2', block_stats)
    block_stats = block_stats[block_stats['keep']]
    # print('filtered block stats 3', block_stats)
    block_stats = block_stats.drop(['keep'], axis=1)
    # print('filtered block stats 4', block_stats)
    block_stats.reset_index(inplace=True,drop=True)
    # print('filtered block stats', block_stats)
    block_stats = pad_block_data(block_stats,start_date,unit)
    flexIds = block_stats['id'].drop_duplicates()
    flexIds = [b for b in flexIds if not isinstance(b, float)]
    return block_stats, flexIds




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
    

    # print('getting data')
    block_data = get_blocks_from_unit(block_schedule,unit)
    block_data = update_block_times(block_data.copy())
    block_dates = get_block_dates(block_data)
    block_rooms = get_block_rooms(block_data)
    # print('got data')
    
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





def get_next_month(curMonth):
    if (curMonth != 12):
        return curMonth + 1
    else:
        return 1
    
def get_next_year(curMonth, curYear):
    if (curMonth != 12):
        return curYear
    else:
        return curYear + 1

def get_cum_block_stats_and_procs(startDate,endDate,block_owner, dataFrameLookup,block_no_release,num_npis):
    cum_block_stats = {}
    cum_block_procs = {}
    for unit in units:
        curStartDate = startDate
        curEndDate = getEndDate(startDate)
        for x in range (startDate.month, endDate.month):
            procedures = getPTProcedures(curStartDate,dataFrameLookup[unit])
            cur_block_schedule = get_block_schedule_from_date(curStartDate, curEndDate, block_no_release,unit)
            block_stats,newProcList = get_block_stats(cur_block_schedule,block_owner,procedures, unit,num_npis,curStartDate,True,[])
            cum_block_stats.update({f"{curStartDate.month}_{curStartDate.year}_{unit}":block_stats})
            cum_block_procs.update({f"{curStartDate.month}_{curStartDate.year}_{unit}":newProcList})
            block_stats.to_csv(f"{curStartDate.month}_{curStartDate.year}_{unit}.csv",index=False)
            write_block_json(newProcList, f"{curStartDate.month}_{curStartDate.year}_{unit}.txt")
            next_month = get_next_month(curStartDate.month)
            next_year = get_next_year(curStartDate.month,curStartDate.year)
            string_date = f"{next_year}-{next_month}-1"
            curStartDate = get_procedure_date(string_date).date()
            curEndDate = getEndDate(curStartDate)
    return cum_block_stats, cum_block_procs


def update_block_dates_from_file(df):
    df['blockDate'] = df['blockDate'].apply(lambda x: get_procedure_date(x))
    df['blockStartTime'] = df['blockStartTime'].apply(lambda x: get_procedure_date(x))
    df['blockEndTime'] = df['blockEndTime'].apply(lambda x: get_procedure_date(x))
    # print(df.dtypes)
    return df

def convert_npis_to_int_from_file(npis):
    if npis[0] == '':
        return '[0]'
    else:
        return [int(i) for i in npis]

    

def update_npi_list_from_file(df):
    df['npis'] = df['npis'].apply(lambda x: x.strip('][').split(','))
    df['npis'] = df['npis'].apply(lambda x: convert_npis_to_int_from_file(x))
    return df


def get_block_stats_props_from_file(startDate,endDate):
    cum_block_stats = {}
    cum_block_procs = {}
    for unit in units:
        curStartDate = startDate
        for x in range (startDate.month, endDate.month):
            cum_block_stats.update({f"{curStartDate.month}_{curStartDate.year}_{unit}":pd.read_csv(f"{curStartDate.month}_{curStartDate.year}_{unit}.csv")})
            cum_block_stats[f"{curStartDate.month}_{curStartDate.year}_{unit}"] = update_block_dates_from_file(cum_block_stats[f"{curStartDate.month}_{curStartDate.year}_{unit}"]) 
            cum_block_stats[f"{curStartDate.month}_{curStartDate.year}_{unit}"] = update_npi_list_from_file(cum_block_stats[f"{curStartDate.month}_{curStartDate.year}_{unit}"])
            cum_block_procs.update({f"{curStartDate.month}_{curStartDate.year}_{unit}":read_block_json(f"{curStartDate.month}_{curStartDate.year}_{unit}.txt")})
            next_month = get_next_month(curStartDate.month)
            next_year = get_next_year(curStartDate.month,curStartDate.year)
            string_date = f"{next_year}-{next_month}-1"
            curStartDate = get_procedure_date(string_date).date()
    return cum_block_stats, cum_block_procs