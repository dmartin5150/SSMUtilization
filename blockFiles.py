import os
from datetime import datetime as dt, timedelta 
import json


def get_file_creation_date(filename):
    src = os.getcwd()
    path = os.path.join(src, filename)
    creation_time =  int(os.path.getctime(path))
    creation_date = dt.fromtimestamp(creation_time).strftime('%m-%d-%Y %H:%M:%S')
    return creation_date

def file_exists(filename):
    path = os.getcwd()
    try :
        if os.path.exists(os.path.join(path, filename)):
            return True
        else:
            return False
    except OSError as err:
        print("OS error: {0}".format(err))
        return False
    

def write_time_stamp(filename, time_stamp):
    with open(filename, 'w') as f:
        f.write(time_stamp)
    
def read_time_stamp(filename):
    with open(filename) as f:
        contents = f.readline()
        return contents
    
def get_saved_timestamp(filename):
    path = os.getcwd()
    if file_exists(filename):
        return read_time_stamp(filename)

def get_file_timestamp(filename):
    path = os.getcwd()
    if file_exists(filename):
        return get_file_creation_date(filename)
    
def write_block_json(procList, filename):
    with open(filename, 'w') as my_file:
        json.dump(procList, my_file)

def read_block_json(filename):
    with open(filename) as fp:
        return json.load(fp)