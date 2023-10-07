import pandas as pd 
from utilities import get_time,get_procedure_date,get_block_date_with_timezone
from blockOwner import get_owner_npis, check_selected_npis
from blockRoomStats import get_all_block_stats, get_in_room_block_stats,get_out_room_block_stats
from padData import pad_block_data
import pytz
from datetime import date, time,datetime, timezone;
from facilityconstants import units
from primeTimeProcedures import getPTProcedures,getEndDate
from blockSchedule import get_block_schedule,get_block_schedule_from_date
from blockFiles import write_block_json,read_block_json

block_stats_cols = ['id', 'blockDate','unit', 'room', 'utilization', 'bt_minutes', 'nbt_minutes','total_minutes', 'type','blockType','blockStartTime','blockEndTime','npis','releaseDate']

def get_blocks_from_unit(block_schedule, unit):
    return block_schedule[block_schedule['unit'] == unit]


def createtime(row):
    print(time(row['start_time'].hour, row['start_time'].minute,row['start_time'].second))
    return time(row['start_time'].hour, row['start_time'].minute,row['start_time'].second)



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
    # print('surgeon list', surgeon_list)
    return any(x in surgeon_list for x in row['npis'])


def get_filtered_block_stats(surgeon_list, block_stats,start_date, unit):
    block_stats['keep'] = block_stats.apply(lambda row: filterBlockRow(row, surgeon_list),axis=1)
    block_stats = block_stats[block_stats['keep']]
    block_stats = block_stats.drop(['keep'], axis=1)
    block_stats.reset_index(inplace=True,drop=True)
    block_stats = pad_block_data(block_stats,start_date,unit)
    flexIdData = block_stats[block_stats['room'] != 'none']
    flexIds = flexIdData['id'].drop_duplicates()
    # print('flexIds', flexIds)
    # flexIds = [b for b in flexIds if not isinstance(b, float)]
    return block_stats, flexIds




def get_block_dates (block_schedule):
    return block_schedule['blockDate'].drop_duplicates().sort_values().tolist()

def get_block_rooms (block_schedule):
    return block_schedule['room'].drop_duplicates().sort_values().tolist()


def get_block_report_hours(data):
    block_report_hours = [{'id':str(row.id), 'blockDate':row.blockDate.strftime("%Y-%m-%d"),'unit':row.unit,
                                    'room':row.room, 'utilization':row.utilization,'bt_minutes':str(row.bt_minutes),
                                    'nbt_minutes':str(row.nbt_minutes),'total_minutes':str(row.total_minutes),
                                    'type':row.type,'blockType':str(row.blockType)} for index, row in data.iterrows()] 
    print('block report hours', block_report_hours)
    return block_report_hours



def get_block_stats(block_schedule, block_owner, procedure_data,unit,num_npis,start_date,selectAll, selectedNPIs):
    block_stats = pd.DataFrame(columns=block_stats_cols)
    

    # print('getting data')
    print('block schedule', block_schedule)
    block_data = get_blocks_from_unit(block_schedule,unit)
    print('block data update', block_data)
    block_data = update_block_times(block_data.copy())
    block_dates = get_block_dates(block_data)
    block_rooms = get_block_rooms(block_data)
    # print('got data')
    
    procedure_list = []
    for block_date in block_dates: 
        for room in block_rooms:
            daily_block_data = block_data[(block_data['blockDate'] == block_date) &
                                    (block_data['room'] == room)]
            # print('daily block data', daily_block_data.columns)
            for x in range(daily_block_data.shape[0]):
                curRow = daily_block_data.iloc[x]
                npis = get_owner_npis (block_owner, curRow['flexId'],num_npis)
                releaseDate = curRow['releaseDate']
                # if selectAll: 
                block_stats = get_all_block_stats(curRow,unit, procedure_data,npis,block_date,room,block_stats,procedure_list,releaseDate)
                block_stats,procedure_list = get_in_room_block_stats(curRow,unit,procedure_data,npis,block_date,room,block_stats,procedure_list,releaseDate)
                block_stats, procedure_list = get_out_room_block_stats(curRow,unit,procedure_data,npis,block_date,room,block_stats,procedure_list,releaseDate)
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

block_id_owner_cols = ['id','blockType','npis']

def remove_brackets(x):
    # print(x['id'], x['npis'], type(x['npis']))
    if (isinstance(x['npis'],str)):
        return 0
    elif (len(x['npis']) == 0):
        print(1)
        return 1
    else:
        curVal=  x['npis'][0]
        print('cur val', curVal)
        return curVal


