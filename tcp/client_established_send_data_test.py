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


if __name__ == "__main__":
    logging.basicConfig(
        format='%(asctime)s.%(msecs)03d [%(filename)s:%(lineno)d] - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S',
        level=logging.DEBUG
    )
    # 获取本地IP和随机端口
    client_seq = random.randint(1000, 1000000)
    ret = False
    helper = tcp_test_helper.TCPHelper(config.TARGET_IP, config.TARGET_PORT, config.LOCAL_IP)

    # 三次握手
    success, server_seq = helper.send_syn_wait_ack(client_seq)
    if not success:
        logging.info("[ERROR] Send SYN failed")
        exit(1)
    
    client_seq += 1
    server_seq += 1
    helper.send_ack(client_seq, server_seq)

    #  发送数据 "12345123451234512345123451234512"
    helper.send_data(client_seq, server_seq, "12345123451234512345123451234512")
    client_seq += 32

    ret = helper.wait_ack(client_seq, timeout=0.5)
    if not ret:
        logging.info("[ERROR] Wait ACK failed")
        exit(1)
    
    #  发送数据 不带ACK 发送 "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
    helper.send_common(client_seq, server_seq, "P", "ABCDEFGHIJKLMNOPQRSTUVWXYZ")

    ret = helper.wait_ack(client_seq + 26, timeout=0.5)
    if ret:
        logging.info("[ERROR] Wait ACK ok")
        exit(1)


    helper.clean_queue()

    #  发送数据 ACK在窗口外 发送 "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
    helper.send_common(client_seq, server_seq - 10, "PA", "ABCDEFGHIJKLMNOPQRSTUVWXYZ")

    ret = helper.wait_ack(client_seq + 26, timeout=0.5)
    if not ret:
        logging.info("[ERROR] Wait ACK failed")
        exit(1)
    client_seq += 26

    #  发送FIN
    ret = helper.send_fin_wait_ack(client_seq, server_seq, timeout=0.1)
    if not ret:
        logging.info("[ERROR] Send FIN failed")
        exit(1)
    
    client_seq += 1

    ret = helper.wait_fin(client_seq, server_seq, timeout=0.1)
    if not ret:
        logging.info(f'[ERROR] Wait FIN failed client:{client_seq} server_seq{server_seq}')
        exit(1)

    server_seq += 1
    helper.send_ack(client_seq, server_seq)