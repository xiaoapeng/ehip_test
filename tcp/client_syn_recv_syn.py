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


# 注入“未来的” syn (窗口外) 
def test_syn_recv_syn_0(client_seq, server_ip, server_port, local_ip, local_port):
    ret = False
    helper = tcp_test_helper.TCPHelper(server_ip, server_port, local_ip, local_port)

    # 三次握手
    success, server_seq = helper.send_syn_wait_ack(client_seq)
    if not success:
        logging.info("[ERROR] Send SYN failed")
        return False
    
    client_seq += 1
    server_seq += 1

    
    # 注入“未来的” syn (窗口外) 对方会重发 syn 报文
    helper.clean_queue()
    helper.send_common(client_seq+0x20000, server_seq, "S")

    ret = helper.wait_common(expected_ack=client_seq, expected_seq=server_seq-1, flags="SA", timeout=1)
    if not ret:
        logging.info("[ERROR] Wait syn test failed")
        return False

    helper.send_ack(client_seq, server_seq)

    #  发送数据 12345
    helper.send_data(client_seq, server_seq, "12345123451234512345123451234512")
    client_seq += 32

    ret = helper.wait_ack(client_seq, timeout=5)
    if not ret:
        logging.info("[ERROR] Wait ACK failed")
        return False

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



# 注入“当前” syn (窗口外) 
def test_syn_recv_syn_1(client_seq, server_ip, server_port, local_ip, local_port):
    ret = False
    helper = tcp_test_helper.TCPHelper(server_ip, server_port, local_ip, local_port)

    # 三次握手
    success, server_seq = helper.send_syn_wait_ack(client_seq)
    if not success:
        logging.info("[ERROR] Send SYN failed")
        return False
    
    client_seq += 1
    server_seq += 1

    
    # 注入“未来的” syn (窗口外) 对方会 rst+ack
    helper.clean_queue()
    helper.send_common(client_seq, server_seq, "S")

    ret = helper.wait_common(expected_ack=client_seq+1, flags="RA", timeout=1)
    if not ret:
        logging.info("[ERROR] Wait rst test failed")
        return False

    return True


if __name__ == "__main__":
    logging.basicConfig(
        format='%(asctime)s.%(msecs)03d [%(filename)s:%(lineno)d] - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S',
        level=logging.DEBUG
    )
    ret = test_syn_recv_syn_0(random.randint(1000, 1000000), config.TARGET_IP, config.TARGET_PORT, config.LOCAL_IP, random.randint(9000, 65535))
    if not ret:
        logging.error("Test failed")
        exit(1)
    
    ret = test_syn_recv_syn_1(random.randint(1000, 1000000), config.TARGET_IP, config.TARGET_PORT, config.LOCAL_IP, random.randint(9000, 65535))
    if not ret:
        logging.error("Test failed")
        exit(1)