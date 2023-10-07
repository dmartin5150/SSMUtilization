import pandas as pd
from utilities import get_procedure_date

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
    block_schedule = pd.read_csv('block_release_schedule.csv')
    blocks_with_owners = blocks_with_owners.merge(block_schedule, how='inner', left_on='id', right_on='flexId')
    print(blocks_with_owners.columns)
    return blocks_with_owners


def getNPIandBlocks(block_owners, group):
    all_npis = group['NPI']
    all_blocks = block_owners.merge(all_npis, how='left', left_on='npi', right_on='NPI')
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
    row_to_append = pd.DataFrame([{'flexId':baseData.flexId ,'unit':unit,'month':month, 'npi': npi,'bt_minutes':baseData.bt_minutes,'nbt_minutes':baseData.nbt_minutes, 'total_minute':baseData.total_minutes, 'utilization':baseData.utilization}])
    curBlocks = pd.concat([curBlocks, row_to_append])
    return curBlocks
    # return curBlocks.append({'flexId':baseData.flexId ,'unit':unit,'month':month, 'npi': npi,'bt_minutes':baseData.bt_minutes,'nbt_minutes':baseData.nbt_minutes, 'total_minute':baseData.total_minutes, 'utilization':baseData.utilization}, ignore_index=True)

def getDailyBlocks(unit, month, npi, npiData,dailyBlocks):
    curDates = npiData['blockDate'].to_list()
    # print('npi data columns', npiData.columns)
    for curDate in curDates:
         curdata = npiData[npiData['blockDate'] == curDate].copy()
         releaseDate = curdata.iloc[0]['releaseDate']
         room = curdata.iloc[0]['room']
         startTimeDate = curdata.iloc[0]['blockStartTime'].split(' ')
         startTime= startTimeDate[1]
        #  print('start time type', type(startTime))
         endTimeDate = curdata.iloc[0]['blockEndTime'].split(' ')
         endTime= endTimeDate[1]
         baseData = getBlockData(curdata)
         row_to_append = pd.DataFrame([{'flexId':baseData.flexId ,'unit':unit,'room':room, 'month':month, 'npi': npi,'bt_minutes':baseData.bt_minutes,'nbt_minutes':baseData.nbt_minutes, 'total_minute':baseData.total_minutes, 'utilization':baseData.utilization,'blockDate':curDate,'startTime': startTime, 'endTime': endTime, 'releaseDate':releaseDate}])
         dailyBlocks = pd.concat(dailyBlocks, row_to_append)
        #  dailyBlocks = dailyBlocks.append({'flexId':baseData.flexId ,'unit':unit,'room':room, 'month':month, 'npi': npi,'bt_minutes':baseData.bt_minutes,'nbt_minutes':baseData.nbt_minutes, 'total_minute':baseData.total_minutes, 'utilization':baseData.utilization,'blockDate':curDate,'startTime': startTime, 'endTime': endTime, 'releaseDate':releaseDate}, ignore_index=True)
    return dailyBlocks


def formatCurBlocks(curBlocks,all_blocks):
    curBlocks=curBlocks.merge(all_blocks,  left_on='npi', right_on='npi')
    curBlocks['month']=curBlocks['month'].apply(lambda x: int(x))
    curBlocks.rename(columns={'flexId_x':'flexId','unit_x':'unit','blockType_x':'blockType'},inplace=True)
    curBlocks.drop(['npis', 'NPI_x','NPI_y', 'id', 'Unnamed: 0','id','blockType_y','name_x','unit_y','flexId_y','name_y'], axis=1, inplace=True)
    # print('curBlocks columns', curBlocks.columns)
    return curBlocks.sort_values(by=['unit', 'npi', 'month'])

def getBlockSchedule(monthlyBlocks):
    block_schedule = pd.read_csv('block_release_schedule.csv')
    block_owners = pd.read_csv('block_id_owners.csv')
    block_owners=block_owners[['npi','fullName','id']]
    block_schedule = block_schedule.merge(block_owners, how='inner', left_on='flexId', right_on='id').drop_duplicates()
    flexIds = monthlyBlocks['flexId'].drop_duplicates().to_list()
    block_schedule['filter'] = block_schedule.apply(lambda row: (row['flexId']in flexIds), axis=1)
    return block_schedule[block_schedule['filter'] == True]

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
    dailyBlocks = getBlockSchedule(monthlyBlocks)
    # print('making daily blcoks')
    dailyBlocks.to_csv('db.csv')
    monthlyBlocks = formatCurBlocks(monthlyBlocks,all_blocks)
    return monthlyBlocks, dailyBlocks

def getSummaryMonthlyBlocks(monthlyBlocks):
    flexIds = monthlyBlocks['flexId'].to_list()
    summaryBlock = pd.DataFrame()
    months = {}
    for flexId in flexIds:
        curblocks = monthlyBlocks[monthlyBlocks['flexId'] == flexId].sort_values(by='month')
        months = {}
        for x in range(1,curblocks.shape[0]):
            curMonth = curblocks.iloc[x]['month']
            # print('curmonth', type(curMonth), curMonth,(curMonth == '7'))
            if (curMonth == '7'):
                months['July'] = curblocks.iloc[x]['utilization']
            if(curMonth == '8'):
                months['August'] = curblocks.iloc[x]['utilization']
            if(curMonth == '9'):
                months['September'] = curblocks.iloc[x]['utilization']
            if(curMonth == '10'):
                months['October'] = curblocks.iloc[x]['utilization']
        print('months', months)
    row_to_append = pd.DataFrame([{'Surgeon':curblocks['fullName'], 'unit':curblocks['unit']}])
    summaryBlock = pd.concat([summaryBlock,row_to_append])
    # summaryBlock = summaryBlock.append({'Surgeon':curblocks['fullName'], 'unit':curblocks['unit']}, ignore_index=True)
    return summaryBlock
                    



