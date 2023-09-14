import pandas as pd

units = ['BH JRI','STM ST OR', 'MT OR','BH CSC','ST OR']
months = ['6','7','8']



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
    # print('row', row['npis'])
    if (row['npis'] == '[]'):
        return False
    # print('row', row)
    # print('pre')
    curNpi = row['npis'].strip('[,]')
    # print('post')
    if (str(npi) == curNpi):
        return True
    return False
curBlocks = pd.DataFrame()
for unit in units:
    for month in months:
        curFile = month + "_2023_" + unit + ".csv"
        curdata = pd.read_csv(curFile)
        curdata = curdata[(curdata['blockType'] == 'Surgeon') & (curdata['type'] == 'ALL')]
        for npi in all_npis:
            curdata = pd.read_csv(curFile)
            curdata = curdata[(curdata['blockType'] == 'Surgeon') & (curdata['type'] == 'ALL')]
            # print('npi', curdata['npis'])
            curdata['inBlock'] = curdata.apply(lambda row: checkValidNPI(npi, row), axis=1)
            curdata['npi'] = npi
            curdata = curdata[curdata['inBlock'] == True]
            curdata.drop(['inBlock','npis'], axis=1,inplace=True)
            curBlocks= curBlocks.append(curdata)
            # print(unit, curFile, npi, curdata.shape)
print(curBlocks)
