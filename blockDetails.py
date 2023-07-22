from utilities import get_procedure_date, get_block_date_with_time
from datetime import date;

def formatProcedureTimes(date):
    return date.strftime("%I:%M %p")

def printType(date):
    return date


def get_block_details_data(room, blockDate, data):
    curDate = get_procedure_date(blockDate).date()
    block_data = data[(data['room'] == room) & (data['blockDate'] == curDate)]
    if block_data.empty:
        return []
    else:
      return[{'name': row.blockName, 'startTime':str(formatProcedureTimes(get_block_date_with_time(row.start_time))),'endTime':str(formatProcedureTimes(get_block_date_with_time(row.end_time))),'releaseDate':date.strftime(row.releaseDate,"%m-%d-%Y")} for index, row in block_data.iterrows()]  