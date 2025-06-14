from scapy.all import *
import time
import random

# 配置目标信息
TARGET_IP = "192.168.12.7"
TARGET_PORT = 7777

def get_local_ip():
    return "192.168.12.12"

# 发送SYN包（三次握手第一步）
def send_syn(src_ip, src_port, client_seq):
    syn_packet = IP(src=src_ip, dst=TARGET_IP) / TCP(
        sport=src_port, 
        dport=TARGET_PORT, 
        flags="S", 
        seq=client_seq
    )
    
    print(f"[+] Sending SYN to {TARGET_IP}:{TARGET_PORT}")
    response = sr1(syn_packet, timeout=2, verbose=0)
    
    if response and response.haslayer(TCP) and response[TCP].flags & 0x12:  # SYN-ACK
        server_seq = response[TCP].seq
        print(f"[+] Received SYN-ACK from {TARGET_IP}, server seq: {server_seq}")
        return True, client_seq + 1, server_seq  # SYN消耗一个序列号
    else:
        print("[-] No SYN-ACK response received")
        return False, client_seq, None

# 发送ACK包（三次握手第三步）
def send_ack(src_ip, src_port, client_seq, server_seq):
    ack_packet = IP(src=src_ip, dst=TARGET_IP) / TCP(
        sport=src_port,
        dport=TARGET_PORT,
        flags="A",
        seq=client_seq,
        ack=server_seq + 1
    )
    
    print("[+] Sending ACK to complete three-way handshake")
    send(ack_packet, verbose=0)
    print("[+] TCP connection established")
    return client_seq, server_seq + 1  # 因为SYN序列号已消耗

# 发送数据
def send_data(src_ip, src_port, data, client_seq, server_seq):
    data_packet = IP(src=src_ip, dst=TARGET_IP) / TCP(
        sport=src_port,
        dport=TARGET_PORT,
        flags="PA",  # PSH + ACK
        seq=client_seq,
        ack=server_seq
    ) / Raw(load=data.encode())
    
    print(f"[+] Sending data: '{data}'")
    send(data_packet, verbose=0)
    
    # 更新序列号（数据长度）
    new_client_seq = client_seq + len(data)
    print(f"[*] Client sequence updated: {client_seq} → {new_client_seq}")
    
    return new_client_seq, server_seq

# 发送FIN（四次挥手第一步）
def send_fin(src_ip, src_port, client_seq, server_seq):
    fin_packet = IP(src=src_ip, dst=TARGET_IP) / TCP(
        sport=src_port,
        dport=TARGET_PORT,
        flags="FA",  # FIN + ACK
        seq=client_seq,
        ack=server_seq
    )
    
    print("[+] Sending FIN (first step of four-way handshake)")
    response = sr1(fin_packet, timeout=2, verbose=0)
    
    if response and response.haslayer(TCP):
        return response
    else:
        print("[-] No response to FIN")
        return None

# 处理服务器FIN（四次挥手第三步）
def handle_server_fin(src_ip, src_port, client_seq, server_seq):
    # 设置嗅探器捕获服务器FIN
    sniff_filter = f"host {TARGET_IP} and tcp port {src_port}"
    print(f"[*] Sniffing for FIN packet (filter: {sniff_filter})")
    
    # 捕获TCP包（等待服务器FIN）
    packets = sniff(filter=sniff_filter, count=1, timeout=3)
    
    if packets:
        pkt = packets[0]
        if pkt[TCP].flags & 0x01:  # FIN
            print(f"[+] Received FIN from server, seq: {pkt[TCP].seq}")
            return pkt[TCP].seq, client_seq, server_seq
    
    print("[-] No FIN received from server")
    return None, client_seq, server_seq

# 发送最终ACK（四次挥手第四步）
def send_final_ack(src_ip, src_port, client_seq, server_seq):
    ack_packet = IP(src=src_ip, dst=TARGET_IP) / TCP(
        sport=src_port,
        dport=TARGET_PORT,
        flags="A",
        seq=client_seq,
        ack=server_seq + 1  # 服务器FIN消耗一个序列号
    )
    
    send(ack_packet, verbose=0)
    print(f"[+] Sent FIN-ACK (server_seq: {server_seq+1})")
    return client_seq, server_seq + 1

if __name__ == "__main__":
    # 获取本地IP和随机端口
    src_ip = get_local_ip()
    src_port = random.randint(1024, 65535)
    
    # 初始化序列号
    client_seq = random.randint(1000, 1000000)
    server_seq = None
    
    print(f"[*] Starting connection from {src_ip}:{src_port}")
    print(f"[*] Initial client seq: {client_seq}")
    
    # 1. 三次握手 - 第一步：发送SYN
    success, client_seq, server_seq = send_syn(src_ip, src_port, client_seq)
    
    if success:
        print(f"[*] After SYN: client_seq={client_seq}, server_seq={server_seq}")
        
        # 2. 三次握手 - 第三步：发送ACK
        client_seq, server_seq = send_ack(src_ip, src_port, client_seq, server_seq)
        print(f"[*] Connection established: client_seq={client_seq}, server_seq={server_seq}")
        
        # 3. 发送数据
        client_seq, server_seq = send_data(src_ip, src_port, "12345", client_seq, server_seq)
        print(f"[*] After data send: client_seq={client_seq}, server_seq={server_seq}")
        
        # 等待0.5秒让服务器处理数据
        time.sleep(0.5)
        
        # 4. 四次挥手开始 - 发送FIN
        fin_response = send_fin(src_ip, src_port, client_seq, server_seq)
        if fin_response:
            # FIN消耗一个序列号
            client_seq += 1
            print(f"[*] After FIN: client_seq={client_seq}")
            
            # 5. 等待并处理服务器FIN
            fin_server_seq, client_seq, server_seq = handle_server_fin(src_ip, src_port, client_seq, server_seq)
            if fin_server_seq:
                # 6. 发送最终ACK
                client_seq, server_seq = send_final_ack(src_ip, src_port, client_seq, fin_server_seq)
                print(f"[+] Four-way handshake completed. Connection closed")
        
        print("[*] Final state:")
        print(f"    Client seq: {client_seq}")
        print(f"    Server seq: {server_seq}")
    
    print("[!] Process completed")