import pandas as pd
from facilityconstants import primetime_minutes_per_room,orLookUp
from utilities import get_procedure_date
import json;


def get_daily_utilization_per_room(room,date, data,prime_minute_per_room):
    room_data = data[(data['new_procedureDate'] == date) & (data['room'] == room)]['duration']
    if len(room_data) != 0:
        room_surgical_time = room_data.sum()
    else:
        room_surgical_time = 0
    return round(room_surgical_time/prime_minute_per_room*100,0)

def get_daily_room_utilization(unit, selected_date,data):
    utilization = []
    procedure_date = get_procedure_date(selected_date)
    rooms = orLookUp[unit]
    for room in rooms:
        room_utlization = get_daily_utilization_per_room(room, procedure_date,data,primetime_minutes_per_room)
        row_to_append = pd.DataFrame([{'id':room,'name':room,'property':str(int(room_utlization)) + '%'}])
        utilization = pd.concat([utilization,row_to_append])
        # utilization.append({'id':room,'name':room,'property':str(int(room_utlization)) + '%'})
    return json.dumps(utilization)