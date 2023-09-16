import pandas as pd
from monthlyBlockStats import getNudgeBlockData





units = ['BH JRI','STM ST OR', 'MT OR','BH CSC','ST OR']
months = ['6','7','8','9']



elite = pd.read_csv('TNNAS  Surgeons - Elite.csv')
toa = pd.read_csv('TNNAS  Surgeons - TOA.csv')
howell_allen = pd.read_csv('TNNAS  Surgeons - Howell Allen.csv')
all_blocks = pd.DataFrame()

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

monthly_block_data,daily_block_data = getNudgeBlockData(units, months, elite)
print(daily_block_data)