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
    # helper.send_data(client_seq, server_seq, "12345123451234512345123451234512")
    # client_seq += 32

    # ret = helper.wait_ack(client_seq, timeout=0.5)
    # if not ret:
    #     logging.info("[ERROR] Wait ACK failed")
    #     exit(1)

    # # 注入“未来的” rst  被测设备会重发 ACk
    # helper.send_common(client_seq+4, server_seq, "R")

    # # 此时应该重发ACK
    # ret = helper.wait_ack(client_seq, timeout=0.5)
    # if not ret:
    #     logging.info("[ERROR] rst 0 Wait ACK failed")
    #     exit(1)

    # 注入“未来的” rst (窗口外) 会被被测设备忽略
    helper.clean_queue()
    helper.send_common(client_seq+0x20000, server_seq, "R")

    ret = helper.wait_ack(client_seq, timeout=0.5)
    if ret:
        logging.info("[ERROR] rst 0 Wait ACK ok")
        exit(1)


    # 注入“过去的” rst  会被被测设备忽略
    helper.send_common(client_seq-4, server_seq, "R")

    helper.send_data(client_seq, server_seq, "12345123451234512345123451234512")
    client_seq += 32

    ret = helper.wait_ack(client_seq, timeout=0.5)
    if not ret:
        logging.info("[ERROR] rst 1 Wait ACK failed")
        exit(1)



    # 注入真实的 rst   等不来ACK 发送数据也等不到ACK
    helper.send_common(client_seq, server_seq, "R")
    client_seq += 1
    ret = helper.wait_ack(client_seq, timeout=0.5)
    if ret:
        logging.info("[ERROR] rst 2 Wait ACK ok")
        exit(1)
    
    helper.send_data(client_seq, server_seq, "12345123451234512345123451234512")
    client_seq += 32

    ret = helper.wait_ack(client_seq, timeout=0.5)
    if ret:
        logging.info("[ERROR] rst 2 Wait ACK ok")
        exit(1)

