import pandas as pd


units = ['BH JRI','STM ST OR', 'MT OR']
jriRooms = ['BH JRI 02','BH JRI 03','BH JRI 04','BH JRI 05','BH JRI 06','BH JRI 07','BH JRI 08','BH JRI 09']
stmSTORRooms = ['STM ST OR 01','STM ST OR 02','STM ST OR 03','STM ST OR 04','STM ST OR 05',
                'STM ST OR 06','STM ST OR 07','STM ST OR 08','STM ST OR 09','STM ST OR 10',
                'STM ST OR 11','STM ST OR 12','STM ST OR 14','STM ST OR 15','STM ST OR 16',
                'STM ST OR 17','STM ST OR 18','STM ST OR Hybrid']
MTORRooms = ['MT Cysto','MT OR 01','MT OR 02','MT OR 03','MT OR 04','MT OR 05','MT OR 06',
             'MT OR 07','MT OR 08','MT OR 09','MT OR 10','MT OR 11','MT OR 12','MT OR 14',
             'MT OR 15','MT OR 16','MT OR 17']


CSCRooms = ['BH CSC 01','BH CSC 02','BH CSC 03','BH CSC 04','BH CSC 05','BH CSC 06','BH CSC 07','BH CSC 09']
orLookUp = {'BH JRI': jriRooms,'STM ST OR':stmSTORRooms, 'MT OR': MTORRooms,'BH CSC':CSCRooms}

baseData = pd.read_csv('AllCaseData.csv',parse_dates=['procedureDate','startTime', 'endTime'])
# print(baseData)
jriData = baseData[baseData['room'].isin(jriRooms)]
                
jriData.to_csv('JRIData.csv')

STMSTORData = baseData[baseData['room'].isin(stmSTORRooms)]
STMSTORData.to_csv('STMSTORData.csv')

MTORData = baseData[baseData['room'].isin(MTORRooms)]
# print(MTORData.shape)
MTORData.to_csv('MTORData.csv')

CSCData = baseData[baseData['room'].isin(CSCRooms)]
CSCData.to_csv('CSCData.csv')

