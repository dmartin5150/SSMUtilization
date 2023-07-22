import pandas as pd

pseudo_schedule_cols = ['local_start_time', 'local_end_time']

def create_pseudo_schedule(procedures):
    new_schedule = pd.DataFrame(columns=pseudo_schedule_cols)
    if procedures.shape[0] > 0:
        local_start_time = procedures.iloc[0]['local_start_time']
        local_end_time = procedures.iloc[0]['local_end_time']
        for x in range(1,procedures.shape[0]):
            curRow = procedures.iloc[x]
            if (curRow['local_start_time'] > local_end_time):
                new_schedule.loc[len(new_schedule.index)] = [local_start_time, local_end_time] 
                local_start_time = curRow['local_start_time']
                local_end_time =  curRow['local_end_time']
            elif ((curRow['local_start_time'] < local_end_time) & (curRow['local_end_time'] < local_end_time)):
                continue
            else:
                local_end_time = curRow['local_end_time']
        new_schedule.loc[len(new_schedule.index)] = [local_start_time, local_end_time]
    return new_schedule 