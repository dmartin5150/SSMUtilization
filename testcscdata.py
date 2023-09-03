import pandas as pd
from datetime import datetime
from utilities import get_procedure_date;

curFile = pd.read_csv('block_no_release.csv')
print(curFile.columns)
procDate =  datetime.strptime('2023-09-08', '%Y-%m-%d').date()
curFile['blockDate'] = curFile['blockDate'].apply(lambda x: get_procedure_date(x).date())
print(curFile.dtypes)
# jri_sched = curFile[(curFile['room'] == 'BH JRI 02')]['blockDate']
jri_sched = curFile[(curFile['room'] == 'BH JRI 02') & (curFile['blockDate'] == procDate)][['room','blockName','blockDate','start_date','end_date','dow','wom1','wom2','wom3','wom4','wom5','releaseDate']].sort_values(by=['releaseDate','room','dow','wom1','wom2','wom3','wom4','wom5'])
# jri_sched.to_csv('block_JRI_Closed_scheduled.csv')
print(jri_sched)
# print('curFile', curFile[(curFile['room'] == 'BH JRI 02') & (curFile['flexId'] == -1)][['room','start_date','end_date','dow','wom1','wom2','wom3','wom4','wom5','releaseDate']].sort_values(by=['releaseDate','room','dow','wom1','wom2','wom3','wom4','wom5']))
# print('curFile', jri_sched[(jri_sched['room'] == 'BH JRI 02')][['room','blockName','blockDate', 'start_date','releaseDate','end_date','dow','wom1','wom2','wom3','wom4','wom5',]].sort_values(by=['releaseDate','blockName','dow','wom1','wom2','wom3','wom4','wom5']))
# print(curFile.columns)
