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

def getMonthlyData(unit, month):
            curFile = month + "_2023_" + unit + ".csv"
            curdata = pd.read_csv(curFile)
            return curdata[(curdata['blockType'] == 'Surgeon') & (curdata['type'] == 'ALL')]

def updateNPIData(curdata,npi):
        npiData = curdata.copy()
        npiData['inBlock'] = npiData.apply(lambda row: checkValidNPI(npi, row), axis=1)
        npiData['npi'] = npi
        return npiData[npiData['inBlock'] == True]

def getCurBlocks(unit, month, npi, npiData,curBlocks):
    bt_minutes = npiData['bt_minutes'].sum()
    nbt_minutes = npiData['nbt_minutes'].sum()
    total_minutes = npiData['total_minutes'].sum()
    flexId = npiData.iloc[0]['id']
    utilization = 0
    if (total_minutes != 0):
        utilization = str(round(bt_minutes/total_minutes * 100,1)) +'%'
    npiData.drop(['inBlock','npis'], axis=1,inplace=True)
    return curBlocks.append({'flexId':flexId ,'unit':unit,'month':month, 'npi': npi,'bt_minutes':bt_minutes,'nbt_minutes':nbt_minutes, 'total_minute':total_minutes, 'utilization':utilization}, ignore_index=True)

def formatCurBlocks(curBlocks,all_blocks):
    curBlocks=curBlocks.merge(all_blocks,  left_on='npi', right_on='npi')
    curBlocks.drop(['npis', 'NPI_x','NPI_y', 'id', 'blockType', 'Unnamed: 0'], axis=1, inplace=True)
    return curBlocks.sort_values(by=['unit', 'npi', 'month'])

def getMonthlyBlockData(units, months, surgeon_group):
    block_owners = getBlockOwner(surgeon_group)
    all_npis, all_blocks = getNPIandBlocks(block_owners, surgeon_group)
    curBlocks = pd.DataFrame()
    for unit in units:
        for month in months:
            curdata = getMonthlyData(unit,month)
            for npi in all_npis:
                npiData = updateNPIData(curdata,npi)
                if npiData.empty:
                    continue
                curBlocks= getCurBlocks(unit, month, npi, npiData,curBlocks)
    return formatCurBlocks(curBlocks,all_blocks)



