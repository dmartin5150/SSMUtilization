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


def get_block_owner(block_owner):
    num_npis = get_num_npis(block_owner)
    block_owner = fill_empty_npis(num_npis, block_owner)
    return block_owner[(block_owner['type'] == 'Surgeon') | (block_owner['type'] == 'Surgeon Group') ]