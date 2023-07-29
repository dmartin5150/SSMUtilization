from blockData import get_num_frequencies
import pandas as pd;
from utilities import create_zulu_datetime_from_string, convert_zulu_to_central_time_from_date, get_date_from_datetime,cast_to_cst
from utilities import get_procedure_date,get_block_date_with_timezone


block_search_cols = [ 'candidateId', 'market', 'ministry', 'hospital', 'unit', 'room','flexId',
       'name', 'releaseDays','blockType', 'type','dow','wom1','wom2', 'wom3','wom4','wom5','start_time','end_time',
       'start_date', 'end_date','state']




def update_block_schedule(index, freq, row, block_schedule):
    cur_index = len(block_schedule)
    block_schedule.loc[cur_index,'candidateId'] = row['candidateId']
    block_schedule.loc[cur_index,'market'] = row['market']
    block_schedule.loc[cur_index,'ministry'] = row['ministry']
    block_schedule.loc[cur_index,'hospital'] = row['hospital']
    block_schedule.loc[cur_index,'unit'] = row['unit']
    block_schedule.loc[cur_index, 'blockType'] = row['type']
    block_schedule.loc[cur_index,'room'] = row['room']
    block_schedule.loc[cur_index, 'flexId'] = row['flexId']
    block_schedule.loc[cur_index,'blockName'] = row['name']
    block_schedule.loc[cur_index,'releaseDays'] = row['releaseDays']
    block_schedule.loc[cur_index,'dow'] = row[f'frequencies[{freq}].dowApplied']
    block_schedule.loc[cur_index,'wom1'] = row[f'frequencies[{freq}].weeksOfMonth[0]']
    block_schedule.loc[cur_index,'wom2'] = row[f'frequencies[{freq}].weeksOfMonth[1]']
    block_schedule.loc[cur_index,'wom3'] = row[f'frequencies[{freq}].weeksOfMonth[2]']
    block_schedule.loc[cur_index,'wom4'] = row[f'frequencies[{freq}].weeksOfMonth[3]']
    block_schedule.loc[cur_index,'wom5'] = row[f'frequencies[{freq}].weeksOfMonth[4]']
    block_schedule.loc[cur_index, 'start_time']= row[f'frequencies[{freq}].blockStartTime']
    block_schedule.loc[cur_index, 'end_time']= row[f'frequencies[{freq}].blockEndTime']
    block_schedule.loc[cur_index, 'start_date']= row[f'frequencies[{freq}].blockStartDate']
    block_schedule.loc[cur_index, 'end_date']= row[f'frequencies[{freq}].blockEndDate']
    block_schedule.loc[cur_index, 'state']= row[f'frequencies[{freq}].state']
    return block_schedule


def convert_block_datetime_strings_to_dates(block_schedule):
    block_schedule['start_date'] = block_schedule['start_date'].apply(lambda x: create_zulu_datetime_from_string(x))
    block_schedule['end_date'] = block_schedule['end_date'].apply(lambda x: create_zulu_datetime_from_string(x))
    block_schedule['start_time'] = block_schedule['start_time'].apply(lambda x: create_zulu_datetime_from_string(x))
    block_schedule['end_time'] = block_schedule['end_time'].apply(lambda x: create_zulu_datetime_from_string(x))
    return block_schedule

def convert_block_datetime_to_central_time(block_schedule):
    # print('block start time', block_schedule.iloc[0]['start_time'])
    block_schedule['start_date'] = block_schedule['start_date'].apply(lambda x: convert_zulu_to_central_time_from_date(x))
    block_schedule['end_date'] = block_schedule['end_date'].apply(lambda x: convert_zulu_to_central_time_from_date(x))
    block_schedule['start_time'] = block_schedule['start_time'].apply(lambda x: convert_zulu_to_central_time_from_date(x))
    block_schedule['end_time'] = block_schedule['end_time'].apply(lambda x: convert_zulu_to_central_time_from_date(x))
    return block_schedule

def convert_start_end_datetime_to_date_only(block_schedule):
    block_schedule['start_date'] = block_schedule['start_date'].apply(lambda x: get_date_from_datetime(x))
    block_schedule['end_date'] = block_schedule['end_date'].apply(lambda x: get_date_from_datetime(x))

# slot data has start/end times listed as zulu time, but they are actually US CST
# therefore need to cast given time as cst.  
def cast_block_datetimes_to_cst(block_schedule):
    block_schedule['start_date'] = block_schedule['start_date'].apply(lambda x: cast_to_cst(x))
    block_schedule['end_date'] = block_schedule['end_date'].apply(lambda x: cast_to_cst(x))
    block_schedule['start_time'] = block_schedule['start_time'].apply(lambda x: cast_to_cst(x))
    block_schedule['end_time'] = block_schedule['end_time'].apply(lambda x: cast_to_cst(x))


def create_block_templates(block_data, frequencies):
    block_data.reset_index(inplace=True)
    num_rows = block_data.shape[0]
    index= 0
    block_schedule = pd.DataFrame(columns=block_search_cols)
    for x in range(num_rows):
        cur_row = block_data.iloc[x]
        for freq in range (frequencies):
            if cur_row[f'frequencies[{freq}].dowApplied'] == -1:
                break
            block_schedule = update_block_schedule(index, freq, cur_row, block_schedule)
            index += 1
    convert_block_datetime_strings_to_dates(block_schedule)
    cast_block_datetimes_to_cst(block_schedule)
    convert_start_end_datetime_to_date_only(block_schedule)
    return block_schedule
    # return block_schedule[(block_schedule['state'] != 'COMPLETE')]



def get_block_templates(block_data):
    frequencies = get_num_frequencies(block_data)
    return create_block_templates(block_data,frequencies)


def get_block_templates_from_file(filename):
    block_templates = pd.read_csv("blockTemplates.csv")
    block_templates['start_date'] = block_templates['start_date'].apply(lambda x: get_procedure_date(x))
    block_templates['end_date'] = block_templates['end_date'].apply(lambda x: get_procedure_date(x))
    block_templates['start_time'] = block_templates['start_time'].apply(lambda x: get_block_date_with_timezone(x))
    block_templates['end_time'] = block_templates['end_time'].apply(lambda x: get_block_date_with_timezone(x))
    return block_templates

