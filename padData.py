import pandas as pd
from utilities import get_procedure_date,all_dates_current_month
from datetime import  datetime;



def remove_block_weekends(procedure_date, data):
    # procedure_date = get_procedure_date(start_date)
    month_dates = all_dates_current_month(procedure_date.month, procedure_date.year)
    for date in month_dates: 
        procedure_date = get_procedure_date(date).date()
        if ((procedure_date.isoweekday()==6) | (procedure_date.isoweekday() == 7)):
            data = data[data['blockDate'] != procedure_date]
            continue
    return data


def remove_weekend(data, procedure_date):
    return (data[data['procedureDtNoTime'] != procedure_date])

def remove_weekends(start_date, data):
    procedure_date = get_procedure_date(start_date)
    month_dates = all_dates_current_month(procedure_date.month, procedure_date.year)
    for date in month_dates: 
        procedure_date = get_procedure_date(date).date()
        if ((procedure_date.isoweekday()==6) | (procedure_date.isoweekday() == 7)):
            data = remove_weekend(data,procedure_date)
            continue
    return data



def pad_block_data(stats,procedure_date,unit):
    stats = remove_block_weekends(procedure_date, stats)
    block_dates = stats['blockDate'].apply(lambda x: x.strftime("%Y-%m-%d"))
    block_dates = block_dates.drop_duplicates().to_list()
    # print('block dates', block_dates)
    # procedure_date = get_procedure_date(procedure_date)
    # print('procedure date', procedure_date)
    # procedure_date = start_date
    month_dates = all_dates_current_month(procedure_date.month, procedure_date.year)
    # print('month dates', list(set(month_dates)))
    # missing_dates = list(set(month_dates).difference(block_dates))
    missing_dates = list((x for x in month_dates if x not in block_dates))
    # ('missing_dates', missing_dates)
    weekdays = []
    for date in missing_dates:
        # print('missing date', date)
        curDate = get_procedure_date(date)
        if ((curDate.isoweekday() == 6) | (curDate.isoweekday() == 7)):
            continue
        weekdays.append(date)
    # print('weekdays', weekdays)
    for weekday in weekdays:
        idx = len(stats) 
        # print('columns', stats.columns)
        # print('weekday',weekday)
        # print('idx',idx)
        # print('converted', datetime.strptime(weekday, "%Y-%m-%d").date())
        stats.loc[len(stats.index)]=[idx+.25,datetime.strptime(weekday, "%Y-%m-%d").date(),unit,'none','No Block',0, 0, 0, 'ALL','None','2023-1-1','2023-1-1','0','2023-1-1']
        stats.loc[len(stats.index)]=[idx+.5,datetime.strptime(weekday, "%Y-%m-%d").date(),unit,'none','No Block',0, 0, 0, 'IN','None','2023-1-1','2023-1-1','0','2023-1-1']
        stats.loc[len(stats.index)]=[idx+.75,datetime.strptime(weekday, "%Y-%m-%d").date(),unit,'none','No Block',0, 0, 0, 'OUT','None','2023-1-1','2023-1-1','0','2023-1-1']
    # print ('post', stats.sort_values(by=['blockDate']))
    return stats.sort_values(by=['blockDate'])



def getBlankEntry (id, unit,date):
    return {'id': id, 'calendar': {'unit': unit, 'NPI': '0', 'procedureDate': date, 'room': 'none', 'prime_time_minutes': '0', 'non_prime_time_minutes': '0'}, 'grid': {'unit': unit, 'room': 'none', 'procedureDate': date, 'prime_time_minutes': '0', 'non_prime_time_minutes': '0','block_status':'0'}, 'details': {'fullName': 'Blank', 'local_start_time': '00:00 PM', 'local_end_time': '00:00 PM', 'procedureName': 'Blank', 'duration': '0', 'procedureDate': date}}


def pad_data(pt_hours,unit,start_date):
    data = pt_hours['surgeryInfo']
    # print('data', data)
    procedure_dates = []
    for procedure in data:
        if procedure['calendar']['procedureDate'] in procedure_dates:
            continue
        procedure_dates.append(procedure['calendar']['procedureDate'])
    # print('start date', start_date)
    procedure_date = get_procedure_date(start_date)
    # print('procedure date', procedure_date)
    month_dates = all_dates_current_month(procedure_date.month, procedure_date.year)
    # month_dates = all_dates_current_month(start_date.month, start_date.year)
    missing_dates = list(set(month_dates).difference(procedure_dates))
    weekdays = []
    for date in missing_dates:
        curDate = get_procedure_date(date)
        if ((curDate.isoweekday() == 6) | (curDate.isoweekday() == 7)):
            continue
        weekdays.append(date)
    for weekday in weekdays:
        idx = len(pt_hours) 
        blankEntry = getBlankEntry(idx,unit, weekday)
        pt_hours['surgeryInfo'].append(blankEntry)
    return pt_hours