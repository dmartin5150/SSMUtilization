import pandas as pd



room_stats_cols = ['unit', 'room', 'procedureName', 'usage','duration_mean', 'duration_std']


def create_procedure_stats(procedures,rooms,filename):
    room_stats = pd.DataFrame(columns=room_stats_cols)
    procedure_names = procedures['procedureName'].drop_duplicates().tolist()
    procedures['duration'] = procedures.apply(lambda row: (row['local_end_time'] - row['local_start_time']).total_seconds()/60, axis=1)
    for procedure in procedure_names:
        curProcedure = procedures[procedures['procedureName'] == procedure]
        proc_count = curProcedure.shape[0]
        duration_mean= round(curProcedure['duration'].mean(),0)
        duration_std= round(curProcedure['duration'].std(),0)
        unit = curProcedure.iloc[0]['unit']
        for room in rooms:
            num_rooms = curProcedure[curProcedure['room'] == room].shape[0]
            # print('num_rooms', num_rooms, 'count', proc_count)
            usage = round((num_rooms/proc_count)*100,0)
            room_stats = room_stats.append({'unit': unit,'room':room,'procedureName':procedure, 'usage': usage,'duration_mean':duration_mean, 'duration_std':duration_std}, ignore_index=True)

    room_stats.to_csv(filename)
    return room_stats

def get_room_stats_from_file(filename):
    return pd.read_csv(filename)
