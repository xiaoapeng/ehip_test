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


def test_alive_recv(client_seq, server_ip, server_port, local_ip, local_port):
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

    # 等待第一个Alive包
    ret = helper.wait_common(expected_ack=client_seq, expected_seq=server_seq-1, flags="A", data_len=1, timeout=8.1)
    if not ret:
        logging.info("[ERROR] Wait alive packet failed")
        return False
    logging.info("[INFO] Receive first alive packet")
    helper.send_common(client_seq, server_seq, "A")

    
    # 等待第二个Alive包
    ret = helper.wait_common(expected_ack=client_seq, expected_seq=server_seq-1, flags="A", data_len=1, timeout=8.1)
    if not ret:
        logging.info("[ERROR] Wait alive packet failed")
        return False
    logging.info("[INFO] Receive second alive packet")
    helper.send_common(client_seq, server_seq, "A")

    
    # 等待第三个Alive包
    ret = helper.wait_common(expected_ack=client_seq, expected_seq=server_seq-1, flags="A", data_len=1, timeout=8.1)
    if not ret:
        logging.info("[ERROR] Wait alive packet failed")
        return False
    logging.info("[INFO] Receive third alive packet")
    #helper.send_common(client_seq, server_seq, "A")

    # 等待第4个Alive包
    ret = helper.wait_common(expected_ack=client_seq, expected_seq=server_seq-1, flags="A", data_len=1, timeout=8.1)
    if not ret:
        logging.info("[ERROR] Wait alive packet failed")
        return False
    logging.info("[INFO] Receive fourth alive packet")

    
    # 等待第5个Alive包
    ret = helper.wait_common(expected_ack=client_seq, expected_seq=server_seq-1, flags="A", data_len=1, timeout=4.1)
    if not ret:
        logging.info("[ERROR] Wait alive packet failed")
        return False
    logging.info("[INFO] Receive fifth alive packet")

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


def test_alive_recv_timeout(client_seq, server_ip, server_port, local_ip, local_port):
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

    # 等待第一个Alive包
    ret = helper.wait_common(expected_ack=client_seq, expected_seq=server_seq-1, flags="A", data_len=1, timeout=8.1)
    if not ret:
        logging.info("[ERROR] Wait alive packet failed")
        return False
    logging.info("[INFO] Receive first alive packet")
    helper.send_common(client_seq, server_seq, "A")

    
    # 等待第二个Alive包
    ret = helper.wait_common(expected_ack=client_seq, expected_seq=server_seq-1, flags="A", data_len=1, timeout=8.1)
    if not ret:
        logging.info("[ERROR] Wait alive packet failed")
        return False
    logging.info("[INFO] Receive second alive packet")
    helper.send_common(client_seq, server_seq, "A")

    
    # 等待第三个Alive包
    ret = helper.wait_common(expected_ack=client_seq, expected_seq=server_seq-1, flags="A", data_len=1, timeout=8.1)
    if not ret:
        logging.info("[ERROR] Wait alive packet failed")
        return False
    logging.info("[INFO] Receive third alive packet")
    #helper.send_common(client_seq, server_seq, "A")

    # 等待 timeout 2 个Alive包
    ret = helper.wait_common(expected_ack=client_seq, expected_seq=server_seq-1, flags="A", data_len=1, timeout=8.1)
    if not ret:
        logging.info("[ERROR] Wait alive packet failed")
        return False
    logging.info("[INFO] Receive timeout 2 alive packet")

    
    # 等待 timeout 3 个Alive包
    ret = helper.wait_common(expected_ack=client_seq, expected_seq=server_seq-1, flags="A", data_len=1, timeout=4.1)
    if not ret:
        logging.info("[ERROR] Wait alive packet failed")
        return False
    logging.info("[INFO] Receive timeout 3 alive packet")

    # 等待 timeout 4 个Alive包
    ret = helper.wait_common(expected_ack=client_seq, expected_seq=server_seq-1, flags="A", data_len=1, timeout=4.1)
    if not ret:
        logging.info("[ERROR] Wait alive packet failed")
        return False
    logging.info("[INFO] Receive timeout 4 alive packet")

    # 等待 timeout 5 个Alive包 (应该等不到)
    ret = helper.wait_common(expected_ack=client_seq, expected_seq=server_seq-1, flags="A", data_len=1, timeout=4.1)
    if ret:
        logging.info("[ERROR] Wait alive packet successed unexpected")
        return False
    return True

def test_windows_ack(client_seq, server_ip, server_port, local_ip, local_port):
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

    data_producer =  tcp_test_helper.TcpTestDataProducer(client_seq)
    send_data = data_producer.make_data(0, len=100)

    helper.send_common(send_data.seq, server_seq, "PA", send_data.payload)
    client_seq = send_data.end_seq

    ret = helper.wait_ack(client_seq, timeout=2)
    if not ret:
        logging.info("[ERROR] Wait ACK failed")
        return False
    
    # 发送一个 alive 包
    helper.send_common(client_seq-1, server_seq, "A")
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

# 对面需要配置 # keepalive_time = 8S  keepalive_intvl = 4S keepalive_probes = 4
if __name__ == "__main__":
    logging.basicConfig(
        format='%(asctime)s.%(msecs)03d [%(filename)s:%(lineno)d] - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S',
        level=logging.DEBUG
    )
    test_alive_recv(random.randint(1000, 1000000), config.TARGET_IP, config.TARGET_ALIVE_TEST, config.LOCAL_IP, random.randint(9000, 65535))
    test_alive_recv_timeout(random.randint(1000, 1000000), config.TARGET_IP, config.TARGET_ALIVE_TEST, config.LOCAL_IP, random.randint(9000, 65535))

