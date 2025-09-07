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


# fin分片测试，fin先到，然后再发送数据
def test_established_fragment_0(client_seq, server_ip, server_port, local_ip, local_port):
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


    
    data_helper = tcp_test_helper.TcpTestDataProducer(client_seq)

    ds_0 = data_helper.make_data(0, end_seq=100)

    # 发送未来的FIN
    helper.send_common(ds_0.end_seq, server_seq, "FA")

    # 会收到一个重复ACK
    ret = helper.wait_ack(client_seq, timeout=1000)
    if not ret:
        logging.info("[ERROR] Wait ACK failed")
        return False


    #  发送数据 12345
    helper.send_data(ds_0.seq, server_seq, ds_0.payload)

    # 之前的FIN会合并
    client_seq = ds_0.end_seq + 1

    ret = helper.wait_ack(client_seq, timeout=1000)
    if not ret:
        logging.info("[ERROR] Wait ACK failed")
        return False
    
    # 等待FIN
    ret = helper.wait_fin(client_seq, server_seq, timeout=1000)
    if not ret:
        logging.info(f'[ERROR] Wait FIN failed client:{client_seq} server_seq{server_seq}')
        return False

    server_seq += 1
    helper.send_ack(client_seq, server_seq)
    return True


# 发送乱序数据测试，
def test_established_fragment_1(client_seq, server_ip, server_port, local_ip, local_port):
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

    data_helper = tcp_test_helper.TcpTestDataProducer(client_seq)

    #  [0-100] [100-200] 
    ds_0 = data_helper.make_data(0, end_seq=100)
    ds_1 = data_helper.make_data(100, end_seq=200)

    #  发送数据 12345
    helper.send_data(ds_1.seq, server_seq, ds_1.payload)

    ret = helper.wait_ack(client_seq, timeout=0.5)
    if not ret:
        logging.info("[ERROR] Wait ACK failed")
        return False
    
    helper.send_data(ds_0.seq, server_seq, ds_0.payload)

    client_seq = ds_1.end_seq

    ret = helper.wait_ack(client_seq, timeout=0.5)
    if not ret:
        logging.info("[ERROR] Wait ACK failed")
        return False

    ret = helper.send_fin_wait_ack(client_seq, server_seq, timeout=0.5)
    if not ret:
        logging.info("[ERROR] Send FIN failed")
        return False
    client_seq += 1

    # 等待FIN
    ret = helper.wait_fin(client_seq, server_seq, timeout=0.5)
    if not ret:
        logging.info(f'[ERROR] Wait FIN failed client:{client_seq} server_seq{server_seq}')
        return False

    server_seq += 1
    helper.send_ack(client_seq, server_seq)
    return True


# 发送乱序数据测试，
def test_established_fragment_2(client_seq, server_ip, server_port, local_ip, local_port):
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

    data_helper = tcp_test_helper.TcpTestDataProducer(client_seq)

    #  [0-100] [100-200] 
    ds_0 = data_helper.make_data(0, end_seq=100)
    ds_1 = data_helper.make_data(100, end_seq=200)
    ds_2 = data_helper.make_data(200, end_seq=300)
    ds_3 = data_helper.make_data(300, end_seq=400)
    ds_4 = data_helper.make_data(400, end_seq=500)
    ds_5 = data_helper.make_data(500, end_seq=600)
    ds_6 = data_helper.make_data(600, end_seq=700)
    ds_7 = data_helper.make_data(700, end_seq=800)
    ds_8 = data_helper.make_data(800, end_seq=900)
    end = data_helper.make_data(900, end_seq=1000)

    send_list = [end, ds_7, ds_5, ds_3, ds_1, ds_8, ds_6, ds_4, ds_2, ds_0]

    for data in send_list:
        helper.send_data(data.seq, server_seq, data.payload)

    # 当 EHIP_TCP_FRAGMENT_SEGMENT_MAX_NUM == 9 时，最多存储 9/2 = 4 个分片
    # end分片应该被丢掉了，因为ehip协议栈中默认存4块分片,在发送ds_1时，end应该被丢弃了，所以最终的ack应该是 ds_8.end_seq
    client_seq = ds_8.end_seq
    ret = helper.wait_ack(client_seq, timeout=0.5)
    if not ret:
        logging.info("[ERROR] Wait ACK failed")
        return False

    ret = helper.send_fin_wait_ack(client_seq, server_seq, timeout=0.5)
    if not ret:
        logging.info("[ERROR] Send FIN failed")
        return False
    client_seq += 1

    # 等待FIN
    ret = helper.wait_fin(client_seq, server_seq, timeout=0.5)
    if not ret:
        logging.info(f'[ERROR] Wait FIN failed client:{client_seq} server_seq{server_seq}')
        return False

    server_seq += 1
    helper.send_ack(client_seq, server_seq)
    return True


