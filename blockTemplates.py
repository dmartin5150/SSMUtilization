from blockData import get_num_frequencies
import pandas as pd;

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
    return block_schedule[(block_schedule['state'] != 'COMPLETE')]


def get_block_templates(block_data):
    print('blockdata', block_data)
    frequencies = get_num_frequencies(block_data)
    return create_block_templates(block_data,frequencies)