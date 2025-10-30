import time
from scapy.layers.inet import IP, TCP
from scapy.sendrecv import send, sr1, AsyncSniffer
from scapy.packet import Raw
import os
import queue
import random
import logging
from dataclasses import dataclass
from ctypes import c_uint32

@dataclass
class TcpData:
    seq: c_uint32
    end_seq: c_uint32
    len: c_uint32
    payload: bytes


class TcpTestDataProducer:
    def __init__(self, first_data_seq:c_uint32):
        self.first_data_seq = first_data_seq

    def make_data(self, seq:c_uint32, len:c_uint32=32, end_seq=None):
        """
        生成测试数据包,数据将从first_data_seq序列号起,
        从0x00开始递增到0xff然后重新从0x00开始递增
        :param seq: 序列号
        :param len: 数据长度
        :return: 生成的测试数据包
        """
        if end_seq is not None:
            len = end_seq - seq
        else:
            end_seq = seq + len

        # 生成数据字节序列
        payload = bytes(
            (seq + i) % 256  # 确保在0x00-0xff范围内循环
            for i in range(len)
        )
        return TcpData(self.first_data_seq + seq, self.first_data_seq + end_seq, len, payload)




class TCPHelper:
    def __init__(self, target_ip, target_port, local_ip, local_port=None, rx_window=65535):
        """
        TCP测试助手类
        
        :param target_ip: 目标IP地址
        :param target_port: 目标端口
        :param local_ip: 本地IP地址
        :param local_port: 本地端口(自动生成随机端口)
        """
        self.target_ip = target_ip
        self.target_port = target_port
        self.local_ip = local_ip
        self.local_port = local_port if local_port else random.randint(9000, 9999)
        
        # 包队列和线程控制
        self.packet_queue = queue.Queue()
        self.sniffing = True
        self.sniffer_thread = None
        self.tx_window = None
        self.mss = 1460  # 默认MSS值
        self.rx_window = rx_window  # 默认接收窗口大小
        
        # 自动阻止重置包
        self._block_reset_packets()
        
        # 启动后台嗅探
        self._start_sniffing()
    
    def _block_reset_packets(self):
        """阻止到目标端口的RST包"""
        cmd = (f"iptables -A OUTPUT -p tcp -d {self.target_ip} "
              f"--dport {self.target_port} --tcp-flags RST RST -j DROP")
        os.system(cmd)
    
    def _unblock_reset_packets(self):
        """恢复网络设置"""
        cmd = (f"iptables -D OUTPUT -p tcp -d {self.target_ip} "
              f"--dport {self.target_port} --tcp-flags RST RST -j DROP")
        os.system(cmd)
    
    def _start_sniffing(self):
        """使用异步嗅探器实现高性能捕获"""
        filter_str = (f"tcp and dst host {self.local_ip} "
                  f"and dst port {self.local_port} "
                  f"and src host {self.target_ip}")
        
        def packet_handler(pkt):
            """包处理回调函数"""
            try:
                if pkt.haslayer(TCP):
                    tcp = pkt[TCP]
                    # logging.debug(f'Received packet: seq={tcp.seq} ack={tcp.ack} flags={tcp.flags}')
                    self.packet_queue.put(pkt)
            except Exception as e:
                logging.error(f"Packet processing error: {e}")
        
        # 创建异步嗅探器
        self.async_sniffer = AsyncSniffer(
            filter=filter_str,
            prn=packet_handler,  # 包到达时的回调
            store=False,         # 不存储包对象，节省内存
            count=0,             # 0表示持续捕获
            timeout=None         # 无超时限制
        )
        
        self.async_sniffer.start()
    
    def _stop_sniffing(self):
        """
        停止抓包
        """
        self.async_sniffer.stop()


    def send_syn_wait_ack(self, seq:c_uint32, timeout=5):
        """
        发送SYN包并等待SYN-ACK响应
        
        :param seq: 初始序列号
        :param timeout: 超时时间(秒)
        :return: (成功状态, SYN-ACK包中的服务器序列号)
        """
        packet = IP(src=self.local_ip, dst=self.target_ip) / TCP(
            sport=self.local_port,
            dport=self.target_port,
            flags="S",
            seq=seq,
            window = self.rx_window
        )
        
        response = sr1(packet, timeout=timeout, verbose=0)
        
        if response and response.haslayer(TCP) and response[TCP].flags & 0x12:  # SYN-ACK
            server_seq = response[TCP].seq
            self.tx_window = response[TCP].window
            options = response[TCP].options
            for option in options:
                if option[0] == 'MSS':
                    # 确认值类型并提取
                    if isinstance(option[1], int):
                        self.mss = option[1]  # 直接使用整数值
                    else:
                        self.mss = 546
                    break
            return True, server_seq
        
        return False, None
    def send_ack(self, seq, ack):
        """
        发送ACK包
        
        :param seq: 当前序列号
        :param ack: 要确认的序列号(接收方最后一个收到的字节的下一个序列号)
        """
        packet = IP(src=self.local_ip, dst=self.target_ip) / TCP(
            sport=self.local_port,
            dport=self.target_port,
            flags="A",  # ACK标志
            seq=seq,
            ack=ack,
            window = self.rx_window
        )
    
        send(packet, verbose=0)

    def send_data(self, seq:c_uint32, ack:c_uint32, data):
        """
        发送数据包
        
        :param seq: 当前序列号
        :param ack: 确认号
        :param data: 要发送的数据
        """

        # 统一数据处理逻辑
        if isinstance(data, str):
            payload = data.encode('utf-8')  # 字符串转二进制（默认UTF-8编码）
        elif isinstance(data, bytes):
            payload = data  # 直接使用二进制数据
        elif isinstance(data, bytearray):
            payload = bytes(data)  # bytearray转bytes
        else:
            raise TypeError(f"Unsupported data type: {type(data).__name__}. "
                            "Expected str, bytes, or bytearray.")

        packet = IP(src=self.local_ip, dst=self.target_ip) / TCP(
            sport=self.local_port,
            dport=self.target_port,
            flags="PA",  # PSH + ACK
            seq=seq,
            ack=ack,
            window = self.rx_window
        ) / Raw(load=payload)
        
        send(packet, verbose=0)
    
    def send_common(self, seq:c_uint32, ack:c_uint32, flags, data=None, rx_window=None):
        """
        发送普通包
        :param seq: SEQ
        :param ack: ACK
        :param flags: 标志位
        :param data: 要发送的数据
        """

        # 统一数据处理逻辑
        if data is None:
            payload = bytes()
        elif isinstance(data, str):
            payload = data.encode('utf-8')  # 字符串转二进制（默认UTF-8编码）
        elif isinstance(data, bytes):
            payload = data  # 直接使用二进制数据
        elif isinstance(data, bytearray):
            payload = bytes(data)  # bytearray转bytes
        else:
            raise TypeError(f"Unsupported data type: {type(data).__name__}. "
                            "Expected str, bytes, or bytearray.")
        if rx_window is None:
            rx_window = self.rx_window
        packet = IP(src=self.local_ip, dst=self.target_ip) / TCP(
            sport=self.local_port,
            dport=self.target_port,
            flags=flags,
            seq=seq,
            ack=ack,
            window = rx_window
        ) / Raw(load=payload)

        send(packet, verbose=0)

    def send_fin(self, seq:c_uint32, ack:c_uint32):
        """
        发送FIN包
        
        :param seq: 当前序列号
        :param ack: 确认号
        """
        packet = IP(src=self.local_ip, dst=self.target_ip) / TCP(
            sport=self.local_port,
            dport=self.target_port,
            flags="FA",  # FIN + ACK
            seq=seq,
            ack=ack,
            window = self.rx_window
        )
        
        send(packet, verbose=0)
    
    def send_fin_wait_ack(self, seq:c_uint32, ack:c_uint32, timeout=5):
        """
        :param seq: 当前序列号
        :param ack: 确认号
        :param timeout: 超时时间(秒)
        :return: (是否收到ACK, 收到的ACK号)
        """
        # 构造包
        fin_packet = IP(src=self.local_ip, dst=self.target_ip) / TCP(
            sport=self.local_port,
            dport=self.target_port,
            flags="FA",  # FIN+ACK
            seq=seq,
            ack=ack,
            window = self.rx_window
        )
        
        # 设置重传机制(可选)
        response = sr1(fin_packet, timeout=timeout, verbose=0)
        if response and response.haslayer(TCP) and response[TCP].flags & 0x10:  # SYN-ACK
            return response[TCP].ack == seq + 1
        
        # 没有收到有效响应
        return False
    
    def clean_queue(self):
        """
        清空队列
        """
        while not self.packet_queue.empty():
            self.packet_queue.get()

    def wait_common(self, expected_ack:c_uint32=None, expected_seq:c_uint32=None, flags:str = None, 
                    data_len=None, data=None, timeout=3):
        """
        等待符合条件的TCP数据包 - 严格匹配模式(含按位标志检查)
        返回布尔值表示是否成功匹配
        
        参数说明:
        expected_ack: 期望的ACK号(精确匹配)
        expected_seq: 期望的SEQ号(精确匹配)
        flags: 期望的TCP标志位(按位检查，如"SA"表示需要同时设置SYN和ACK)
        data: 期望的数据内容(精确匹配)
        data_len: 期望的数据长度(精确匹配)
        timeout: 超时时间(秒)
        
        返回: True(匹配成功) / False(匹配失败)
        """
        start_time = time.time()
        
        # 准备标志位掩码
        flags_mask = 0
        if flags:
            flag_mapping = {
                'F': 0x01,  # FIN
                'S': 0x02,  # SYN
                'R': 0x04,  # RST
                'P': 0x08,  # PSH
                'A': 0x10,  # ACK
                'U': 0x20,  # URG
                'E': 0x40,  # ECE
                'C': 0x80   # CWR
            }
            
            for char in flags.upper():
                if char in flag_mapping:
                    flags_mask |= flag_mapping[char]
        
        while time.time() - start_time < timeout:
            try:
                pkt = self.packet_queue.get(timeout=0.1)
                
                # 跳过非TCP包
                if not pkt.haslayer(TCP):
                    continue
                    
                tcp_layer = pkt[TCP]
                
                # 严格检查SEQ
                if expected_seq is not None and tcp_layer.seq != expected_seq:
                    continue
                
                # 严格检查ACK
                if expected_ack is not None and tcp_layer.ack != expected_ack:
                    continue
                
                # 按位检查标志位
                if flags_mask:
                    # 获取包的当前标志位值
                    pkt_flags = tcp_layer.flags
                    
                    # 使用位操作检查是否设置了所有要求的标志位
                    if (pkt_flags & flags_mask) != flags_mask:
                        continue
                
                # 检查数据长度
                raw_data = pkt[Raw].load if pkt.haslayer(Raw) else b''
                
                if data_len is not None and len(raw_data) != data_len:
                    continue
                
                # 检查数据内容
                if data is not None:
                    # 直接比较字节或字符串
                    if isinstance(data, str):
                        try:
                            if raw_data.decode('utf-8') != data:
                                continue
                        except UnicodeDecodeError:
                            continue
                    elif raw_data != data:  # 字节比较
                        continue
                
                # 所有条件满足，匹配成功
                return True
                    
            except queue.Empty:
                pass
        
        return False  # 超时未找到匹配包



    def wait_ack(self, expected_ack:c_uint32, timeout=3):
        """
        等待特定ACK号的确认包
        
        :param expected_ack: 期待的ACK号
        :param timeout: 超时时间(秒)
        :return: 是否收到符合条件的ACK包
        """
        start_time = time.time()
        
        while time.time() - start_time < timeout:
            try:
                pkt = self.packet_queue.get(timeout=0.1)
                # logging.debug(f'wait_ack :{pkt} seq{pkt[TCP].seq} ack{pkt[TCP].ack}')
                if pkt.haslayer(TCP) and pkt[TCP].flags & 0x10:  # ACK
                    if pkt[TCP].ack == expected_ack:
                        self.tx_window = pkt[TCP].window
                        return True
            except queue.Empty:
                pass
        
        return False
    

    def wait_fin(self, expected_ack:c_uint32, expected_seq:c_uint32, timeout=5):
        """
        等待带有特定序列号和确认号的FIN包
        
        :param expected_seq: 期望的序列号(服务器应该发送的)
        :param expected_ack: 期望的确认号(服务器应该确认的本地序列号)
        :param timeout: 超时时间(秒)
        :return: 是否成功接收到符合条件的FIN包
        """
        start_time = time.time()
        
        while time.time() - start_time < timeout:
            try:
                pkt = self.packet_queue.get(timeout=0.1)
                # logging.debug(f'wait_fin :{pkt} seq{pkt[TCP].seq} ack{pkt[TCP].ack}')
                if pkt.haslayer(TCP) and pkt[TCP].flags & 0x01:  # FIN标志
                    actual_seq = pkt[TCP].seq
                    actual_ack = pkt[TCP].ack
                    
                    # 检查seq和ack是否符合预期
                    if actual_seq == expected_seq and actual_ack == expected_ack:
                        if pkt[TCP].flags & 0x10:  # 确保是ACK
                            self.tx_window = pkt[TCP].window
                        return True
            except queue.Empty:
                pass
        
        return False
    
    def __del__(self):
        """析构函数，清理资源"""
        self._stop_sniffing()
        self._unblock_reset_packets()