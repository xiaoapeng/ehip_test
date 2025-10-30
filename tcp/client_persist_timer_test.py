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


def test_persist_timer_test(client_seq, server_ip, server_port, local_ip, local_port):
    ret = False
    helper = tcp_test_helper.TCPHelper(server_ip, server_port, local_ip, local_port, rx_window=1024)  # 设置一个很小的接收窗口

    # 三次握手
    success, server_seq = helper.send_syn_wait_ack(client_seq)
    if not success:
        logging.info("[ERROR] Send SYN failed")
        return False
    
    client_seq += 1
    server_seq += 1
    helper.send_ack(client_seq, server_seq)

    # 发送一些数据
    tcp_data_prodicer = tcp_test_helper.TcpTestDataProducer(client_seq)
    test_data0 = tcp_data_prodicer.make_data(0, 1024)
    test_data1 = tcp_data_prodicer.make_data(1024, 1024)

    helper.send_common(test_data0.seq, server_seq, "PA", test_data0.payload)
    client_seq = test_data0.end_seq

    ret = helper.wait_common(expected_ack=client_seq, expected_seq=server_seq, flags="A", data = test_data0.payload, timeout=2 )
    if not ret:
        logging.info("[ERROR] Wait ACK for data failed")
        return False
    logging.info("[INFO] Receive ACK for data")

    server_seq += test_data0.len

    
    # 回复0窗口 ACK
    helper.send_common(test_data1.seq, server_seq, "PA", data = test_data1.payload, rx_window=0 )
    client_seq = test_data1.end_seq

    # 此时应该先收到一个ACK
    ret = helper.wait_common(expected_ack=client_seq, expected_seq=server_seq, flags="A", timeout=1)
    if not ret:
        logging.info("[ERROR] Wait ACK for zero window data failed")
        return False

    # 准备接收0窗口探测报文
    ret = helper.wait_common(expected_ack=client_seq, expected_seq=server_seq, flags="A", data_len = 1, timeout=4.1)
    if not ret:
        logging.info("[ERROR] Wait Detect for zero window data failed")
        return False
    helper.send_common(client_seq, server_seq,"A",rx_window=0)

    # 准备接收0窗口探测报文
    ret = helper.wait_common(expected_ack=client_seq, expected_seq=server_seq, flags="A", data_len = 1, timeout=8.1)
    if not ret:
        logging.info("[ERROR] Wait Detect for zero window data failed")
        return False
    helper.send_common(client_seq, server_seq,"A",rx_window=0)

    # 准备接收0窗口探测报文
    ret = helper.wait_common(expected_ack=client_seq, expected_seq=server_seq, flags="A", data_len = 1, timeout=16.1)
    if not ret:
        logging.info("[ERROR] Wait Detect for zero window data failed")
        return False
    server_seq += 1
    helper.send_common(client_seq, server_seq,"A")

    ret = helper.wait_common(expected_ack=client_seq, expected_seq=server_seq, flags="A", data_len=test_data1.len-1)
    if not ret:
        logging.info("[ERROR] Wait data failed")
        return False
    server_seq += test_data1.len-1
    helper.send_common(client_seq, server_seq,"A")

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

# 对面需要配置 # keepalive_time = 8S  keepalive_intvl = 4S keepalive_probes = 4
if __name__ == "__main__":
    logging.basicConfig(
        format='%(asctime)s.%(msecs)03d [%(filename)s:%(lineno)d] - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S',
        level=logging.DEBUG
    )
    test_persist_timer_test(random.randint(1000, 1000000), config.TARGET_IP, config.TARGET_PORT_ECHO, config.LOCAL_IP, random.randint(9000, 65535))

