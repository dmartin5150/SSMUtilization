import pandas as pd

class BasicBlockData:
    bt_minutes =  -1
    nbt_minutes = -1
    total_minutes = -1
    flexId = -1
    utilization = -1



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

def getBlockData( npiData):
    blockData = BasicBlockData()
    blockData.bt_minutes = npiData['bt_minutes'].sum()
    blockData.nbt_minutes = npiData['nbt_minutes'].sum()
    blockData.total_minutes = npiData['total_minutes'].sum()
    blockData.flexId = npiData.iloc[0]['id']
    blockData.utilization = 0
    if (blockData.total_minutes != 0):
        blockData.utilization = str(round(blockData.bt_minutes/blockData.total_minutes * 100,1)) +'%'
    return blockData


def getMonthlyBlockData(unit,month,npi,npiData,curBlocks):
    baseData = getBlockData(npiData)
    return curBlocks.append({'flexId':baseData.flexId ,'unit':unit,'month':month, 'npi': npi,'bt_minutes':baseData.bt_minutes,'nbt_minutes':baseData.nbt_minutes, 'total_minute':baseData.total_minutes, 'utilization':baseData.utilization}, ignore_index=True)

def getDailyBlocks(unit, month, npi, npiData,dailyBlocks):
    curDates = npiData['blockDate'].to_list()
    for curDate in curDates:
         curdata = npiData[npiData['blockDate'] == curDate].copy()
         baseData = getBlockData(curdata)
         dailyBlocks = dailyBlocks.append({'flexId':baseData.flexId ,'unit':unit,'month':month, 'npi': npi,'bt_minutes':baseData.bt_minutes,'nbt_minutes':baseData.nbt_minutes, 'total_minute':baseData.total_minutes, 'utilization':baseData.utilization,'blockDate':curDate}, ignore_index=True)
    return dailyBlocks


def formatCurBlocks(curBlocks,all_blocks):
    curBlocks=curBlocks.merge(all_blocks,  left_on='npi', right_on='npi')
    curBlocks.drop(['npis', 'NPI_x','NPI_y', 'id', 'blockType', 'Unnamed: 0'], axis=1, inplace=True)
    return curBlocks.sort_values(by=['unit', 'npi', 'month'])

def getNudgeBlockData(units, months, surgeon_group):
    block_owners = getBlockOwner(surgeon_group)
    all_npis, all_blocks = getNPIandBlocks(block_owners, surgeon_group)
    monthlyBlocks = pd.DataFrame()
    dailyBlocks = pd.DataFrame()
    for unit in units:
        for month in months:
            curdata = getMonthlyData(unit,month)
            for npi in all_npis:
                npiData = updateNPIData(curdata,npi)
                if npiData.empty:
                    continue
                monthlyBlocks= getMonthlyBlockData(unit, month, npi, npiData,monthlyBlocks)
                dailyBlocks = getDailyBlocks(unit, month, npi, npiData,dailyBlocks)
    monthlyBlocks = formatCurBlocks(monthlyBlocks,all_blocks)
    return monthlyBlocks, dailyBlocks



