import os
import sys
import socket
import struct
import threading
import time
from typing import Tuple

# 获取当前文件的父目录的绝对路径
parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
# 添加到模块搜索路径
sys.path.append(parent_dir)

import config


def tcp_echo_test(total_bytes: int, ip: str, port: int, recv_timeout: float = 5.0) -> Tuple[float, float, int]:
    if total_bytes <= 0:
        raise ValueError("total_bytes must be > 0")
    if total_bytes % 4 != 0:
        pad = 4 - (total_bytes % 4)
        print(f"[WARN] total_bytes {total_bytes} 不是 4 的倍数，将补齐 {pad} 字节")
        total_bytes += pad

    total_uint32 = total_bytes // 4

    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.settimeout(10.0)
    sock.connect((ip, port))
    sock.settimeout(recv_timeout)

    stop_event = threading.Event()
    error_info = {"occurred": False, "message": None}
    counters = {"sent_uints": 0, "recv_uints": 0}

    next_send_seq = 0

    # ===== 发送线程（原始逻辑，无延时） =====
    def sender():
        nonlocal next_send_seq
        try:
            batch_uints = 1024*32  # 每批 16KB
            while not stop_event.is_set() and next_send_seq < total_uint32:
                remaining = total_uint32 - next_send_seq
                send_count = min(batch_uints, remaining)
                buf = b''.join(struct.pack('!I', (next_send_seq + i) & 0xFFFFFFFF) for i in range(send_count))
                try:
                    sent_bytes = sock.send(buf)
                except Exception as e:
                    error_info["occurred"] = True
                    error_info["message"] = f"发送异常: {e}"
                    stop_event.set()
                    break
                sent_uints = sent_bytes // 4
                next_send_seq += sent_uints
                counters["sent_uints"] += sent_uints
                if sent_uints < send_count:
                    break
        except Exception as e:
            error_info["occurred"] = True
            error_info["message"] = f"发送线程异常: {e}"
            stop_event.set()

    # ===== 接收线程（一次多收） =====
    def receiver():
        expected = 0
        leftover = b''  # 存上次多出来的残留字节
        try:
            while not stop_event.is_set() and counters["recv_uints"] < total_uint32:
                try:
                    data = sock.recv(4096)
                except socket.timeout:
                    error_info["occurred"] = True
                    error_info["message"] = f"接收超时 {recv_timeout}s"
                    stop_event.set()
                    return
                except Exception as e:
                    error_info["occurred"] = True
                    error_info["message"] = f"接收异常: {e}"
                    stop_event.set()
                    return
                if not data:
                    error_info["occurred"] = True
                    error_info["message"] = "连接被关闭"
                    stop_event.set()
                    return

                data = leftover + data
                total_len = len(data)
                # 按 4 字节解析
                full_uints = total_len // 4
                leftover = data[full_uints * 4:]  # 存下不满 4 字节的部分

                for i in range(full_uints):
                    val, = struct.unpack_from('!I', data, i * 4)
                    expected_wrapped = expected & 0xFFFFFFFF
                    if val != expected_wrapped:
                        error_info["occurred"] = True
                        error_info["message"] = f"数据错: 期望 {expected_wrapped}, 收到 {val}"
                        stop_event.set()
                        return
                    expected += 1
                    counters["recv_uints"] += 1
        except Exception as e:
            error_info["occurred"] = True
            error_info["message"] = f"接收线程异常: {e}"
            stop_event.set()

    # ===== 进度线程 =====
    def monitor(start_time):
        while not stop_event.is_set():
            time.sleep(0.5)
            now = time.time()
            sent_b = counters["sent_uints"] * 4
            recv_b = counters["recv_uints"] * 4
            pct = (recv_b / total_bytes) * 100
            speed = recv_b / (now - start_time) if now > start_time else 0
            print(f"[PROGRESS] elapsed={now-start_time:.2f}s sent={sent_b}B recv={recv_b}B recv_pct={pct:.2f}% speed={speed:.2f} B/s")
            if counters["recv_uints"] >= total_uint32:
                break

    # ===== 启动线程 =====
    start_time = time.time()
    t_send = threading.Thread(target=sender, daemon=True)
    t_recv = threading.Thread(target=receiver, daemon=True)
    t_mon = threading.Thread(target=monitor, args=(start_time,), daemon=True)

    t_send.start()
    t_recv.start()
    t_mon.start()

    while not stop_event.is_set():
        if counters["recv_uints"] >= total_uint32:
            break
        time.sleep(0.1)

    # ===== 稳定退出顺序 =====
    stop_event.set()
    t_send.join()
    t_recv.join()
    t_mon.join()
    try:
        sock.shutdown(socket.SHUT_RDWR)
    except Exception:
        pass
    sock.close()

    elapsed = time.time() - start_time
    recv_bytes = counters["recv_uints"] * 4
    speed = recv_bytes / elapsed if elapsed > 0 else 0

    if error_info["occurred"]:
        print(f"[TEST STOPPED] {error_info['message']}")
    else:
        print("[TEST COMPLETE] 数据全部验证通过")
    print(f"[SUMMARY] elapsed={elapsed:.3f}s bytes_recv={recv_bytes} speed={speed:.2f} B/s")

    return elapsed, speed, recv_bytes


# 示例用法（请把 ip, port 改为你的 echo 服务端地址）
if __name__ == "__main__":
    TOTAL_BYTES = 40 * 1024 * 1024  # 例如 100k 个 uint32 -> 400k 字节
    try:
        elapsed, spd, recv_bytes = tcp_echo_test(TOTAL_BYTES, config.TARGET_IP, config.TARGET_PORT_ECHO)
        print(f"结果: elapsed={elapsed:.3f}s speed={spd:.2f} B/s recv_bytes={recv_bytes}")
    except Exception as e:
        print(f"运行失败: {e}")
