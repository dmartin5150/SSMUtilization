import pandas as pd


curFile = pd.read_csv('CSCData.csv')
print(curFile[curFile['procedures[0].primaryNpi'] == 0])
# print(curFile.dtypes)