def combine_with_surgeons(block_id_owners):
    surgeons = pd.read_csv('Surgeons.csv')
    block_id_owners = block_id_owners.merge(surgeons, how='left', left_on='npis', right_on='npi')
    return block_id_owners                    


def clean_up_block_id_owners(block_id_owners):
    block_id_owners.drop_duplicates(subset='id', inplace=True)
    block_id_owners = block_id_owners[block_id_owners['blockType'] == 'Surgeon']
    block_id_owners['npis'] = block_id_owners.apply(lambda row: remove_brackets(row), axis=1)
    return block_id_owners

def get_cum_block_stats_and_procs(startDate,endDate,block_owner, dataFrameLookup,block_no_release,num_npis):
    cum_block_stats = {}
    cum_block_procs = {}
    block_id_owners = pd.DataFrame(columns=block_id_owner_cols)
    print('block no release ', block_no_release)
    for unit in units:
        curStartDate = startDate
        print('unit', unit)
        curEndDate = getEndDate(startDate)
        for x in range (startDate.month, endDate.month):
            # print('dataframe', dataFrameLookup[unit])
            procedures = getPTProcedures(curStartDate,dataFrameLookup[unit])
            # print('unit',unit,  procedures.shape)
            cur_block_schedule = get_block_schedule_from_date(curStartDate, curEndDate, block_no_release,unit)
            print('blockschedule', cur_block_schedule.shape, curStartDate, curEndDate)
            print('block no release', block_no_release[block_no_release['unit'] == 'BH CSC'])
            block_stats,newProcList = get_block_stats(cur_block_schedule,block_owner,procedures, unit,num_npis,curStartDate,True,[])
            cum_block_stats.update({f"{curStartDate.month}_{curStartDate.year}_{unit}":block_stats})
            cum_block_procs.update({f"{curStartDate.month}_{curStartDate.year}_{unit}":newProcList})
            block_stats.to_csv(f"{curStartDate.month}_{curStartDate.year}_{unit}.csv",index=False)
            new_blocks = block_stats[['id','blockType','npis']]
            block_id_owners = pd.concat([new_blocks,block_id_owners])
            write_block_json(newProcList, f"{curStartDate.month}_{curStartDate.year}_{unit}.txt")
            next_month = get_next_month(curStartDate.month)
            next_year = get_next_year(curStartDate.month,curStartDate.year)
            string_date = f"{next_year}-{next_month}-1"
            curStartDate = get_procedure_date(string_date).date()
            curEndDate = getEndDate(curStartDate)
    block_id_owners = clean_up_block_id_owners(block_id_owners)
    block_id_owners = combine_with_surgeons(block_id_owners)
    print('block id owners', block_id_owners)
    block_id_owners.to_csv('block_id_owners.csv')
    return cum_block_stats, cum_block_procs, block_id_owners


def get_block_id_owner_from_file():
    return pd.read_csv('block_id_owners.csv')

def update_block_dates_from_file(df):
    df['blockDate'] = df['blockDate'].apply(lambda x: get_procedure_date(x))
    df['blockDate'] = df['blockDate'].apply(lambda x: x.date())
    df['blockStartTime'] = df['blockStartTime'].apply(lambda x: get_block_date_with_timezone(x))
    df['blockEndTime'] = df['blockEndTime'].apply(lambda x: get_block_date_with_timezone(x))
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


def get_block_stats_procs_from_file(startDate,endDate):
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

def add_block_date(block_stats):
    # block_stats['blockDate'] = block_stats['blockDate'].apply(lambda x: x.date())
    block_stats['weekday'] = block_stats['blockDate'].apply(lambda x: x.isoweekday())
    # print('dates',block_stats['weekday'])
    return block_stats


# def addWeekdays(block_stats):
#     block_stats = add_block_date(block_stats)
#     block_stats['weekday'] = block_stats['blockProcedureDate'].apply(lambda x: x.isoweekday())
#     print('block weekday', block_stats['blockProcedureDate'])
#     block_stats = block_stats.drop(['blockProcedureDate'], axis=1)
#     block_stats.reset_index(inplace=True,drop=True)
#     return block_stats



def get_block_filtered_by_date(curStartDate, curEndDate, block_stats,selectAll):
    # print('start date type', curStartDate)
    # print('enddate', curEndDate)
    print('block date', block_stats.iloc[0]['blockDate'], type(block_stats.iloc[0]['blockDate']))
    if selectAll:
        block_stats = add_block_date(block_stats)

    block_stats['weekday'] = block_stats['blockDate'].apply(lambda x: x.isoweekday())
    block_stats = block_stats[(block_stats['blockDate'] >= curStartDate) & (block_stats['blockDate'] <= curEndDate)]
    return block_stats
    # return block_stats[(block_stats['blockDate'] >= curStartDate) & (block_stats['blockDate'] <= curEndDate)]



