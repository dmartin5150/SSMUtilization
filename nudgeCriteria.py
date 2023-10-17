import pandas as pd
from utilities import get_procedure_date
from datetime import date, timedelta;

def assignBlockName(flexId, blockNames):
    blockName = blockNames[blockNames['flexId'] == flexId]['blockName']
    if (blockName.shape[0] == 0):
        return 'Unknown'
    else:
        return blockName.iloc[0]


blocks = pd.read_csv('block_release_schedule.csv')
blockNames = blocks[['flexId','blockName']].drop_duplicates()
openTimes = pd.read_csv('opentime.csv')
openBlock = openTimes[openTimes['open_type'] == 'BLOCK']
# print(openBlock.shape[0])

openBlock['blockName'] = openBlock.apply(lambda row: assignBlockName(row['block_id'],blockNames.copy()), axis=1)
openBlock['release_date'] = openBlock['release_date'].apply(lambda x: get_procedure_date(x).date())
curDay = get_procedure_date('2023-10-10').date()
blockStartDate= curDay + timedelta(days=14)
openBlock['first_email']= openBlock.apply(lambda row: row['release_date'] - timedelta(days=10),axis=1)
openBlock['second_email']= openBlock.apply(lambda row: row['release_date'] - timedelta(days=7),axis=1)
blocks_with_release = openBlock[openBlock['release_date'] >= blockStartDate]
block_greater_than_4_hours = blocks_with_release[blocks_with_release['unused_block_minutes'] >= 240]
block_greater_than_4_hours = block_greater_than_4_hours.sort_values(by=['unit','release_date'])
block_greater_than_4_hours.to_csv('blockNudgeCriteria.csv')