# 发送乱序数据测试，
def test_established_fragment_3(client_seq, server_ip, server_port, local_ip, local_port):
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

    data_helper = tcp_test_helper.TcpTestDataProducer(client_seq)

    #  [0-100] [100-200] 
    ds_0 = (data_helper.make_data(0, end_seq=100)    ,False)
    ds_1 = (data_helper.make_data(100, end_seq=200)  ,False)
    ds_2 = (data_helper.make_data(200, end_seq=300)  ,False)
    ds_3 = (data_helper.make_data(300, end_seq=400)  ,False)
    ds_4 = (data_helper.make_data(400, end_seq=500)  ,False)
    ds_5 = (data_helper.make_data(500, end_seq=600)  ,False)
    ds_6 = (data_helper.make_data(600, end_seq=700)  ,True )
    end =  (data_helper.make_data(900, end_seq=1000) ,False)

    send_list = [end, ds_5, ds_3, ds_1, ds_6, ds_4, ds_2, ds_0]

    for data, is_fin in send_list:
        if is_fin:
            helper.send_common(data.seq, server_seq, "PAF", data.payload)
            client_seq = data.end_seq + 1
        else:
            helper.send_common(data.seq, server_seq, "PA", data.payload)

    ret = helper.wait_ack(client_seq, timeout=0.5)
    if not ret:
        logging.info("[ERROR] Wait ACK failed")
        return False

    # 等待FIN
    ret = helper.wait_fin(client_seq, server_seq, timeout=0.5)
    if not ret:
        logging.info(f'[ERROR] Wait FIN failed client:{client_seq} server_seq{server_seq}')
        return False

    server_seq += 1
    helper.send_ack(client_seq, server_seq)
    return True


# 发送乱序数据测试，
def test_established_fragment_4(client_seq, server_ip, server_port, local_ip, local_port):
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

    data_helper = tcp_test_helper.TcpTestDataProducer(client_seq)

    send_list = [
            (data_helper.make_data(100, end_seq=1100) , "A" ),
            (data_helper.make_data(200, end_seq=300) , "A" ),
            (data_helper.make_data(300, end_seq=400) , "A" ),
            (data_helper.make_data(300, end_seq=1000) , "FA" ),
            (data_helper.make_data(0, end_seq=500) ,  "A" ),
        ]

    for data, flags in send_list:
        helper.send_common(data.seq, server_seq, flags, data.payload)
        if "F" in flags:
            client_seq = data.end_seq + 1

    ret = helper.wait_ack(client_seq, timeout=0.5)
    if not ret:
        logging.info("[ERROR] Wait ACK failed client:{client_seq} server_seq{server_seq}")
        return False

    # 等待FIN
    ret = helper.wait_fin(client_seq, server_seq, timeout=0.5)
    if not ret:
        logging.info(f'[ERROR] Wait FIN failed client:{client_seq} server_seq{server_seq}')
        return False

    server_seq += 1
    helper.send_ack(client_seq, server_seq)
    return True


