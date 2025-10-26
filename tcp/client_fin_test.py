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


def test_data_fin(client_seq, server_ip, server_port, local_ip, local_port):
    ret = False
    helper = tcp_test_helper.TCPHelper(server_ip, server_port, local_ip, local_port)

    # 三次握手
    success, server_seq = helper.send_syn_wait_ack(client_seq)
    if not success:
        logging.info("[ERROR] Send SYN failed")
        exit(1)
    
    client_seq += 1
    server_seq += 1
    helper.send_ack(client_seq, server_seq)

    data_helper = tcp_test_helper.TcpTestDataProducer(client_seq)

    send_data = data_helper.make_data(0, len=32)

    # 发送数据和FIN
    helper.send_common(send_data.seq, server_seq, "FA", send_data.payload)
    client_seq += 32 + 1
    
    ret = helper.wait_ack(client_seq, timeout=0.5)
    if not ret:
        logging.info("[ERROR] Send FIN failed")
        exit(1)

    helper.wait_fin(client_seq, server_seq)
    server_seq += 1

    helper.send_ack(client_seq, server_seq)


# 乱序FIN测试
def test_out_order_fin(client_seq, server_ip, server_port, local_ip, local_port):
    ret = False
    helper = tcp_test_helper.TCPHelper(server_ip, server_port, local_ip, local_port)

    # 三次握手
    success, server_seq = helper.send_syn_wait_ack(client_seq)
    if not success:
        logging.info("[ERROR] Send SYN failed")
        exit(1)
    
    client_seq += 1
    server_seq += 1
    helper.send_ack(client_seq, server_seq)

    data_helper = tcp_test_helper.TcpTestDataProducer(client_seq)

    send_data_head = data_helper.make_data(0, end_seq=5)
    send_data_tail = data_helper.make_data(5, end_seq=37)

    # 发送数据和FIN
    helper.send_common(send_data_tail.seq, server_seq, "FA", send_data_tail.payload)
    
    helper.send_data(send_data_head.seq, server_seq, send_data_head.payload)
    client_seq = send_data_tail.end_seq + 1

    ret = helper.wait_ack(client_seq, timeout=0.5)
    if not ret:
        logging.info("[ERROR] Send FIN failed")
        exit(1)

    helper.wait_fin(client_seq, server_seq)
    server_seq += 1

    helper.send_ack(client_seq, server_seq)


# close wait loss fin test 1
def test_close_wait_loss_fin_1(client_seq, server_ip, server_port, local_ip, local_port):
    ret = False
    helper = tcp_test_helper.TCPHelper(server_ip, server_port, local_ip, local_port)

    # 三次握手
    success, server_seq = helper.send_syn_wait_ack(client_seq)
    if not success:
        logging.info("[ERROR] Send SYN failed")
        exit(1)
    
    client_seq += 1
    server_seq += 1
    helper.send_ack(client_seq, server_seq)

    data_helper = tcp_test_helper.TcpTestDataProducer(client_seq)
    send_data = data_helper.make_data(0, len=32)
    # 发送数据和FIN
    helper.send_common(send_data.seq, server_seq, "FA", send_data.payload)

    ret = helper.wait_ack(send_data.end_seq + 1, timeout=0.5)
    if not ret:
        logging.info("[ERROR] Send FIN failed")
        exit(1)

    ret = helper.wait_fin(send_data.end_seq + 1, server_seq, timeout = 2)
    if not ret:
        logging.info(f'[ERROR] Wait FIN failed client:{client_seq} server_seq{server_seq}')
        exit(1)
    
    helper.send_common(send_data.seq, server_seq, "FA", send_data.payload)

    ret = helper.wait_ack(send_data.end_seq + 1, timeout=0.5)
    if not ret:
        logging.info("[ERROR] Send FIN failed")
        exit(1)

    ret = helper.wait_fin(send_data.end_seq + 1, server_seq, timeout = 2)
    if not ret:
        logging.info(f'[ERROR] Wait FIN failed client:{client_seq} server_seq{server_seq}')
        exit(1)
    
    helper.send_common(send_data.seq, server_seq, "FA", send_data.payload)

    ret = helper.wait_ack(send_data.end_seq + 1, timeout=0.5)
    if not ret:
        logging.info("[ERROR] Send FIN failed")
        exit(1)

    ret = helper.wait_fin(send_data.end_seq + 1, server_seq, timeout = 2)
    if not ret:
        logging.info(f'[ERROR] Wait FIN failed client:{client_seq} server_seq{server_seq}')
        exit(1)
    
    
        
    client_seq += send_data.end_seq + 1
    server_seq += 1

    helper.send_ack(client_seq, server_seq)


