from facilityconstants import orLookUp, units



def get_future_open_times(starDate, endDate, dataFrameLookup, cum_block_stats):
    print('start date', starDate)
    print('end date', endDate)
    for unit in units:
        for room in orLookUp[unit]:
            print(room)


