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


# ----> fin wait 2 测试
def test_fin_wait_2(client_seq, server_ip, server_port, local_ip, local_port):
    ret = False
    helper = tcp_test_helper.TCPHelper(server_ip, server_port, local_ip, local_port)

    # 三次握手
    success, server_seq = helper.send_syn_wait_ack(client_seq,1000)
    if not success:
        logging.info("[ERROR] Send SYN failed")
        return False
    
    client_seq += 1
    server_seq += 1
    helper.send_ack(client_seq, server_seq)

    # 直接等待FIN
    ret = helper.wait_common(expected_ack=client_seq, expected_seq=server_seq, flags="FA", timeout=5)
    if not ret:
        logging.info("[ERROR] Wait fin test failed")
        return False
    server_seq += 1
    helper.send_ack(client_seq, server_seq)

    ret = helper.send_fin_wait_ack(client_seq, server_seq, timeout=1)
    if not ret:
        logging.info("[ERROR] Send fin wait ack failed")
        return False

    return True

# ----> closing 测试
def test_fin_closing(client_seq, server_ip, server_port, local_ip, local_port):
    ret = False
    helper = tcp_test_helper.TCPHelper(server_ip, server_port, local_ip, local_port)

    # 三次握手
    success, server_seq = helper.send_syn_wait_ack(client_seq,1000)
    if not success:
        logging.info("[ERROR] Send SYN failed")
        return False
    
    client_seq += 1
    server_seq += 1
    helper.send_ack(client_seq, server_seq)

    # 直接等待FIN
    ret = helper.wait_common(expected_ack=client_seq, expected_seq=server_seq, flags="FA", timeout=5)
    if not ret:
        logging.info("[ERROR] Wait fin test failed")
        return False

    ret = helper.send_fin_wait_ack(client_seq, server_seq, timeout=1)
    if not ret:
        logging.info("[ERROR] Send fin wait ack failed")
        return False
    client_seq += 1
    server_seq += 1
    helper.send_ack(client_seq, server_seq)

    return True

# ----> time_wait 测试
def test_fin_time_wait(client_seq, server_ip, server_port, local_ip, local_port):
    ret = False
    helper = tcp_test_helper.TCPHelper(server_ip, server_port, local_ip, local_port)

    # 三次握手
    success, server_seq = helper.send_syn_wait_ack(client_seq,1000)
    if not success:
        logging.info("[ERROR] Send SYN failed")
        return False
    
    client_seq += 1
    server_seq += 1
    helper.send_ack(client_seq, server_seq)

    # 直接等待FIN
    ret = helper.wait_common(expected_ack=client_seq, expected_seq=server_seq, flags="FA", timeout=5)
    if not ret:
        logging.info("[ERROR] Wait fin test failed")
        return False

    server_seq += 1
    ret = helper.send_fin_wait_ack(client_seq, server_seq, timeout=1)
    if not ret:
        logging.info("[ERROR] Send fin wait ack failed")
        return False
    client_seq += 1
    helper.wait_ack(client_seq, server_seq)

    return True




# ----> fin wait 1 丢弃fin 测试
def test_fin_wait_1_lose_fin(client_seq, server_ip, server_port, local_ip, local_port):
    ret = False
    helper = tcp_test_helper.TCPHelper(server_ip, server_port, local_ip, local_port)

    # 三次握手
    success, server_seq = helper.send_syn_wait_ack(client_seq,1000)
    if not success:
        logging.info("[ERROR] Send SYN failed")
        return False
    
    client_seq += 1
    server_seq += 1
    helper.send_ack(client_seq, server_seq)

    # 直接等待FIN
    ret = helper.wait_common(expected_ack=client_seq, expected_seq=server_seq, flags="FA", timeout=1)
    if not ret:
        logging.info("[ERROR] Wait fin test failed")
        return False
    
    
    # 直接等待FIN
    ret = helper.wait_common(expected_ack=client_seq, expected_seq=server_seq, flags="FA", timeout=2)
    if not ret:
        logging.info("[ERROR] Wait fin test failed")
        return False

    # 直接等待FIN
    ret = helper.wait_common(expected_ack=client_seq, expected_seq=server_seq, flags="FA", timeout=4)
    if not ret:
        logging.info("[ERROR] Wait fin test failed")
        return False

    server_seq += 1
    helper.send_ack(client_seq, server_seq)

    ret = helper.send_fin_wait_ack(client_seq, server_seq, timeout=1)
    if not ret:
        logging.info("[ERROR] Send fin wait ack failed")
        return False

    return True

