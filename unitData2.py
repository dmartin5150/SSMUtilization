import pandas as pd
from facilityconstants import jriRooms, stmSTORRooms,MTORRooms, CSCRooms, STORRooms
import pytz;
from datetime import date, time,datetime, timezone;
from utilities import get_block_date_with_timezone,get_procedure_date,cast_to_cst
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


def correct_two_day_procedures(row):
    timezone = pytz.timezone("US/Central")
    if (row['ptEnd'] < row['ptStart']):
        row['ptEnd'] =  timezone.localize(datetime.combine(date(2023, 1, 2), 
                          time(row['ptEnd'].hour, row['ptEnd'].minute,row['ptEnd'].second)))
    return row


def create_pt_compare (unitData):
    timezone = pytz.timezone("US/Central")
    unitData['ptStart'] = unitData['local_start_time'].apply(lambda x: timezone.localize(datetime.combine(date(2023, 1, 1), 
                          time(x.hour, x.minute,x.second))))
    unitData['ptEnd'] = unitData['local_end_time'].apply(lambda x: timezone.localize(datetime.combine(date(2023, 1, 1), 
                          time(x.hour, x.minute,x.second))))
    # Need to correct times where procedure start/end times cross midnight
    unitData = unitData.apply(lambda row: correct_two_day_procedures(row),axis=1)
    return unitData


def update_soft_blocks_datetimes(softBlocks):
    softBlocks['procedureDtNoTime'] = softBlocks['procedureDate'].apply(lambda x: get_block_date_with_timezone(x).date())
    softBlocks['startTime'] = softBlocks['startTime'].apply(lambda x:get_block_date_with_timezone(x))
    softBlocks['startTime'] = softBlocks['startTime'].apply(lambda x: convert_zulu_to_central_time_from_date(x))
    softBlocks['endTime'] = softBlocks['endTime'].apply(lambda x:get_block_date_with_timezone(x))
    softBlocks['endTime'] = softBlocks['endTime'].apply(lambda x: convert_zulu_to_central_time_from_date(x))
    return softBlocks



def get_unit_data(filename,grid_block_schedule):
    dataCols = ['procedures[0].primaryNpi','startTime','endTime','duration','procedureDate',
            'room','procedures[0].procedureName','unit']
    names = ['NPI', 'startTime', 'endTime', 'duration', 'procedureDate', 'room', 'procedureName','unit']
    baseData = pd.read_csv(filename, usecols=dataCols)
    # print('filename', filename, 'basedata', baseData.shape)
    baseData.rename(columns={'procedures[0].primaryNpi':'NPI','procedures[0].procedureName':'procedureName'}, inplace=True)
    softBlocks = baseData[baseData['NPI'] == 0]
    softBlocks = update_soft_blocks_datetimes(softBlocks.copy())
    surgeons = pd.read_csv('Surgeons.csv')
    dataWithSurgeonNames = baseData.merge(surgeons, left_on='NPI', right_on='npi')
    # print('filename', filename, 'after surgeons basedata', baseData.shape)
    #only select SSM units 
    dataWithSurgeonNames = dataWithSurgeonNames[(dataWithSurgeonNames['room'].isin(jriRooms)) | (dataWithSurgeonNames['room'].isin(stmSTORRooms)) 
                        | (dataWithSurgeonNames['room'].isin(MTORRooms)) | (dataWithSurgeonNames['room'].isin(CSCRooms)) |
                         (dataWithSurgeonNames['room'].isin(STORRooms)) ]
    #properly format dates and times
    dataWithSurgeonNames = convert_unit_datetime_strings_to_dates(dataWithSurgeonNames)
    dataWithSurgeonNames = convert_unit_datetime_to_central_time(dataWithSurgeonNames)
    dataWithSurgeonNames = convert_start_end_datetime_to_date_only(dataWithSurgeonNames)
    #create dummydate with start endtimes for prime time comparsions set to 1-1-2023
    dataWithSurgeonNames = create_pt_compare (dataWithSurgeonNames)


    #add block status
    dataWithSurgeonNames= dataWithSurgeonNames.merge(grid_block_schedule,how='left', left_on=['procedureDtNoTime','room'], right_on=['blockDate','room'])
    dataWithSurgeonNames['weekday'] = dataWithSurgeonNames['procedureDtNoTime'].apply(lambda x: x.isoweekday())
    #remove soft blocks
    dataWithSurgeonNames = dataWithSurgeonNames[dataWithSurgeonNames['npi'] != 0]
    print('npi values', dataWithSurgeonNames['npi'].drop_duplicates().sort_values())
    
    return dataWithSurgeonNames , softBlocks


def update_unit_date_times_from_file(unitData):
    unitData['procedureDate'] = unitData['procedureDate'].apply(lambda x: get_block_date_with_timezone(x))
    unitData['startTime'] = unitData['startTime'].apply(lambda x: get_block_date_with_timezone(x))
    unitData['endTime'] = unitData['endTime'].apply(lambda x: get_block_date_with_timezone(x))
    unitData['local_start_time'] = unitData['local_start_time'].apply(lambda x: get_block_date_with_timezone(x))
    unitData['local_start_time'] = unitData['local_start_time'].apply(lambda x: cast_to_cst(x))
    unitData['local_end_time'] = unitData['local_end_time'].apply(lambda x: get_block_date_with_timezone(x))
    unitData['local_end_time'] = unitData['local_end_time'].apply(lambda x: cast_to_cst(x))
    # unitData['local_start_time'] = unitData['local_start_time'].apply(lambda x: datetime.fromtimestamp(x))
    unitData['blockDate_x'] = unitData['blockDate_x'].apply(lambda x: get_procedure_date(x).date())
    unitData['procedureDtNoTime'] = unitData['procedureDtNoTime'].apply(lambda x:get_procedure_date(x).date())
    unitData['ptStart'] = unitData['ptStart'].apply(lambda x: cast_to_cst(get_block_date_with_timezone(x)))
    unitData['ptEnd'] = unitData['ptEnd'].apply(lambda x: cast_to_cst(get_block_date_with_timezone(x)))
    # unitData['blockDate_y'] = unitData['blockDate_y'].apply(lambda x: get_procedure_date(x))
    return unitData

    



def get_unit_data_from_file(filename):
    unitData = pd.read_csv(filename)
    unitData = update_unit_date_times_from_file(unitData)
    # print(unitData.dtypes)
    return unitData

def create_unit_data(filename,grid_block_schedule,ud_output_filename):
    unitData, unitSoftBlock = get_unit_data(filename,grid_block_schedule)
    unitData.to_csv(ud_output_filename,index=False)
    return unitData, unitSoftBlock