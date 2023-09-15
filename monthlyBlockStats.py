import pandas as pd

units = ['BH JRI','STM ST OR', 'MT OR','BH CSC','ST OR']
months = ['6','7','8','9']



elite = pd.read_csv('TNNAS  Surgeons - Elite.csv')
toa = pd.read_csv('TNNAS  Surgeons - TOA.csv')
howell_allen = pd.read_csv('TNNAS  Surgeons - Howell Allen.csv')


block_owners = pd.read_csv('block_id_owners.csv')
elite_npi = elite['NPI']
# print(elite_npi)

elite_blocks = block_owners.merge(elite_npi, how='inner', left_on='npi', right_on='NPI')
# print(elite_blocks)

howell_allen_npi = howell_allen['NPI']

howell_allen_blocks = block_owners.merge(howell_allen_npi, how='inner', left_on='npi', right_on='NPI')
# print(howell_allen_blocks)

toa_npi = toa['NPI']

toa_blocks = block_owners.merge(toa_npi, how='inner', left_on='npi', right_on='NPI')
# print(toa_blocks)

all_blocks = pd.concat([elite_blocks, howell_allen_blocks])
all_blocks = pd.concat([all_blocks, toa_blocks ])
all_npis = all_blocks['NPI']
# print(all_blocks)

def checkValidNPI(npi, row):
    if (row['npis'] == '[]'):
        return False
    curNpi = row['npis'].strip('[,]')
    if (str(npi) == curNpi):
        return True
    return False

def getMonthlyBlockData(units, months, surgeon_group):
    block_owners = pd.read_csv('block_id_owners.csv')
    blocks_with_owners = block_owners.merge(surgeon_group, how='inner', left_on='npi', right_on='NPI')
    all_npis = blocks_with_owners['NPI']
    curBlocks = pd.DataFrame()
    for unit in units:
        for month in months:
            curFile = month + "_2023_" + unit + ".csv"
            curdata = pd.read_csv(curFile)
            curdata = curdata[(curdata['blockType'] == 'Surgeon') & (curdata['type'] == 'ALL')]
            for npi in all_npis:
                npiData = curdata.copy()
                npiData['inBlock'] = npiData.apply(lambda row: checkValidNPI(npi, row), axis=1)
                npiData['npi'] = npi
                npiData = npiData[npiData['inBlock'] == True]
                if npiData.empty:
                    continue
                bt_minutes = npiData['bt_minutes'].sum()
                nbt_minutes = npiData['nbt_minutes'].sum()
                total_minutes = npiData['total_minutes'].sum()
                flexId = npiData.iloc[0]['id']
                utilization = 0
                if (total_minutes != 0):
                    utilization = str(round(bt_minutes/total_minutes * 100,1)) +'%'
                npiData.drop(['inBlock','npis'], axis=1,inplace=True)
                curBlocks= curBlocks.append({'flexId':flexId ,'unit':unit,'month':month, 'npi': npi,'bt_minutes':bt_minutes,'nbt_minutes':nbt_minutes, 'total_minute':total_minutes, 'utilization':utilization}, ignore_index=True)
                # print(unit, curFile, npi, curdata.shape)
    curBlocks=curBlocks.merge(all_blocks,  left_on='npi', right_on='NPI')

    curBlocks.drop(['npis', 'npi_x','npi_x', 'id', 'blockType'], axis=1, inplace=True)
    print(curBlocks.sort_values(by=['unit', 'NPI', 'month']))
    return curBlocks

getMonthlyBlockData(units, months, toa)