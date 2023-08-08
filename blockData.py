from facilityconstants import jriRooms, stmSTORRooms,MTORRooms,CSCRooms,STORRooms
import re
from utilities import get_procedure_date
import pandas as pd

def get_num_frequencies(block_data):
    mylist = block_data.columns.tolist()
    r = re.compile(".+blockStartDate$")
    newlist = list(filter(r.match, mylist)) # Read Note below
    return len(newlist)



def fill_column(colName, value,data):
    return data.fillna({colName:value})

def fill_empty_data(num_frequencies, data):
    for x in range(num_frequencies):
        data = fill_column(f'frequencies[{x}].dowApplied', -1,data)
        data = fill_column(f'frequencies[{x}].weeksOfMonth[0]',-1,data)
        data =fill_column(f'frequencies[{x}].weeksOfMonth[1]',-1,data)
        data =fill_column(f'frequencies[{x}].weeksOfMonth[2]',-1,data)
        data =fill_column(f'frequencies[{x}].weeksOfMonth[3]',-1,data)
        data =fill_column(f'frequencies[{x}].weeksOfMonth[4]',-1,data)
        data =fill_column(f'frequencies[{x}].blockStartDate',get_procedure_date('2000-1-1'),data)
        data =fill_column(f'frequencies[{x}].blockEndDate',get_procedure_date('2000-1-1'),data)
        data =fill_column(f'frequencies[{x}].blockStartTime',get_procedure_date('2000-1-1'),data)
        data =fill_column(f'frequencies[{x}].blockEndTime',get_procedure_date('2000-1-1'),data)
        data =fill_column(f'frequencies[{x}].state','Empty',data)
    return data




def get_block_data(block_data):
    num_frequencies = get_num_frequencies(block_data)
    block_data = fill_empty_data(num_frequencies, block_data)
    block_data = block_data[block_data['ministry'] == 'TNNAS'].copy()
    block_data = block_data[(block_data['room'].isin(jriRooms)) | (block_data['room'].isin(stmSTORRooms)) 
                            | (block_data['room'].isin(MTORRooms)) | (block_data['room'].isin(CSCRooms)) |
                            (block_data['room'].isin(STORRooms))].copy()
    closed_rooms = block_data[(block_data['flexId'] == -1)]
    block_data = block_data[(block_data['type'] == 'Surgeon') | (block_data['type'] == 'Surgical Specialty')
                            | (block_data['type'] == 'Surgeon Group')].copy()
    return block_data


def create_block_data(filename):
    block_data = pd.read_csv(filename)
    return get_block_data(block_data)