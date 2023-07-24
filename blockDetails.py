from utilities import get_procedure_date, get_block_date_with_time,formatProcedureTimes
from datetime import date;



def printType(date):
    return date


def get_block_details_data(room, blockDate, data):
    curDate = get_procedure_date(blockDate).date()
    block_data = data[(data['room'] == room) & (data['blockDate'] == curDate)]
    if block_data.empty:
        return []
    else:
      return[{'name': row.blockName, 'startTime':str(formatProcedureTimes(row.start_time)),'endTime':str(formatProcedureTimes(row.end_time)),'releaseDate':date.strftime(row.releaseDate,"%m-%d-%Y")} for index, row in block_data.iterrows()]  