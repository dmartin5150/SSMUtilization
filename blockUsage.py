def get_block_usage(procedures, block_start, block_end,room_type,id):
        non_block_time = 0
        block_time = 0
        total_minutes = (block_end - block_start).total_seconds()/60
        for x in range(procedures.shape[0]):
            curRow = procedures.loc[x]
            # if ((block_type == 'ALL') & (id == 430001)):
            #     print('block usage', block_start, block_end, 'proc stat', curRow['local_start_time'], 'proc end', curRow['local_end_time'])
            if ((curRow['local_end_time'] <= block_start) | (curRow['local_start_time'] >= block_end)):
                non_block_time += (curRow['local_end_time'] - curRow['local_start_time']).total_seconds()/60
                continue
            if ((curRow['local_start_time'] >= block_start) & (curRow['local_end_time'] <= block_end)):
                block_time += (curRow['local_end_time'] - curRow['local_start_time']).total_seconds()/60
                continue
            if ((curRow['local_start_time'] < block_start) & (curRow['local_end_time'] > block_end)):
                block_time += (block_end - block_start).total_seconds()/60
                non_block_time += (block_start - curRow['local_start_time']).total_seconds()/60
                non_block_time += (curRow['local_end_time'] - block_end).total_seconds()/60
                continue
            if ((curRow['local_start_time'] == block_start) & (curRow['local_end_time'] > block_end)):
                block_time += (block_end - block_start).total_seconds()/60
                non_block_time += (curRow['local_end_time'] - block_end).total_seconds()/60
                continue
            if ((curRow['local_start_time'] <block_start) & (curRow['local_end_time'] == block_end)):
                block_time += (block_end - block_start).total_seconds()/60
                non_block_time += (block_start-curRow['local_start_time']).total_seconds()/60
                continue
            if((curRow['local_start_time'] < block_start) & (curRow['local_end_time'] < block_end)):
                block_time += (curRow['local_end_time'] - block_start).total_seconds()/60
                non_block_time += (block_start - curRow['local_start_time']).total_seconds()/60
                continue
            if((curRow['local_start_time'] > block_start) & (curRow['local_end_time'] > block_end)):
                block_time += (block_end - curRow['local_start_time']).total_seconds()/60 
                non_block_time += (curRow['local_end_time'] - block_end).total_seconds()/60
                continue
        return  block_time, non_block_time, total_minutes