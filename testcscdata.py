import pandas as pd
from datetime import datetime
from utilities import get_procedure_date, create_zulu_datetime_from_string,get_block_date_with_timezone
from calendar import Calendar
# curFile = pd.read_csv('csc_gen_data.csv')
# print(curFile[(curFile['procedureDtNoTime'] == '2023-09-27') & (curFile['room'] == 'BH CSC 09')])

c = Calendar()
for d in [x for x in c.itermonthdates(2023, 10) if x.month == 10]:
    print(d)
# print(curFile[(curFile['proc_date']== '2023-09-27') & (curFile['room']== 'BH CSC 09')])

