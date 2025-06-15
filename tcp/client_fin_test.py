import time
import random
import os
import tcp_test_helper
import logging


# 配置目标信息
TARGET_IP = "192.168.12.12"
TARGET_PORT = 7777
LOCAL_IP = "192.168.12.7"

if __name__ == "__main__":
    logging.basicConfig(
        format='%(asctime)s.%(msecs)03d [%(filename)s:%(lineno)d] - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S',
        level=logging.DEBUG
    )
    # 获取本地IP和随机端口
    client_seq = random.randint(1000, 1000000)
    ret = False
    helper = tcp_test_helper.TCPHelper(TARGET_IP, TARGET_PORT, LOCAL_IP)

    # 三次握手
    success, server_seq = helper.send_syn_wait_ack(client_seq)
    if not success:
        logging.info("[ERROR] Send SYN failed")
        exit(1)
    
    client_seq += 1
    server_seq += 1
    helper.send_ack(client_seq, server_seq)


    # 发送数据和FIN
    helper.send_common(client_seq, server_seq, "FA", "CCCCC1234512345123451234512FFFFF")
    client_seq += 32 + 1
    
    ret = helper.wait_ack(client_seq, timeout=0.5)
    if not ret:
        logging.info("[ERROR] Send FIN failed")
        exit(1)

    helper.wait_fin(client_seq, server_seq)
    server_seq += 1

    helper.send_ack(client_seq, server_seq)


    ###################  乱序 FIN测试  ###################

    
    # 获取本地IP和随机端口
    client_seq = random.randint(1000, 1000000)
    ret = False
    helper = tcp_test_helper.TCPHelper(TARGET_IP, TARGET_PORT, LOCAL_IP)

    # 三次握手
    success, server_seq = helper.send_syn_wait_ack(client_seq)
    if not success:
        logging.info("[ERROR] Send SYN failed")
        exit(1)
    
    client_seq += 1
    server_seq += 1
    helper.send_ack(client_seq, server_seq)


    # 发送数据和FIN
    helper.send_common(client_seq + 5, server_seq, "FA", "CCCCC1234512345123451234512FFFFF")
    
    helper.send_data(client_seq, server_seq, "12345")
    client_seq += 32 + 1 + 5

    ret = helper.wait_ack(client_seq, timeout=0.5)
    if not ret:
        logging.info("[ERROR] Send FIN failed")
        exit(1)

    helper.wait_fin(client_seq, server_seq)
    server_seq += 1

    helper.send_ack(client_seq, server_seq)


