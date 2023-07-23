import re


def fill_column(colName, value,data):
    return data.fillna({colName:value})

def get_num_npis(data):
    mylist = data.columns.tolist()
    r = re.compile("^npis")
    newlist = list(filter(r.match, mylist)) # Read Note below
    return len(newlist)

def fill_empty_npis(num_npis, data):
    for x in range(num_npis):
        data = fill_column(f'npis[{x}]', -1,data)
    return data

def get_owner_npis (data, flexId,num_npis):
    curData = data[data['ownerId'] == flexId]
    return create_block_owners(curData,num_npis)

def check_selected_npis(npis, selectedNPIs):
    for npi in selectedNPIs:
        if (npi in npis):
            return True
    return False


def get_block_owner(block_owner):
    num_npis = get_num_npis(block_owner)
    block_owner = fill_empty_npis(num_npis, block_owner)
    return block_owner[(block_owner['type'] == 'Surgeon') | (block_owner['type'] == 'Surgeon Group') ]

def create_block_owners(data, npis):
    data.reset_index(inplace=True)
    cur_npi_list = []
    num_rows = data.shape[0]
    for x in range(num_rows):
        cur_row = data.iloc[x]
        for npi in range (npis):
            if cur_row[f'npis[{npi}]'] == -1:
                break
            cur_npi_list.append(int(cur_row[f'npis[{npi}]'])) 

    return cur_npi_list