# 发送乱序数据测试，
def test_established_fragment_5(client_seq, server_ip, server_port, local_ip, local_port):
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

    data_helper = tcp_test_helper.TcpTestDataProducer(client_seq)

    send_list = [
            (data_helper.make_data(100, end_seq=1300) , "A" ),
            (data_helper.make_data(200, end_seq=300) , "A" ),
            (data_helper.make_data(300, end_seq=400) , "A" ),
            (data_helper.make_data(300, end_seq=1000) , "A" ),
            (data_helper.make_data(1100, end_seq=1100) , "FA" ),
            (data_helper.make_data(0, end_seq=500) ,  "A" ),
        ]

    for data, flags in send_list:
        helper.send_common(data.seq, server_seq, flags, data.payload)
        if "F" in flags:
            client_seq = data.end_seq + 1

    ret = helper.wait_ack(client_seq, timeout=0.5)
    if not ret:
        logging.info("[ERROR] Wait ACK failed client:{client_seq} server_seq{server_seq}")
        return False

    # 等待FIN
    ret = helper.wait_fin(client_seq, server_seq, timeout=0.5)
    if not ret:
        logging.info(f'[ERROR] Wait FIN failed client:{client_seq} server_seq{server_seq}')
        return False

    server_seq += 1
    helper.send_ack(client_seq, server_seq)
    return True


# 发送正序数据测试，
def test_established_fragment_6(client_seq, server_ip, server_port, local_ip, local_port):
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

    data_helper = tcp_test_helper.TcpTestDataProducer(client_seq)

    send_list = [
            (data_helper.make_data(0,       len=1460 ) , "A" ),
            (data_helper.make_data(1460,    len=1460 ) , "A" ),
            (data_helper.make_data(1460*2,  len=1460 ) , "A" ),
            (data_helper.make_data(1460*3,  len=1460 ) , "A" ),
            (data_helper.make_data(1460*4,  len=1460 ) , "FA" ),
        ]

    for data, flags in send_list:
        helper.send_common(data.seq, server_seq, flags, data.payload)
        if "F" in flags:
            client_seq = data.end_seq + 1

    ret = helper.wait_ack(client_seq, timeout=0.5)
    if not ret:
        logging.info("[ERROR] Wait ACK failed client:{client_seq} server_seq{server_seq}")
        return False

    # 等待FIN
    ret = helper.wait_fin(client_seq, server_seq, timeout=0.5)
    if not ret:
        logging.info(f'[ERROR] Wait FIN failed client:{client_seq} server_seq{server_seq}')
        return False

    server_seq += 1
    helper.send_ack(client_seq, server_seq)
    return True


if __name__ == "__main__":
    logging.basicConfig(
        format='%(asctime)s.%(msecs)03d [%(filename)s:%(lineno)d] - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S',
        level=logging.DEBUG
    )

    ret = test_established_fragment_0(random.randint(1000, 1000000), config.TARGET_IP, config.TARGET_PORT, config.LOCAL_IP, random.randint(9000, 65535))
    if not ret:
        logging.error("Test failed")
        exit(1)
    
    ret = test_established_fragment_1(0, config.TARGET_IP, config.TARGET_PORT, config.LOCAL_IP, random.randint(9000, 65535))
    if not ret:
        logging.error("Test failed")
        exit(1)
    
    ret = test_established_fragment_2(0, config.TARGET_IP, config.TARGET_PORT, config.LOCAL_IP, random.randint(9000, 65535))
    if not ret:
        logging.error("Test failed")
        exit(1)
    
    ret = test_established_fragment_3(0, config.TARGET_IP, config.TARGET_PORT, config.LOCAL_IP, random.randint(9000, 65535))
    if not ret:
        logging.error("Test failed")
        exit(1)
    
    ret = test_established_fragment_4(0, config.TARGET_IP, config.TARGET_PORT, config.LOCAL_IP, random.randint(9000, 65535))
    if not ret:
        logging.error("Test failed")
        exit(1)
    
    ret = test_established_fragment_5(0, config.TARGET_IP, config.TARGET_PORT, config.LOCAL_IP, random.randint(9000, 65535))
    if not ret:
        logging.error("Test failed")
        exit(1)
    
    ret = test_established_fragment_6(0, config.TARGET_IP, config.TARGET_PORT, config.LOCAL_IP, random.randint(9000, 65535))
    if not ret:
        logging.error("Test failed")
        exit(1)
    