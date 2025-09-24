import time
import random
import tcp_test_helper
import logging

import os
import sys


# 获取当前文件的父目录的绝对路径
parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
# 添加到模块搜索路径
sys.path.append(parent_dir)

import config

def test_established_rto_test(client_seq, server_ip, server_port, local_ip, local_port):
    ret = False
    helper = tcp_test_helper.TCPHelper(server_ip, server_port, local_ip, local_port)

    # 三次握手
    success, server_seq = helper.send_syn_wait_ack(client_seq,1000)
    if not success:
        logging.info("[ERROR] Send SYN failed")
        return False
    
    client_seq += 1
    server_seq += 1
    helper.send_ack(client_seq, server_seq)


    
    data_helper = tcp_test_helper.TcpTestDataProducer(client_seq)

    ds_0 = data_helper.make_data(0, 1200)
    ds_1 = data_helper.make_data(1200, 1200)

    #  发送数据 12345
    logging.info(f'[INFO] Send data:{ds_0.seq}')
    helper.send_common(ds_0.seq, server_seq, "AP", data=ds_0.payload)
    client_seq = ds_0.end_seq

    ret = helper.wait_common(expected_ack=client_seq, expected_seq=server_seq, flags="AP", data_len=ds_0.len, data=ds_0.payload, timeout=1000)
    if not ret:
        logging.info(f'[ERROR] Wait ACK failed client:{client_seq} server_seq{server_seq}')
        return False
    
    server_seq += ds_0.len

    logging.info(f'[INFO] Send data:{ds_1.seq}')
    helper.send_common(ds_1.seq, server_seq, "AP", data=ds_1.payload)
    client_seq = ds_1.end_seq

    ret = helper.wait_common(expected_ack=client_seq, expected_seq=server_seq, flags="AP", data_len=ds_1.len, data=ds_1.payload, timeout=1000)
    if not ret:
        logging.info(f'[ERROR] Wait ACK failed client:{client_seq} server_seq{server_seq}')
        return False
    
    ret = helper.wait_common(expected_ack=client_seq, expected_seq=server_seq, flags="AP", data_len=ds_1.len, data=ds_1.payload, timeout=2000)
    if not ret:
        logging.info(f'[ERROR] Wait ACK failed client:{client_seq} server_seq{server_seq}')
        return False
    
    ret = helper.wait_common(expected_ack=client_seq, expected_seq=server_seq, flags="AP", data_len=ds_1.len, data=ds_1.payload, timeout=4000)
    if not ret:
        logging.info(f'[ERROR] Wait ACK failed client:{client_seq} server_seq{server_seq}')
        return False
    
    ret = helper.wait_common(expected_ack=client_seq, expected_seq=server_seq, flags="AP", data_len=ds_1.len, data=ds_1.payload, timeout=8000)
    if not ret:
        logging.info(f'[ERROR] Wait ACK failed client:{client_seq} server_seq{server_seq}')
        return False
    
    ret = helper.wait_common(expected_ack=client_seq, expected_seq=server_seq, flags="AP", data_len=ds_1.len, data=ds_1.payload, timeout=8000)
    if not ret:
        logging.info(f'[ERROR] Wait ACK failed client:{client_seq} server_seq{server_seq}')
        return False
    
    server_seq += ds_1.len
    helper.send_ack(client_seq, server_seq)

    #  发送FIN
    ret = helper.send_fin_wait_ack(client_seq, server_seq, timeout=0.1)
    if not ret:
        logging.info("[ERROR] Send FIN failed")
        return False
    
    client_seq += 1

    ret = helper.wait_fin(client_seq, server_seq, timeout=0.1)
    if not ret:
        logging.info(f'[ERROR] Wait FIN failed client:{client_seq} server_seq{server_seq}')
        return False

    server_seq += 1
    helper.send_ack(client_seq, server_seq)
    return True



if __name__ == "__main__":
    logging.basicConfig(
        format='%(asctime)s.%(msecs)03d [%(filename)s:%(lineno)d] - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S',
        level=logging.DEBUG
    )

    ret = test_established_rto_test(random.randint(1000, 1000000), config.TARGET_IP, config.TARGET_PORT_ECHO, config.LOCAL_IP, random.randint(9000, 65535))
    if not ret:
        logging.error("Test failed")
        exit(1)
    