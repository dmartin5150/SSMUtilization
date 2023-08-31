import pandas as pd


curFile = pd.read_csv('blockTemplates.csv')
kurtz_blocks = curFile[curFile['blockName'].str.contains('Kurtz')][['flexId','start_time','end_time','room','dow','wom1','wom2','wom3','wom4','wom5','state','start_date', 'end_date']]
print(kurtz_blocks[(kurtz_blocks.duplicated(['room','dow','wom1','wom2','wom3','wom4', 'wom5'], keep=False)) &
                   (kurtz_blocks['state'] == 'ACTIVE')].sort_values(by=['room','dow', 'wom1','wom2','wom3','wom4', 'wom5']))
# print(curFile.columns)
