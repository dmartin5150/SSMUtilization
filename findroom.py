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
        if (proc_count == 1):
            duration_std = 0
        else: 
            duration_std= round(curProcedure['duration'].std(),0)
        unit = curProcedure.iloc[0]['unit']
        for room in rooms:
            num_rooms = curProcedure[curProcedure['room'] == room].shape[0]
            # print('num_rooms', num_rooms, 'count', proc_count)
            usage = round((num_rooms/proc_count)*100,0)
            row_to_append = pd.DataFrame([{'unit': unit,'room':room,'procedureName':procedure, 'usage': usage,'duration_mean':duration_mean, 'duration_std':duration_std}])
            # room_stats = room_stats.append({'unit': unit,'room':room,'procedureName':procedure, 'usage': usage,'duration_mean':duration_mean, 'duration_std':duration_std}, ignore_index=True)
            room_stats = pd.concat([room_stats, row_to_append])
    room_stats.fillna(0,inplace=True)
    room_stats.to_csv(filename)
    return room_stats





def get_room_no_surgeon(room_stats, open_time, start_date, unit, procedure_name):
    print('start date', start_date, 'type', type(start_date))
    print(type(open_time.iloc[0]['proc_date']))
    cur_stats = room_stats[(room_stats['unit'] == unit) & (room_stats['procedureName'] == procedure_name)]
    duration = cur_stats.iloc[0]['duration_mean']
    cur_open_times = open_time[(open_time['unit'] == unit) & (open_time['proc_date'] >= start_date ) &
                               (open_time['open_type'] == 'OPEN') & (open_time['unused_block_minutes'] >= duration)]
    print('curStats', cur_stats)
    print('open times', cur_open_times)






def get_room_stats(open_times):

    room_stat_summary = [{'id': index, 'openTimeName': row.openTimeName, 'unit': row.unit,'name':row.openTimeName, 'local_start_time':row.local_start_time, 'local_end_time':row.local_end_time,
                          'room':row.room, 'unused_block_minutes':row.unused_block_minutes, 'formatted_minutes':row.formatted_minutes, 
                          'open_type':row.open_type, 'proc_date': str(row.proc_date), 'release_date':str(row.release_date), 'open_start_time':row.open_start_time.strftime('%Y-%m-%dT%H:%M:%SZ')
                          } for index, row in open_times.iterrows()] 
    return room_stat_summary




def create_roomstats_summary(room_stats):
    # print('row stats', room_stats)
    room_stat_summary= [{'unit':row.unit, 'room': row.room,'procedureName': row.procedureName, 
                              'usage': row.usage, 'duration': row.duration_mean, 'duration_std':row.duration_std}
                          for index, row in room_stats.iterrows()] 
    return room_stat_summary


def get_room_stats_from_file(filename):
    return pd.read_csv(filename)
