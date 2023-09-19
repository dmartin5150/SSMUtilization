import pandas as pd
from utilities import get_procedure_date
import datetime





def get_unused_block():
    open_times = pd.read_csv('opentime.csv')
    open_times = open_times[(open_times['open_type'] == 'BLOCK')]
    open_times['proc_date'] = open_times['proc_date'].apply(lambda x: get_procedure_date(x).date())
    return open_times

flexIds = [663019,675009]
months = [8,9]

def check_block_id(block_id, flexIds):
    if(block_id in flexIds):
        return block_id
    return -1



def get_start_end_dates(months):
    start_month = int(months[0])
    start_dom = 1
    today = datetime.date.today()
    start_year = today.year 
    start_date = get_procedure_date(f'{start_year}-{start_month}-{start_dom}').date()
    end_month = int(months[-1]) + 1
    end_dom = 1
    if (end_month == 12):
        end_year = start_year + 1
    else:
        end_year = start_year
    end_date = get_procedure_date(f'{end_year}-{end_month}-{end_dom}').date()
    return start_date, end_date




def get_monthly_unused_block(flexIds,months):
    unused_block = get_unused_block()
    unused_block['flexId'] = unused_block.apply(lambda row: check_block_id(row['block_id'],flexIds), axis=1)
    start_date, end_date = get_start_end_dates(months)
    unused_block = unused_block[unused_block['flexId'] != -1].sort_values(by=['block_id','proc_date' ])
    unused_block = unused_block[(unused_block['proc_date']>= start_date) & (unused_block['proc_date'] < end_date)]
    return unused_block.sort_values(by=['block_id','proc_date','unused_block_minutes'])

get_monthly_unused_block(flexIds,months)




def getSurgeonList(monthly_block_data):
    block_owners = pd.read_csv('block_id_owners.csv')
    flexIds = block_owners['id'].to_list()
    monthly_block_data['filtered'] = monthly_block_data.apply(lambda row:row['flexId'] in flexIds, axis=1)
    surgeon_list = monthly_block_data[monthly_block_data['filtered'] == True]['fullName'].drop_duplicates().to_list()
    flexId_list = monthly_block_data[monthly_block_data['filtered'] == True]['flexId'].drop_duplicates().to_list()
    return surgeon_list, flexId_list

    