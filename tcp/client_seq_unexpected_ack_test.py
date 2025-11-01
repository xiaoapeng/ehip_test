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


# 在 recv状态收到非预期的seq
def test_syn_recv_unexpected_seq_test(client_seq, server_ip, server_port, local_ip, local_port):
    ret = False
    helper = tcp_test_helper.TCPHelper(server_ip, server_port, local_ip, local_port)

    # 三次握手
    success, server_seq = helper.send_syn_wait_ack(client_seq)
    if not success:
        logging.info("[ERROR] Send SYN failed")
        return False
    
    client_seq += 1
    server_seq += 1
    helper.clean_queue()
    helper.send_ack(client_seq-1, server_seq)

    ret = helper.wait_ack(client_seq, timeout=2)
    if not ret:
        logging.info("[ERROR] Wait ACK failed")
        return False

    #  发送FIN
    ret = helper.send_fin_wait_ack(client_seq, server_seq, timeout=0.1)
    if not ret:
        logging.info("[ERROR] Send FIN failed")
        return False
    
    client_seq += 1
    # 等待FIN
    ret = helper.wait_fin(client_seq, server_seq, timeout=0.5)
    if not ret:
        logging.info("[ERROR] Wait FIN failed")
        return False

    server_seq += 1
    helper.send_ack(client_seq, server_seq)
    return True


# 在 recv状态收到非预期的seq
def test_established_unexpected_seq_test(client_seq, server_ip, server_port, local_ip, local_port):
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
    helper.clean_queue()
    helper.send_ack(client_seq-1, server_seq)

    ret = helper.wait_ack(client_seq, timeout=2)
    if not ret:
        logging.info("[ERROR] Wait ACK failed")
        return False

    #  发送FIN
    ret = helper.send_fin_wait_ack(client_seq, server_seq, timeout=0.1)
    if not ret:
        logging.info("[ERROR] Send FIN failed")
        return False
    
    client_seq += 1
    # 等待FIN
    ret = helper.wait_fin(client_seq, server_seq, timeout=0.5)
    if not ret:
        logging.info("[ERROR] Wait FIN failed")
        return False

    server_seq += 1
    helper.send_ack(client_seq, server_seq)
    return True

def test_fin_wait1_unexpected_seq_test(client_seq, server_ip, server_port, local_ip, local_port):
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

    # 等待FIN
    ret = helper.wait_fin(client_seq, server_seq, timeout=0.5)
    if not ret:
        logging.info("[ERROR] Wait FIN failed")
        return False

    server_seq += 1
    helper.send_ack(client_seq-1, server_seq)
    
    ret = helper.wait_ack(client_seq, timeout=2)
    if not ret:
        logging.info("[ERROR] Wait ACK failed")
        return False
    
    ret = helper.send_fin_wait_ack(client_seq, server_seq, 2)
    if not ret:
        logging.info("[ERROR] Send FIN failed")
        return False
    
    return True


def test_time_wait_unexpected_seq_test(client_seq, server_ip, server_port, local_ip, local_port):
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

    # 等待FIN
    ret = helper.wait_fin(client_seq, server_seq, timeout=0.5)
    if not ret:
        logging.info("[ERROR] Wait FIN failed")
        return False

    server_seq += 1
    helper.send_ack(client_seq, server_seq)
    
    ret = helper.send_fin_wait_ack(client_seq, server_seq, 2)
    if not ret:
        logging.info("[ERROR] Send FIN failed")
        return False
    client_seq += 1

    # time wait 2MSL
    helper.clean_queue()
    helper.send_ack(client_seq-1, server_seq)
    ret = helper.wait_ack(client_seq, timeout=4)
    if not ret:
        logging.info("[ERROR] Wait ACK failed")
        return False



    return True


# 对面需要配置 # keepalive_time = 8S  keepalive_intvl = 4S keepalive_probes = 4
if __name__ == "__main__":
    logging.basicConfig(
        format='%(asctime)s.%(msecs)03d [%(filename)s:%(lineno)d] - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S',
        level=logging.DEBUG
    )
    test_syn_recv_unexpected_seq_test(random.randint(1000, 1000000), config.TARGET_IP, config.TARGET_ALIVE_TEST, config.LOCAL_IP, random.randint(9000, 65535))
    test_fin_wait1_unexpected_seq_test(random.randint(1000, 1000000), config.TARGET_IP, config.TARGET_FIN, config.LOCAL_IP, random.randint(9000, 65535))
    test_time_wait_unexpected_seq_test(random.randint(1000, 1000000), config.TARGET_IP, config.TARGET_FIN, config.LOCAL_IP, random.randint(9000, 65535))

