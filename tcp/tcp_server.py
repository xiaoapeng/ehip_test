import socket

def start_tcp_server(host='0.0.0.0', port=8888, buffer_size=3072):
    # 创建 TCP 套接字
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    
    # 设置接收缓冲区大小
    server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_RCVBUF, buffer_size)
    server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

    # 绑定到指定端口
    server_socket.bind((host, port))
    server_socket.listen(1)
    
    print(f"Listening on {host}:{port} with receive buffer size {buffer_size} bytes")

    # 等待客户端连接
    client_socket, client_address = server_socket.accept()
    print(f"Connection established with {client_address}")

    # 接收数据并打印
    while True:
        data = client_socket.recv(buffer_size)
        if not data:
            break
        print(data.decode('utf-8', errors='ignore'))  # 打印接收到的数据（假设是文本）

    print("File data received and printed.")
    client_socket.close()
    server_socket.close()

if __name__ == "__main__":
    start_tcp_server()
