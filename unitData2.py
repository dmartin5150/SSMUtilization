import pandas as pd
from facilityconstants import jriRooms, stmSTORRooms,MTORRooms
import pytz;
from datetime import date, time,datetime, timezone;
from utilities import get_procedure_date_with_time
from utilities import create_zulu_datetime_from_string_format2, convert_zulu_to_central_time_from_date, get_date_from_datetime,get_procedure_date_with_time

def convert_unit_datetime_strings_to_dates(unitData):
    unitData['procedureDate'] = unitData['procedureDate'].apply(lambda x: create_zulu_datetime_from_string_format2(x))
    unitData['startTime'] = unitData['startTime'].apply(lambda x: create_zulu_datetime_from_string_format2(x))
    unitData['endTime'] = unitData['endTime'].apply(lambda x: create_zulu_datetime_from_string_format2(x))
    return unitData

def convert_unit_datetime_to_central_time(unitData):
    unitData['procedureDate'] = unitData['procedureDate'].apply(lambda x: convert_zulu_to_central_time_from_date(x))
    unitData['local_start_time'] = unitData['startTime'].apply(lambda x: convert_zulu_to_central_time_from_date(x))
    unitData['local_end_time'] = unitData['endTime'].apply(lambda x: convert_zulu_to_central_time_from_date(x))
    return unitData

def convert_start_end_datetime_to_date_only(unitData):
    unitData['blockDate'] = unitData['procedureDate'].apply(lambda x: get_date_from_datetime(x))
    unitData['procedureDtNoTime'] = unitData['local_start_time'].apply(lambda x: get_date_from_datetime(x))
    return unitData


    


def create_pt_compare (unitData):
    timezone = pytz.timezone("US/Central")
    unitData['ptStart'] = unitData['local_start_time'].apply(lambda x: timezone.localize(datetime.combine(date(2023, 1, 1), 
                          time(x.hour, x.minute,x.second))))
    unitData['ptEnd'] = unitData['local_end_time'].apply(lambda x: timezone.localize(datetime.combine(date(2023, 1, 1), 
                          time(x.hour, x.minute,x.second))))
    return unitData



def get_unit_data(filename,grid_block_schedule):
    dataCols = ['procedures[0].primaryNpi','startTime','endTime','duration','procedureDate',
            'room','procedures[0].procedureName','unit']
    names = ['NPI', 'startTime', 'endTime', 'duration', 'procedureDate', 'room', 'procedureName','unit']
    baseData = pd.read_csv(filename, usecols=dataCols)
    baseData.rename(columns={'procedures[0].primaryNpi':'NPI','procedures[0].procedureName':'procedureName'}, inplace=True)

    surgeons = pd.read_csv('Surgeons.csv')
    dataWithSurgeonNames = baseData.merge(surgeons, left_on='NPI', right_on='npi')

    #only select SSM units 
    dataWithSurgeonNames = dataWithSurgeonNames[(dataWithSurgeonNames['room'].isin(jriRooms)) | (dataWithSurgeonNames['room'].isin(stmSTORRooms)) 
                        | (dataWithSurgeonNames['room'].isin(MTORRooms))]
    #properly format dates and times
    dataWithSurgeonNames = convert_unit_datetime_strings_to_dates(dataWithSurgeonNames)
    dataWithSurgeonNames = convert_unit_datetime_to_central_time(dataWithSurgeonNames)
    dataWithSurgeonNames = convert_start_end_datetime_to_date_only(dataWithSurgeonNames)
    #create dummydate with start endtimes for prime time comparsions set to 1-1-2023
    dataWithSurgeonNames = create_pt_compare (dataWithSurgeonNames)


    #add block status
    dataWithSurgeonNames= dataWithSurgeonNames.merge(grid_block_schedule,how='left', left_on=['blockDate','room'], right_on=['blockDate','room'])
    dataWithSurgeonNames['weekday'] = dataWithSurgeonNames['procedureDtNoTime'].apply(lambda x: x.isoweekday())
    #remove soft blocks
    dataWithSurgeonNames = dataWithSurgeonNames[dataWithSurgeonNames['npi'] != 0]
    return dataWithSurgeonNames