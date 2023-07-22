from utilities import formatProcedureTimes,get_procedure_date,formatMinutes
from datetime import date, timedelta, datetime, timezone;
import pytz;

def get_room_details(unit, selected_date, room,data,pt_start, pt_end):
    details = []
    pt_start_data = pt_start.split(':')
    pt_end_data = pt_end.split(':')
    # print(pt_end)
    procedure_date = get_procedure_date(selected_date)
    room_data = data[(data['procedureDtNoTime'] == procedure_date.date()) & (data['room'] == room)].sort_values(by=['startTime'])

    prime_time_start= datetime(procedure_date.year,procedure_date.month,procedure_date.day,int(pt_start_data[0]),int(pt_start_data[1]),0).astimezone(pytz.timezone("US/Central"))
    prime_time_end= datetime(procedure_date.year,procedure_date.month,procedure_date.day,int(pt_end_data[0]),int(pt_end_data[1]),0).astimezone(pytz.timezone("US/Central"))
    room_data.reset_index(drop=True, inplace=True)
    for ind in room_data.index:
        surgeon = room_data['fullName'][ind]
        npi = room_data['NPI'][ind]
        start_time = room_data['local_start_time'][ind]
        end_time = room_data['local_end_time'][ind]
        duration = room_data['duration'][ind]
        procedure_name = room_data['procedureName'][ind]
        # print(ind)
        if ind == 0:
            if (start_time > prime_time_start):
                if (start_time > prime_time_end):
                    time_difference = (prime_time_end - prime_time_start).seconds/60
                else:
                    time_difference = (start_time - prime_time_start).seconds/60
                if time_difference > 15:
                    formatted_time = formatMinutes(time_difference)
                    formatted_start = formatProcedureTimes(prime_time_start)
                    if (start_time > prime_time_end):
                        formatted_end = formatProcedureTimes(prime_time_end)
                    else:
                        formatted_end = formatProcedureTimes(start_time)
                    details.append({'id': str(ind + 0.5), 'col1':'Open Time','col2':'','col3':str(formatted_start),'col4':str(formatted_end),'col5':str(formatted_time)}) 
        else:
            if (start_time > prime_time_start):
                time_difference = (start_time - room_data['local_end_time'][ind - 1]).seconds/60
                if time_difference > 15:
                    formatted_time = formatMinutes(time_difference)
                    formatted_start = formatProcedureTimes(room_data['local_end_time'][ind - 1])
                    formatted_end = formatProcedureTimes(start_time)
                    details.append({'id': str(ind + 0.5), 'col1':'Open Time','col2':'','col3':str(formatted_start),'col4':str(formatted_end),'col5':str(formatted_time)}) 
        formatted_time = formatMinutes(duration)
        formatted_start = formatProcedureTimes(start_time)
        formatted_end = formatProcedureTimes(end_time)
        details.append({'id': str(npi), 'col1':str(surgeon),'col2':str(procedure_name),'col3':str(formatted_start),'col4':str(formatted_end),'col5':str(formatted_time)})
        if ind == len(room_data.index)-1:
            if end_time < prime_time_end:  
                time_difference = (prime_time_end - end_time).seconds/60
                if time_difference > 15:
                    formatted_time = formatMinutes(time_difference)
                    formatted_start = formatProcedureTimes(end_time)
                    formatted_end = formatProcedureTimes(prime_time_end)
                    details.append({'id':str(ind + 0.75),'col1':'Open Time','col2':'','col3':str(formatted_start), 'col4':str(formatted_end),'col5':str(formatted_time)})
        
    return details