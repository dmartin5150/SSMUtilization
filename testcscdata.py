import pandas as pd
from datetime import datetime
from utilities import get_procedure_date, create_zulu_datetime_from_string,get_block_date_with_timezone

curFile = pd.read_csv('csc_gen_data.csv')
print(curFile[(curFile['procedureDtNoTime'] == '2023-09-27') & (curFile['room'] == 'BH CSC 09')])

# print(curFile[(curFile['proc_date']== '2023-09-27') & (curFile['room']== 'BH CSC 09')])

