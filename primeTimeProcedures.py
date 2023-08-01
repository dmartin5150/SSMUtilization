from facilityconstants import jriRooms, stmSTORRooms,MTORRooms,orLookUp
from blockSchedule import get_block_schedule
from gridBlockSchedule import get_grid_block_schedule
from unitData import get_unit_data
from datetime import date, datetime;
from enum import Enum

class RoomOptions(Enum):
    All = 1
    Selected = 2
    Surgeon = 3

# RoomOptions = Enum('RoomOptions', ['All', 'Selected', 'Surgeon'])

def getEndDate(startDate):
    if startDate.month == 12:
        next_month = 1
        next_year = startDate.year +1
    else:
        next_month = startDate.month +1
        next_year = startDate.year
    return date(next_year, next_month,1)


    

def getPTProcedures(startDate, data):
    endDate = getEndDate(startDate)
    procedures = data[(data['procedureDtNoTime']>= startDate) & (data['procedureDtNoTime'] < endDate)]
    return procedures

def getPTProceduresWithRange(startDate, endDate, data):
        return data[(data['procedureDtNoTime']>= startDate) & (data['procedureDtNoTime'] <= endDate)]

def getfilteredPTProcedures(procedures, selectedProviders):
     return procedures[procedures['npi'].isin(selectedProviders)]


def get_procedures_from_date(data, date):
    return data[data['procedureDtNoTime'] == date.date()].sort_values(by=['local_start_time'])

def get_procedures_from_room(data, room):
    return data[data['room'] == room].sort_values(by=['local_start_time'])

def get_filtered_procedures(procedures, npi_list): 
    return procedures[procedures['NPI'].isin(npi_list)]

def getfilteredRoomPTProcedures(procedures,roomSelectionOption, selectedRooms):
     if (roomSelectionOption == 1):
          return procedures
     else:
          return procedures[procedures['room'].isin(selectedRooms)]

     