# ----> time_wait 发送FIN 测试
def test_time_wait_send_fin(client_seq, server_ip, server_port, local_ip, local_port):
    ret = False
    helper = tcp_test_helper.TCPHelper(server_ip, server_port, local_ip, local_port)

    # 三次握手
    success, server_seq = helper.send_syn_wait_ack(client_seq,1000)
    if not success:
        logging.info("[ERROR] Send SYN failed")
        return False
    
    client_seq += 1
    server_seq += 1
    helper.send_ack(client_seq, server_seq)

    # 直接等待FIN
    ret = helper.wait_common(expected_ack=client_seq, expected_seq=server_seq, flags="FA", timeout=1)
    if not ret:
        logging.info("[ERROR] Wait fin test failed")
        return False
    
    server_seq += 1
    helper.send_ack(client_seq, server_seq)

    ret = helper.send_fin_wait_ack(client_seq, server_seq, timeout=1)
    if not ret:
        logging.info("[ERROR] Send fin wait ack failed")
        return False
    
    
    ret = helper.send_fin_wait_ack(client_seq, server_seq, timeout=1)
    if not ret:
        logging.info("[ERROR] Send fin wait ack failed")
        return False
    
    
    ret = helper.send_fin_wait_ack(client_seq, server_seq, timeout=1)
    if not ret:
        logging.info("[ERROR] Send fin wait ack failed")
        return False
    
    
    ret = helper.send_fin_wait_ack(client_seq, server_seq, timeout=1)
    if not ret:
        logging.info("[ERROR] Send fin wait ack failed")
        return False
    
    
    ret = helper.send_fin_wait_ack(client_seq, server_seq, timeout=1)
    if not ret:
        logging.info("[ERROR] Send fin wait ack failed")
        return False

    ret = helper.send_fin_wait_ack(client_seq, server_seq, timeout=1)
    if not ret:
        logging.info("[ERROR] Send fin wait ack failed")
        return False
    
    return True


# ----> closing 发送FIN 测试1
def test_fin_closing_send_fin_1(client_seq, server_ip, server_port, local_ip, local_port):
    ret = False
    helper = tcp_test_helper.TCPHelper(server_ip, server_port, local_ip, local_port)

    # 三次握手
    success, server_seq = helper.send_syn_wait_ack(client_seq,1000)
    if not success:
        logging.info("[ERROR] Send SYN failed")
        return False
    
    client_seq += 1
    server_seq += 1
    helper.send_ack(client_seq, server_seq)

    # 直接等待FIN
    ret = helper.wait_common(expected_ack=client_seq, expected_seq=server_seq, flags="FA", timeout=5)
    if not ret:
        logging.info("[ERROR] Wait fin test failed")
        return False

    ret = helper.send_fin_wait_ack(client_seq, server_seq, timeout=1)
    if not ret:
        logging.info("[ERROR] Send fin wait ack failed")
        return False
    
    ret = helper.send_fin_wait_ack(client_seq, server_seq, timeout=1)
    if not ret:
        logging.info("[ERROR] Send fin wait ack failed")
        return False
    
    ret = helper.send_fin_wait_ack(client_seq, server_seq, timeout=1)
    if not ret:
        logging.info("[ERROR] Send fin wait ack failed")
        return False
    
    ret = helper.send_fin_wait_ack(client_seq, server_seq, timeout=1)
    if not ret:
        logging.info("[ERROR] Send fin wait ack failed")
        return False

    client_seq += 1
    server_seq += 1
    helper.send_ack(client_seq, server_seq)

    return True



