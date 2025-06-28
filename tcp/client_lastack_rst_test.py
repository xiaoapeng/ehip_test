#!/usr/bin/env python3
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

# 在 lastack状态下发送未来rst的测试 注入“未来的” rst (窗口外) 
def test_lastack_out_of_window_rst_0(client_seq, server_ip, server_port, local_ip, local_port):
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

    # 此时 server 已经进入了LAST-ACK

    # 注入RST报文进行干扰
    # 注入“未来的” rst (窗口外) 会被被测设备忽略
    helper.clean_queue()
    helper.send_common(client_seq+0x20000, server_seq, "R")
    
    
    # 等待FIN重传
    ret = helper.wait_fin(client_seq, server_seq, timeout=1)
    if not ret:
        logging.info(f'[ERROR] Wait FIN failed client:{client_seq} server_seq{server_seq}')
        return False

    server_seq += 1
    helper.send_ack(client_seq, server_seq)
    return True

# 在 lastack状态下发送未来rst的测试 注入“过去的” rst (窗口外) 
def test_lastack_out_of_window_rst_1(client_seq, server_ip, server_port, local_ip, local_port):
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

    # 此时 server 已经进入了LAST-ACK

    # 注入RST报文进行干扰
    # 注入“过去的” rst (窗口外) 会被被测设备忽略
    helper.clean_queue()
    helper.send_common(client_seq-0x200, server_seq, "R")
    
    
    # 等待FIN重传
    ret = helper.wait_fin(client_seq, server_seq, timeout=1)
    if not ret:
        logging.info(f'[ERROR] Wait FIN failed client:{client_seq} server_seq{server_seq}')
        return False

    server_seq += 1
    helper.send_ack(client_seq, server_seq)
    return True


# 在 lastack状态下发送未来rst的测试 (窗口内，但不是nxt_seq) 
def test_lastack_rst_2(client_seq, server_ip, server_port, local_ip, local_port):
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

    # 此时 server 已经进入了LAST-ACK

    # 注入RST报文进行干扰
    # 注入rst (窗口内) 
    helper.clean_queue()
    helper.send_common(client_seq+5, server_seq, "R")
    
    ret = helper.wait_ack(client_seq, timeout=0.5)
    if not ret:
        logging.info("[ERROR] Wait FIN ACK failed")
        return False

    # 等待FIN重传
    ret = helper.wait_fin(client_seq, server_seq, timeout=1)
    if not ret:
        logging.info(f'[ERROR] Wait FIN failed client:{client_seq} server_seq{server_seq}')
        return False

    server_seq += 1
    helper.send_ack(client_seq, server_seq)
    return True


# 在 lastack状态下发送未来rst的测试 (窗口内，但不是nxt_seq) 
def test_lastack_rst_3(client_seq, server_ip, server_port, local_ip, local_port):
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

    # 此时 server 已经进入了LAST-ACK

    # 注入RST报文进行干扰
    # 注入rst (窗口内) 
    helper.clean_queue()
    helper.send_common(client_seq, server_seq, "R")
    
    ret = helper.wait_ack(client_seq, timeout=0.5)
    if ret:
        logging.info("[ERROR] Wait FIN ACK OK")
        return False

    return True


if __name__ == "__main__":
    logging.basicConfig(
        format='%(asctime)s.%(msecs)03d [%(filename)s:%(lineno)d] - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S',
        level=logging.DEBUG
    )
    ret = False
    # 获取本地IP和随机端口
    ret = test_lastack_out_of_window_rst_0(random.randint(1000, 1000000), config.TARGET_IP, config.TARGET_PORT, config.LOCAL_IP, random.randint(9000, 65535))
    if not ret:
        logging.error("test_lastack_out_of_window_rst_0 Test failed.")
        exit(1)
    
    ret = test_lastack_out_of_window_rst_1(random.randint(1000, 1000000), config.TARGET_IP, config.TARGET_PORT, config.LOCAL_IP, random.randint(9000, 65535))
    if not ret:
        logging.error("test_lastack_out_of_window_rst_1 Test failed.")
        exit(1)
    
    ret = test_lastack_rst_2(random.randint(1000, 1000000), config.TARGET_IP, config.TARGET_PORT, config.LOCAL_IP, random.randint(9000, 65535))
    if not ret:
        logging.error("test_alstack_rst_2 Test failed.")
        exit(1)
    
    ret = test_lastack_rst_3(random.randint(1000, 1000000), config.TARGET_IP, config.TARGET_PORT, config.LOCAL_IP, random.randint(9000, 65535))
    if not ret:
        logging.error("test_lastack_rst_3 Test failed.")
        exit(1)


