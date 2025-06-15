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

    #  发送数据 12345
    helper.send_data(client_seq, server_seq, "12345123451234512345123451234512")
    client_seq += 32

    ret = helper.wait_ack(client_seq, timeout=5)
    if not ret:
        logging.info("[ERROR] Wait ACK failed")
        exit(1)

    #  发送数据 12345
    helper.send_data(client_seq, server_seq, "ZZZZZ1234512345123451234512TTTTT")
    client_seq += 32


    helper.clean_queue()
    # 发送一个迷惑的 syn 包
    helper.send_common(client_seq + 544444, server_seq, "S")

    ret = helper.wait_ack(client_seq, timeout=5)
    if not ret:
        logging.info("[ERROR] Wait syn test ACK failed")
        exit(1)


    
    helper.clean_queue()
    # 发送一个迷惑的 syn 包
    helper.send_common(abs(client_seq - 544444), server_seq, "S")

    ret = helper.wait_ack(client_seq, timeout=5)
    if not ret:
        logging.info("[ERROR] Wait syn test ACK failed")
        exit(1)

    # 发送一个正常的 syn 包 会被rst
    helper.clean_queue()
    helper.send_common(client_seq, server_seq, "S")
    ret = helper.wait_common(expected_ack=client_seq + 1, flags="RA", timeout=0.5)
    if not ret:
        logging.info("[ERROR] Wait syn test ACK failed")
        exit(1)

