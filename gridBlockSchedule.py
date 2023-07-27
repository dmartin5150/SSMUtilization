from calendar import Calendar, monthrange
import pandas as pd

grid_block_data_cols = ['room', 'blockDate', 'block_status']

def get_monthly_grid_block_schedule(curMonth,roomLists, block_schedule):
    grid_block_data = pd.DataFrame(columns=grid_block_data_cols)
    c = Calendar()
    index = 0
    for d in [x for x in c.itermonthdates(2023, curMonth) if x.month == curMonth]:
        for roomList in roomLists:
            for room in roomList: 
                block_data = block_schedule[(block_schedule['room'] == room) & (block_schedule['blockDate'] == d) ]
                if block_data.empty:
                    grid_block_data.loc[index]= [room, d, 0]
                else:
                    grid_block_data.loc[index]=[room, d, 1]
                index +=1
    return grid_block_data


def get_grid_block_schedule(startDate,endDate,roomLists, data): 
    final_grid_block_schedule = pd.DataFrame()
    for curMonth in range(startDate.month, endDate.month):
        cur_grid_schedule = get_monthly_grid_block_schedule(curMonth,roomLists, data)
        final_grid_block_schedule = pd.concat([final_grid_block_schedule, cur_grid_schedule])
    return final_grid_block_schedule