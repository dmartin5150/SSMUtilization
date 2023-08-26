from utilities import formatMinutes,get_date_range
from facilityconstants import orLookUp
import calendar;


def getProcedures(unit,start_date,dataFrameLookup):
    data = dataFrameLookup[unit]
    data = data[data['room'].isin(orLookUp[unit])]
    start_date, end_date = get_date_range(start_date)
    data = data[(data['procedureDtNoTime']>= start_date) & (data['procedureDtNoTime'] < end_date)]
    return data.copy()



def get_monthly_stats(npi, procedures):
    daysOfWeek = list(calendar.day_abbr)
    card =[]
    for i in range(1,6):
        weekday = daysOfWeek[i-1]
        provider_procedures = procedures[(procedures['NPI'] == npi) & (procedures['weekday'] == i)]
        num_procedures = provider_procedures.shape[0]
        minutes = formatMinutes(provider_procedures['duration'].sum())
        card.append({'day':weekday, 'procedure':num_procedures, 'hour':minutes})
    return card


def get_surgeon_stats(unit,name, npi,dataFrameLookup): 
    secondary_cards = []
    august_procedures = getProcedures(unit,'2023-8-1',dataFrameLookup)
    # print('august procs', august_procedures)
    august_card_data = get_monthly_stats(npi, august_procedures)
    august_card = {'title':'August', 'data':august_card_data}
    july_procedures = getProcedures(unit,'2023-7-1',dataFrameLookup)
    # print('july procs', july_procedures)
    july_card_data = get_monthly_stats(npi, july_procedures)
    july_card = {'title':'July', 'data':july_card_data}
    june_procedures = getProcedures(unit,'2023-6-1',dataFrameLookup)
    june_card_data = get_monthly_stats(npi, june_procedures)
    june_card = {'title':'June', 'data':june_card_data}
    may_procedures = getProcedures(unit,'2023-7-1',dataFrameLookup)
    may_card_data = get_monthly_stats(npi, may_procedures)
    may_card = {'title':'May', 'data':may_card_data}
    april_procedures = getProcedures(unit,'2023-7-1',dataFrameLookup)
    april_card_data = get_monthly_stats(npi, april_procedures)
    april_card = {'title':'April', 'data':april_card_data}

    secondary_cards.append(may_card)
    secondary_cards.append(june_card)
    secondary_cards.append(july_card)
  
    return {'surgeon':{'id':npi,'value':npi, 'label':name},
            'mainCard':august_card,
            'secondaryCards':secondary_cards}