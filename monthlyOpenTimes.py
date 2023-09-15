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
    return block_id in flexIds



def get_start_end_dates(months):
    start_month = months[0]
    start_dom = 1
    today = datetime.date.today()
    start_year = today.year 
    start_date = get_procedure_date(f'{start_year}-{start_month}-{start_dom}').date()
    end_month = months[-1] + 1
    end_dom = 1
    if (end_month == 12):
        end_year = start_year + 1
    else:
        end_year = start_year
    end_date = get_procedure_date(f'{end_year}-{end_month}-{end_dom}').date()
    return start_date, end_date




def get_monthly_unused_block(flexIds,months):
    unused_block = get_unused_block()
    unused_block['filtered'] = unused_block.apply(lambda row: check_block_id(row['block_id'],flexIds), axis=1)
    start_date, end_date = get_start_end_dates(months)
    unused_block = unused_block[unused_block['filtered'] == True].sort_values(by=['block_id','proc_date' ])
    unused_block = unused_block[(unused_block['proc_date']>= start_date) & (unused_block['proc_date'] < end_date)]
    return unused_block

get_monthly_unused_block(flexIds,months)