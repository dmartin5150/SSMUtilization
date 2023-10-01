from calendar import Calendar, monthrange
import pandas as pd
from utilities import get_procedure_date
from datetime import datetime

grid_block_data_cols = ['room', 'blockDate', 'block_status']

def get_monthly_grid_block_schedule(curMonth,roomLists, block_schedule):
    grid_block_data = pd.DataFrame(columns=grid_block_data_cols)
    c = Calendar()
    index = 0
    procDate =  datetime.strptime('2023-09-08', '%Y-%m-%d').date()
    for d in [x for x in c.itermonthdates(2023, curMonth) if x.month == curMonth]:
        # print(d)
        # if (d == procDate):
        #     print('dates are equal')
        for roomList in roomLists:
            for room in roomList: 
                block_data = block_schedule[(block_schedule['room'] == room) & (block_schedule['blockDate'] == d) ]
                # if (d == procDate):
                    # print('room', room, 'block_data', block_data, )
                if block_data.empty:
                    grid_block_data.loc[index]= [room, d, 0]
                else:
                    # print('adding block to grid')
                    grid_block_data.loc[index]=[room, d, 1]
                index +=1
    return grid_block_data


def get_grid_block_schedule(startDate,endDate,roomLists, data): 
    final_grid_block_schedule = pd.DataFrame()
    for curMonth in range(startDate.month, endDate.month):
        cur_grid_schedule = get_monthly_grid_block_schedule(curMonth,roomLists, data)
        final_grid_block_schedule = pd.concat([final_grid_block_schedule, cur_grid_schedule])
    return final_grid_block_schedule

def get_grid_block_schedule_from_file(filename):
    grid_block_schedule = pd.read_csv(filename)
    grid_block_schedule['blockDate'] = grid_block_schedule['blockDate'].apply(lambda x: get_procedure_date(x))
    return grid_block_schedule


def create_grid_block_schedule(startDate, endDate, roomLists, block_schedule, grid_ouput_filename):
    grid_block_schedule = get_grid_block_schedule(startDate,endDate,roomLists,block_schedule) 
    grid_block_schedule.to_csv(grid_ouput_filename,index=False)
    return grid_block_schedule