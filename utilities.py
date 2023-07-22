from datetime import  datetime;

def get_procedure_date(dt):
    return datetime.strptime(dt, '%Y-%m-%d')