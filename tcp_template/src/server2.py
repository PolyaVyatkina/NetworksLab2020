import errno
import select
import socket
import queue

HEADER_LENGTH = 16

server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server.setblocking(False)
server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
server.bind(('0.0.0.0', 1234))
# server.bind(('127.0.0.1', 1234))
server.listen(7)
print('Server is online')

inputs = [server]
outputs = []
message_queues = {}
buffer = {}


def send_data(current_client, data):
    for client in message_queues.keys():
        if client != current_client:
            client.sendall(data)


def close_connection(user):
    if user in outputs:
        outputs.remove(user)
    inputs.remove(user)
    user.close()
    del message_queues[user]
    print(f"Client disconnected")


def receive_bytes(client, length):
    received = 0
    message = buffer[client]['message']
    data = client.recv(length - received)
    message += data
    received += len(data)
    buffer[client]['length'] = length
    buffer[client]['received'] = received
    buffer[client]['message'] = message


def listen_socket(user):
    if user not in buffer.keys():
        data = user.recv(HEADER_LENGTH)
        if data == b'':
            close_connection(user)
            return
        else:
            message_length = int(data.decode('utf-8').strip())
            print(f"message length: {message_length}")
            buffer[user] = {'header': data, 'length': message_length, 'received': 0, 'message': b''}
            receive_bytes(user, message_length)
            if user not in outputs:
                outputs.append(user)
    else:
        receive_bytes(user, buffer[user]['length'] - buffer[user]['received'])
    if buffer[user]['length'] == buffer[user]['received']:
        message_queues[user].put(buffer[user]['header'] + buffer[user]['message'])
        del buffer[user]


def accept_sockets(readable, writable, exceptional):
    for _socket in readable:
        if _socket is server:
            client, addr = _socket.accept()
            client.setblocking(False)
            inputs.append(client)
            message_queues[client] = queue.Queue()
            print(f"User [{addr}] connected")
        else:
            listen_socket(_socket)
    for _socket in writable:
        try:
            next_msg = message_queues[_socket].get_nowait()
        except queue.Empty:
            outputs.remove(_socket)
        else:
            send_data(_socket, next_msg)
    for _socket in exceptional:
        close_connection(_socket)


def main():
    while inputs:
        readable, writable, exceptional = select.select(inputs, outputs, inputs)
        accept_sockets(readable, writable, exceptional)


if __name__ == '__main__':
    main()