# ----> closing 发送FIN 测试2
def test_fin_closing_send_fin_2(client_seq, server_ip, server_port, local_ip, local_port):
    ret = False
    helper = tcp_test_helper.TCPHelper(server_ip, server_port, local_ip, local_port)

    # 三次握手
    success, server_seq = helper.send_syn_wait_ack(client_seq,1000)
    if not success:
        logging.info("[ERROR] Send SYN failed")
        return False
    
    client_seq += 1
    server_seq += 1
    helper.send_ack(client_seq, server_seq)

    # 直接等待FIN
    ret = helper.wait_common(expected_ack=client_seq, expected_seq=server_seq, flags="FA", timeout=5)
    if not ret:
        logging.info("[ERROR] Wait fin test failed")
        return False

    ret = helper.send_fin_wait_ack(client_seq, server_seq, timeout=1)
    if not ret:
        logging.info("[ERROR] Send fin wait ack failed")
        return False
    
    ret = helper.send_fin_wait_ack(client_seq, server_seq, timeout=1)
    if not ret:
        logging.info("[ERROR] Send fin wait ack failed")
        return False
    
    ret = helper.send_fin_wait_ack(client_seq, server_seq, timeout=1)
    if not ret:
        logging.info("[ERROR] Send fin wait ack failed")
        return False
    
    server_seq += 1
    ret = helper.send_fin_wait_ack(client_seq, server_seq, timeout=1)
    if not ret:
        logging.info("[ERROR] Send fin wait ack failed")
        return False
    
    ret = helper.send_fin_wait_ack(client_seq, server_seq, timeout=1)
    if not ret:
        logging.info("[ERROR] Send fin wait ack failed")
        return False
    
    ret = helper.send_fin_wait_ack(client_seq, server_seq, timeout=1)
    if not ret:
        logging.info("[ERROR] Send fin wait ack failed")
        return False

    return True

if __name__ == "__main__":
    logging.basicConfig(
        format='%(asctime)s.%(msecs)03d [%(filename)s:%(lineno)d] - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S',
        level=logging.DEBUG
    )

    ret = test_fin_wait_2(random.randint(1000, 1000000), config.TARGET_IP, config.TARGET_FIN, config.LOCAL_IP, random.randint(9000, 65535))
    if not ret:
        logging.error("Test failed")
        exit(1)
    
    ret = test_fin_closing(random.randint(1000, 1000000), config.TARGET_IP, config.TARGET_FIN, config.LOCAL_IP, random.randint(9000, 65535))
    if not ret:
        logging.error("Test failed")
        exit(1)

    ret = test_fin_time_wait(random.randint(1000, 1000000), config.TARGET_IP, config.TARGET_FIN, config.LOCAL_IP, random.randint(9000, 65535))
    if not ret:
        logging.error("Test failed")
        exit(1)
    
    ret = test_fin_wait_1_lose_fin(random.randint(1000, 1000000), config.TARGET_IP, config.TARGET_FIN, config.LOCAL_IP, random.randint(9000, 65535))
    if not ret:
        logging.error("Test failed")
        exit(1)
    
    ret = test_time_wait_send_fin(random.randint(1000, 1000000), config.TARGET_IP, config.TARGET_FIN, config.LOCAL_IP, random.randint(9000, 65535))
    if not ret:
        logging.error("Test failed")
        exit(1)
    
    ret = test_fin_closing_send_fin_1(random.randint(1000, 1000000), config.TARGET_IP, config.TARGET_FIN, config.LOCAL_IP, random.randint(9000, 65535))
    if not ret:
        logging.error("Test failed")
        exit(1)
    
    ret = test_fin_closing_send_fin_2(random.randint(1000, 1000000), config.TARGET_IP, config.TARGET_FIN, config.LOCAL_IP, random.randint(9000, 65535))
    if not ret:
        logging.error("Test failed")
        exit(1)



