from facilityconstants import jriRooms, stmSTORRooms,MTORRooms,orLookUp
from blockSchedule import get_block_schedule
from gridBlockSchedule import get_grid_block_schedule
from unitData import get_unit_data
from datetime import date, datetime;

def getEndDate(startDate):
    if startDate.month == 12:
        next_month = 1
        next_year = startDate.year +1
    else:
        next_month = startDate.month +1
        next_year = startDate.year
    return date(next_year, next_month,1)

# def getPTProcedures(startDate, unit,block_templates):
#     endDate = getEndDate(startDate)
#     roomLists = [jriRooms,stmSTORRooms,MTORRooms]
#     block_no_release,block_schedule = get_block_schedule(startDate,endDate, block_templates,roomLists)
#     grid_block_schedule = get_grid_block_schedule(startDate,endDate,roomLists,block_schedule)
    
#     if unit == 'BH JRI':
#         print ('getting JRI data')
#         procedures = get_unit_data('JRIData.csv',grid_block_schedule)
#     elif unit == 'MT OR':
#         procedures = get_unit_data('MTORData.csv',grid_block_schedule)
#     else:
#         procedures = get_unit_data('STMSTORData.csv',grid_block_schedule)

#     procedures = procedures[procedures['room'].isin(orLookUp[unit])]
   
#     procedures = procedures[(procedures['procedureDtNoTime']>= startDate) & (procedures['procedureDtNoTime'] < endDate)]
#     return procedures

def getPTProcedures(startDate, data):
    endDate = getEndDate(startDate)
    procedures = data[(data['procedureDtNoTime']>= startDate) & (data['procedureDtNoTime'] < endDate)]
    return procedures



def get_procedures_from_date(data, date):
    return data[data['procedureDtNoTime'] == date.date()].sort_values(by=['local_start_time'])

def get_procedures_from_room(data, room):
    return data[data['room'] == room].sort_values(by=['local_start_time'])

def get_filtered_procedures(procedures, npi_list): 
    return procedures[procedures['NPI'].isin(npi_list)]
