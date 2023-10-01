def get_all_block_procedures(procedure_data,npis,block_date):
    return procedure_data[(procedure_data['NPI'].isin(npis)) & 
                          (procedure_data['procedureDtNoTime'] == block_date)].sort_values(by=['local_start_time'])

def get_in_room_block_procedures(procedure_data,npis,block_date,room):
    return procedure_data[(procedure_data['NPI'].isin(npis)) & 
                          ((procedure_data['procedureDtNoTime'] == block_date)) & 
                          (procedure_data['room'] == room)].sort_values(by=['local_start_time'])  
                                                                                                                                                        
def get_out_room_block_procedures(procedure_data,npis,block_date,room):
    return procedure_data[(procedure_data['NPI'].isin(npis)) & 
                          (procedure_data['procedureDtNoTime'] == block_date) &
                          (procedure_data['room'] != room) ].sort_values(by=['local_start_time'])  