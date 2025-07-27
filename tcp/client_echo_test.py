import os
import sys
import socket
import time
import threading
import struct

# 获取当前文件的父目录的绝对路径
parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
# 添加到模块搜索路径
sys.path.append(parent_dir)

import config

# 全局变量
send_complete = threading.Event()
test_results = {"successful": 0, "failed": 0, "total_bytes": 0}
result_lock = threading.Lock()
next_expected_value = 0  # 全局递增的期望值

def generate_test_data(start_value, num_uint32):
    """
    生成测试数据，包含递增的uint32值
    
    Args:
        start_value (int): 起始uint32值
        num_uint32 (int): 要生成的uint32数量
        
    Returns:
        bytes: 生成的测试数据
    """
    test_data = b''
    for i in range(num_uint32):
        value = start_value + i
        test_data += struct.pack('>I', value)  # 大端序打包
    
    return test_data

def print_progress_bar(progress, total, prefix='', suffix='', length=50, fill='█'):
    """
    打印进度条
    
    Args:
        progress (int): 当前进度
        total (int): 总量
        prefix (str): 进度条前缀
        suffix (str): 进度条后缀
        length (int): 进度条长度
        fill (str): 进度条填充字符
    """
    percent = f"{100 * (progress / float(total)):.1f}" if total > 0 else "0.0"
    filled_length = int(length * progress // total) if total > 0 else 0
    bar = fill * filled_length + '-' * (length - filled_length)
    print(f'\r{prefix} |{bar}| {percent}% {suffix}', end='\r')
    if progress == total:
        print()  # 完成后换行

def send_thread_function(client_socket, total_bytes):
    """
    发送数据的线程函数
    
    Args:
        client_socket: TCP套接字
        total_bytes (int): 总发送字节数
    """
    global next_expected_value
    
    try:
        bytes_sent = 0
        current_value = 0
        
        while bytes_sent < total_bytes:
            # 计算本次发送的数据量（最多4096字节）
            chunk_size = min(4096, total_bytes - bytes_sent)
            num_uint32 = chunk_size // 4
            
            # 生成并发送测试数据
            test_data = generate_test_data(current_value, num_uint32)
            client_socket.sendall(test_data)
            
            current_value += num_uint32
            bytes_sent += len(test_data)
            
        # 发送完成后显示简单提示
        print("发送完成")
    except Exception as e:
        print(f"发送线程错误: {e}")
    finally:
        # 标记发送完成
        send_complete.set()

def receive_thread_function(client_socket, total_bytes):
    """
    接收数据的线程函数
    
    Args:
        client_socket: TCP套接字
        total_bytes (int): 总接收字节数
    """
    global next_expected_value
    bytes_received = 0
    start_time = time.time()  # 记录开始时间用于计算速度
    
    try:
        while bytes_received < total_bytes:
            try:
                # 接收回声数据
                remaining_bytes = total_bytes - bytes_received
                chunk_size = min(4096, remaining_bytes)
                received_data = client_socket.recv(chunk_size)
                
                if not received_data:
                    # 连接关闭，退出循环
                    break
                
                # 验证数据中的uint32值是否正确递增
                num_uint32 = len(received_data) // 4
                is_valid = True
                
                for i in range(num_uint32):
                    expected_value = next_expected_value
                    try:
                        actual_value = struct.unpack('>I', received_data[i*4:i*4+4])[0]
                        if actual_value != expected_value:
                            is_valid = False
                            break
                    except:
                        is_valid = False
                        break
                    next_expected_value += 1
                
                # 更新测试结果
                with result_lock:
                    if is_valid:
                        test_results["successful"] += num_uint32
                    else:
                        test_results["failed"] += num_uint32
                    
                    bytes_received += len(received_data)
                    test_results["total_bytes"] = bytes_received
                    
                    # 计算当前速度
                    elapsed_time = time.time() - start_time
                    speed = bytes_received / elapsed_time if elapsed_time > 0 else 0
                    speed_str = f"{speed/1024/1024:.2f} MB/s" if speed > 0 else "0.00 MB/s"
                    
                    # 显示接收进度条和速度
                    print_progress_bar(bytes_received, total_bytes, prefix='测试进度:', 
                                     suffix=f'({speed_str})', length=30)
                    
            except socket.timeout:
                with result_lock:
                    # 计算剩余未接收的uint32数量
                    remaining_bytes = total_bytes - bytes_received
                    remaining_uint32 = remaining_bytes // 4
                    test_results["failed"] += remaining_uint32
                    test_results["total_bytes"] = bytes_received
                break
            except Exception as e:
                with result_lock:
                    # 计算剩余未接收的uint32数量
                    remaining_bytes = total_bytes - bytes_received
                    remaining_uint32 = remaining_bytes // 4
                    test_results["failed"] += remaining_uint32
                    test_results["total_bytes"] = bytes_received
                break
                
        # 计算最终速度
        elapsed_time = time.time() - start_time
        avg_speed = total_bytes / elapsed_time if elapsed_time > 0 else 0
        avg_speed_str = f"{avg_speed/1024/1024:.2f} MB/s" if avg_speed > 0 else "0.00 MB/s"
        
        print(f"\n接收完成，平均速度: {avg_speed_str}")
        
        # 如果没有接收到所有数据，标记剩余的为失败
        if bytes_received < total_bytes:
            with result_lock:
                remaining_bytes = total_bytes - bytes_received
                remaining_uint32 = remaining_bytes // 4
                test_results["failed"] += remaining_uint32
                
    except Exception as e:
        print(f"接收线程发生异常: {e}")

def echo_test_stream_threaded(total_bytes=40960):
    """
    基于多线程的流式TCP回声测试实现（按4096字节块发送）
    
    Args:
        total_bytes (int): 要测试的总数据长度（字节）
    
    Returns:
        dict: 测试结果统计
    """
    global test_results, next_expected_value
    test_results = {"successful": 0, "failed": 0, "total_bytes": 0}
    next_expected_value = 0
    
    client_socket = None
    try:
        # 创建TCP套接字
        client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        client_socket.settimeout(15)  # 设置15秒超时
        
        print(f"正在连接到 {config.TARGET_IP}:{config.TARGET_PORT_ECHO}...")
        client_socket.connect((config.TARGET_IP, config.TARGET_PORT_ECHO))
        print("连接成功!")
        
        # 创建发送和接收线程
        send_thread = threading.Thread(
            target=send_thread_function,
            args=(client_socket, total_bytes),
            name="SendThread"
        )
        
        receive_thread = threading.Thread(
            target=receive_thread_function,
            args=(client_socket, total_bytes),
            name="ReceiveThread"
        )
        
        # 启动线程
        receive_thread.start()
        send_thread.start()
        
        # 等待线程结束
        send_thread.join()
        receive_thread.join()
        
        return test_results.copy()
        
    except Exception as e:
        print(f"连接或测试过程中发生错误: {e}")
        # 计算总的uint32数量
        total_uint32 = total_bytes // 4
        return {
            "successful": 0,
            "failed": total_uint32,
            "total_bytes": 0
        }
    finally:
        send_complete.clear()
        if client_socket:
            try:
                client_socket.close()
            except:
                pass

def main():
    """
    主函数，执行基于多线程流式的回声测试
    """
    # 可以通过命令行参数指定测试数据总字节数
    total_bytes = 1024*1024*500  # 默认40KB
    
    if len(sys.argv) > 1:
        try:
            total_bytes = int(sys.argv[1])
        except ValueError:
            print("无效的参数，使用默认值 40960 字节")
    
    print(f"开始TCP回声测试，总字节数: {total_bytes}")
    print("-" * 50)
    
    # 记录测试开始时间
    start_time = time.time()
    
    # 执行测试
    result = echo_test_stream_threaded(total_bytes)
    
    # 计算测试耗时
    elapsed_time = time.time() - start_time
    
    # 计算总uint32数量和成功率
    total_uint32 = total_bytes // 4
    success_rate = (result['successful'] / total_uint32 * 100) if total_uint32 > 0 else 0
    
    # 计算传输速度
    speed_mbps = (total_bytes * 8) / (elapsed_time * 1024 * 1024) if elapsed_time > 0 else 0
    
    # 输出测试结果
    print("-" * 50)
    print("测试结果:")
    print(f"  成功率: {success_rate:.2f}%")
    print(f"  传输速度: {speed_mbps:.2f} Mbps")
    print(f"  测试耗时: {elapsed_time:.2f} 秒")

if __name__ == "__main__":
    main()