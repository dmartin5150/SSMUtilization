import pandas as pd
import numpy as np

overall_stats_cols =['unit','procedureName','procedure_count','rooms','duration_mean', 'duration_std' ]
room_stats_cols = ['unit', 'room', 'procedureName', 'usage']


def get_procedure_stats(procedures,rooms):
    overall_stats = pd.DataFrame(columns=overall_stats_cols)
    room_stats = pd.DataFrame(columns=room_stats_cols)
    procedure_names = procedures['procedureName'].drop_duplicates().tolist()
    procedures['duration'] = procedures.apply(lambda row: (row['local_end_time'] - row['local_start_time']).total_seconds()/60, axis=1)
    print(procedures.columns)
    for procedure in procedure_names:
        
        curProcedure = procedures[procedures['procedureName'] == procedure]
        proc_count = curProcedure.shape[0]
        proc_rooms = curProcedure['room'].drop_duplicates().tolist()
        # proc_rooms ='bhjri'
        duration_mean= curProcedure['duration'].mean()
        duration_std= curProcedure['duration'].std()
        unit = curProcedure.iloc[0]['unit']
        # duration_std= curProcedure.groupby("duration").agg([np.std])
        print('procedure', procedure,'count',proc_count, 'duration',duration_mean, 'std', duration_std)
        overall_stats = overall_stats.append({'unit': unit, 'procedureName':procedure, 'procedure_count':proc_count,'rooms':proc_rooms,
                                                  'duration_mean':duration_mean, 'duration_std':duration_std},ignore_index=True)
        print(overall_stats)
        # for room in rooms:
        #     num_rooms = curProcedure[curProcedure['room'] == room].shape[0]
        #     print('num_rooms', num_rooms, 'count', proc_count)
        #     usage = (num_rooms/proc_count)*100
        #     room_stats = room_stats.append({'unit': curProcedure['unit'],'rooms':proc_rooms,'procedureName':procedure, 'usage': usage}, ignore_index=True)

    # print(overall_stats.to_csv('procstats.csv'))
    overall_stats.to_csv('procstats.csv')
    # room_stats.to_csv('roomstats.csv')
    return procedures