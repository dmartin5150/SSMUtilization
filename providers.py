def get_providers(unit,dataFrameLookup):
    data = dataFrameLookup[unit]
    data = data[data['NPI'] != 0]
    providers = data[['fullName','NPI']].copy()
    providers = providers.drop_duplicates().sort_values(by=['fullName'])
    surgeon_list = [{'id': row.NPI, 'name':row.fullName,'NPI':row.NPI, 'selected':True} for index, row in providers.iterrows() ] 
    return surgeon_list