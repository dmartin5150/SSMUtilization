import pandas as pd






def checkValidNPI(npi, row):
    if (row['npis'] == '[]'):
        return False
    curNpi = row['npis'].strip('[,]')
    if (str(npi) == curNpi):
        return True
    return False

def getBlockOwner(surgeon_group):
    block_owners = pd.read_csv('block_id_owners.csv')
    blocks_with_owners = block_owners.merge(surgeon_group, how='inner', left_on='npi', right_on='NPI')
    return blocks_with_owners


def getNPIandBlocks(block_owners, group):
    all_npis = group['NPI']
    all_blocks = block_owners.merge(all_npis, how='inner', left_on='npi', right_on='NPI')
    return all_npis, all_blocks

def getMonthlyBlockData(units, months, surgeon_group):
    block_owners = getBlockOwner(surgeon_group)
    all_npis, all_blocks = getNPIandBlocks(block_owners, surgeon_group)
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
    curBlocks=curBlocks.merge(all_blocks,  left_on='npi', right_on='npi')
    curBlocks.drop(['npis', 'NPI_x','NPI_y', 'id', 'blockType', 'Unnamed: 0'], axis=1, inplace=True)
    print(curBlocks.sort_values(by=['unit', 'npi', 'month']))
    return curBlocks

