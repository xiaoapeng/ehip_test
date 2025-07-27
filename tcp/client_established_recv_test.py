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


# 接收5字节的数据，然后进行ACK
def test_established_recv_test_0(client_seq, server_ip, server_port, local_ip, local_port):
    ret = False
    helper = tcp_test_helper.TCPHelper(server_ip, server_port, local_ip, local_port)

    # 三次握手
    success, server_seq = helper.send_syn_wait_ack(client_seq)
    if not success:
        logging.info("[ERROR] Send SYN failed")
        return False
    
    client_seq += 1
    server_seq += 1
    helper.send_ack(client_seq, server_seq)

    # 接收5个字节的数据
    ret = helper.wait_common(expected_ack=client_seq, expected_seq=server_seq, data_len=5, timeout=20)
    if not ret:
        logging.info("[ERROR] Wait data failed")
        return False
    server_seq += 5

    helper.send_ack(client_seq, server_seq)

    ret = helper.send_fin_wait_ack(client_seq, server_seq, timeout=0.5)
    if not ret:
        logging.info(f'[ERROR] Send FIN failed client:{client_seq} server_seq:{server_seq}')
        return False
    client_seq += 1
    # 等待FIN
    ret = helper.wait_fin(client_seq, server_seq, timeout=0.5)
    if not ret:
        logging.info(f'[ERROR] Wait FIN failed client:{client_seq} server_seq:{server_seq}')
        return False

    server_seq += 1
    helper.send_ack(client_seq, server_seq)
    return True


# 接收5字节的数据，然后进行ACK ACK的seq在窗口外
def test_established_recv_test_1(client_seq, server_ip, server_port, local_ip, local_port):
    ret = False
    helper = tcp_test_helper.TCPHelper(server_ip, server_port, local_ip, local_port)

    # 三次握手
    success, server_seq = helper.send_syn_wait_ack(client_seq)
    if not success:
        logging.info("[ERROR] Send SYN failed")
        return False
    
    client_seq += 1
    server_seq += 1
    helper.send_ack(client_seq, server_seq)

    # 接收5个字节的数据
    ret = helper.wait_common(expected_ack=client_seq, expected_seq=server_seq, data_len=5, timeout=20)
    if not ret:
        logging.info("[ERROR] Wait data failed")
        return False
    
    helper.clean_queue()

    # 窗口外ACK
    helper.send_ack(client_seq - 100, server_seq + 5+1)

    # 接收重发的报文
    ret = helper.wait_common(expected_ack=client_seq, expected_seq=server_seq, data_len=5, timeout=5)
    if not ret:
        logging.info("[ERROR] Wait data failed")
        return False
    
    # 正常ACk
    helper.send_ack(client_seq, server_seq + 5)
    server_seq += 5


    ret = helper.send_fin_wait_ack(client_seq, server_seq, timeout=0.5)
    if not ret:
        logging.info(f'[ERROR] Send FIN failed client:{client_seq} server_seq:{server_seq}')
        return False
    client_seq += 1
    # 等待FIN
    ret = helper.wait_fin(client_seq, server_seq, timeout=0.5)
    if not ret:
        logging.info(f'[ERROR] Wait FIN failed client:{client_seq} server_seq:{server_seq}')
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

    ret = test_established_recv_test_0(random.randint(1000, 1000000), config.TARGET_IP, config.TARGET_PORT, config.LOCAL_IP, random.randint(9000, 65535))
    if not ret:
        logging.error("Test failed")
        exit(1)
    ret = test_established_recv_test_1(random.randint(1000, 1000000), config.TARGET_IP, config.TARGET_PORT, config.LOCAL_IP, random.randint(9000, 65535))
    if not ret:
        logging.error("Test failed")
        exit(1)

    