def formatBlockSubHeaders(title,minutes):
       h, m = divmod(minutes, 60)
       return title + ' {:d}H {:02d}M'.format(int(h), int(m))


bt_total_cols = ['date', 'dayOfWeek', 'display','nonPTMinutes', 'ptMinutes', 'subHeading1', 'subHeading2','type','class']




def get_block_summary(block_data,bt_totals, room_type,block_type):
    block_data = block_data[(block_data['type'] == room_type) & (block_data['blockType'] == block_type)]
    # print('block Data', block_data)
    # bt_totals= pd.DataFrame(columns=bt_total_cols)
    # block_data = addWeekdays(block_data)
    for i in range(5):
        total_minutes=0
        ptMinutes = 0
        nonptMinutes = 0
        curData = block_data[block_data['weekday'] == (i + 1)]
        # print('curdata', curData)
        total_minutes = curData['total_minutes'].sum()
        title = 'Block Totals'
        dayOfWeek = i + 1
        ptMinutes = curData['bt_minutes'].sum()
        nonptMinutes = curData['nbt_minutes'].sum()
        subHeading1 = formatBlockSubHeaders('BT: ',ptMinutes)
        subHeading2 = formatBlockSubHeaders('nBT: ',nonptMinutes)
        if total_minutes == 0:
            display = 'None'
        else:
            display = str(int(round(ptMinutes/total_minutes*100,0))) +'%'
        row_to_append = pd.DataFrame([{'date':title,'dayOfWeek':dayOfWeek,'ptMinutes': ptMinutes,'nonPTMinutes':nonptMinutes,
                            'subHeading1':subHeading1,'subHeading2':subHeading2,'display':display,'type':room_type,'className':block_type}])
        bt_totals = pd.concat([bt_totals,row_to_append])
        # bt_totals = bt_totals.append({'date':title,'dayOfWeek':dayOfWeek,'ptMinutes': ptMinutes,'nonPTMinutes':nonptMinutes,
        #                     'subHeading1':subHeading1,'subHeading2':subHeading2,'display':display,'type':room_type,'className':block_type},ignore_index=True)
        
    # unit_bt_totals= [{'date': 'Summary', 'dayOfWeek': row.dayOfWeek,'ptMinutes': str(row.ptMinutes), 
    #                           'notPTMinutes': row.nonPTMinutes, 'subHeading1': row.subHeading1,'subHeading2':row.subHeading2, 'display': row.display }
    #                       for index, row in bt_totals.iterrows()] 
    return bt_totals
    
def create_block_summary(block_data):
    # block_data = block_data[block_data['type'] == 'ALL']
    bt_totals= pd.DataFrame(columns=bt_total_cols)

    bt_totals = get_block_summary(block_data,bt_totals, 'ALL','Surgeon')
    bt_totals = get_block_summary(block_data,bt_totals, 'IN','Surgeon')
    bt_totals = get_block_summary(block_data,bt_totals, 'OUT','Surgeon')
    bt_totals = get_block_summary(block_data,bt_totals, 'ALL','Surgeon Group')
    bt_totals = get_block_summary(block_data,bt_totals, 'IN','Surgeon Group')
    bt_totals = get_block_summary(block_data,bt_totals, 'OUT','Surgeon Group')
    # print(bt_totals)
    unit_bt_totals= [{'date': 'Summary', 'dayOfWeek': row.dayOfWeek,'ptMinutes': str(row.ptMinutes), 
                              'notPTMinutes': row.nonPTMinutes, 'subHeading1': row.subHeading1,'subHeading2':row.subHeading2, 'display': row.display,'type':row.type,'class':row.className }
                          for index, row in bt_totals.iterrows()] 
    return unit_bt_totals


def get_cum_block_stats_with_dates(curStartDate,curEndDate,unit, cum_block_stats):
    block_stats = pd.DataFrame()
    startMonth = curStartDate.month
    endMonth = curEndDate.month + 1
    # print('start month', startMonth, curStartDate)
    # print('end month', endMonth,curEndDate)
    for i in range(startMonth, endMonth):
        block_data_string = f"{i}_{curStartDate.year}_{unit}"
        # print('block_data_string',block_data_string)
        block_stats = pd.concat([block_stats, cum_block_stats[block_data_string]])
    #     print('block_stats', block_stats)
    # print('block_stats', block_stats)
    return block_stats
        