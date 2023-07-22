import pandas as pd
from facilityconstants import jriRooms, stmSTORRooms,MTORRooms
import pytz;
from datetime import timezone;


def get_unit_data(filename,grid_block_schedule):
    dataCols = ['procedures[0].primaryNpi','startTime','endTime','duration','procedureDate',
            'room','procedures[0].procedureName','unit']
    names = ['NPI', 'startTime', 'endTime', 'duration', 'procedureDate', 'room', 'procedureName','unit']
    baseData = pd.read_csv(filename, usecols=dataCols,parse_dates=['procedureDate','startTime', 'endTime'])
    baseData.rename(columns={'procedures[0].primaryNpi':'NPI','procedures[0].procedureName':'procedureName'}, inplace=True)

    surgeons = pd.read_csv('Surgeons.csv')
    dataWithSurgeonNames = baseData.merge(surgeons, left_on='NPI', right_on='npi')

    #only select SSM units 
    dataWithSurgeonNames = dataWithSurgeonNames[(dataWithSurgeonNames['room'].isin(jriRooms)) | (dataWithSurgeonNames['room'].isin(stmSTORRooms)) 
                        | (dataWithSurgeonNames['room'].isin(MTORRooms))]

    # need to create date column without timestamp
    dataWithSurgeonNames['new_procedureDate'] = pd.to_datetime(dataWithSurgeonNames['procedureDate']).dt.tz_convert(None)



    #add procedure date without time for block information
    dataWithSurgeonNames['blockDate'] = dataWithSurgeonNames['new_procedureDate'].apply(lambda x: x.date())
    #add block status to procedure room/date
    # print('pre', dataWithSurgeonNames['blockDate'])
    dataWithSurgeonNames= dataWithSurgeonNames.merge(grid_block_schedule,how='left', left_on=['blockDate','room'], right_on=['blockDate','room'])


    #convert Zulu Time
    dataWithSurgeonNames['local_start_time'] = dataWithSurgeonNames['startTime'].apply(lambda x: x.replace(tzinfo=timezone.utc).astimezone(pytz.timezone("US/Central")))
    dataWithSurgeonNames['local_end_time'] = dataWithSurgeonNames['endTime'].apply(lambda x: x.replace(tzinfo=timezone.utc).astimezone(pytz.timezone("US/Central")))
    dataWithSurgeonNames['procedureDtNoTime'] = dataWithSurgeonNames['local_start_time'].apply(lambda x: x.date())
    dataWithSurgeonNames['weekday'] = dataWithSurgeonNames['procedureDtNoTime'].apply(lambda x: x.isoweekday())
    #remove soft blocks
    dataWithSurgeonNames = dataWithSurgeonNames[dataWithSurgeonNames['npi'] != 0]
    return dataWithSurgeonNames