# close wait loss fin test 1
def test_close_wait_loss_fin_2(client_seq, server_ip, server_port, local_ip, local_port):
    ret = False
    helper = tcp_test_helper.TCPHelper(server_ip, server_port, local_ip, local_port)

    # 三次握手
    success, server_seq = helper.send_syn_wait_ack(client_seq)
    if not success:
        logging.info("[ERROR] Send SYN failed")
        exit(1)
    
    client_seq += 1
    server_seq += 1
    helper.send_ack(client_seq, server_seq)

    data_helper = tcp_test_helper.TcpTestDataProducer(client_seq)
    send_data = data_helper.make_data(0, len=32)
    # 发送数据和FIN
    helper.send_common(send_data.seq, server_seq, "FA", send_data.payload)

    ret = helper.wait_ack(send_data.end_seq + 1, timeout=0.5)
    if not ret:
        logging.info("[ERROR] Send FIN failed")
        exit(1)

    ret = helper.wait_fin(send_data.end_seq + 1, server_seq, timeout = 1)
    if not ret:
        logging.info(f'[ERROR] Wait FIN failed client:{client_seq} server_seq{server_seq}')
        exit(1)
    
    client_seq = send_data.end_seq
    
    # 重复发FIN
    helper.send_fin(client_seq, server_seq)

    ret = helper.wait_ack(client_seq + 1, timeout=0.5)
    if not ret:
        logging.info("[ERROR] Send FIN failed")
        exit(1)

    ret = helper.wait_fin(client_seq + 1, server_seq, timeout = 2)
    if not ret:
        logging.info(f'[ERROR] Wait FIN failed client:{client_seq} server_seq{server_seq}')
        exit(1)


    helper.send_fin(client_seq, server_seq)

    ret = helper.wait_ack(client_seq + 1, timeout=0.5)
    if not ret:
        logging.info("[ERROR] Send FIN failed")
        exit(1)

    ret = helper.wait_fin(client_seq + 1, server_seq, timeout = 4)
    if not ret:
        logging.info(f'[ERROR] Wait FIN failed client:{client_seq} server_seq{server_seq}')
        exit(1)

    server_seq += 1

    helper.send_ack(client_seq, server_seq)


if __name__ == "__main__":
    logging.basicConfig(
        format='%(asctime)s.%(msecs)03d [%(filename)s:%(lineno)d] - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S',
        level=logging.DEBUG
    )
    test_data_fin(random.randint(1000, 1000000), config.TARGET_IP, config.TARGET_PORT, config.LOCAL_IP, random.randint(9000, 65535))
    test_out_order_fin(random.randint(1000, 1000000), config.TARGET_IP, config.TARGET_PORT, config.LOCAL_IP, random.randint(9000, 65535))
    test_close_wait_loss_fin_1(random.randint(1000, 1000000), config.TARGET_IP, config.TARGET_PORT, config.LOCAL_IP, random.randint(9000, 65535))
    test_close_wait_loss_fin_2(random.randint(1000, 1000000), config.TARGET_IP, config.TARGET_PORT, config.LOCAL_IP, random.randint(9000, 65535))

