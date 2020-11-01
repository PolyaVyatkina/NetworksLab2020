from _datetime import datetime, timezone
import socket
import threading

HEADER_LENGTH = 16

username = input('Write your name: ')
client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
try:
    client.connect(('127.0.0.1', 1234))
    # client.connect(('51.15.130.137', 1234))
except ConnectionRefusedError:
    print("Server is offline")
    exit(0)
else:
    print("Connected to server\n")


def close_connection():
    print("closing")
    client.shutdown(socket.SHUT_WR)
    client.close()
    exit(0)


def encode(data):
    message = [username.encode('utf-8'),
               datetime.utcnow().strftime('%d/%m/%Y %H:%M').encode('utf-8'),
               data.encode('utf-8')]
    return b'\0'.join(message)


def decode(message):
    message = [part.decode('utf-8') for part in message.split(b'\0')]
    return message[0], message[1], message[2]


def print_message(_username, _time, _data):
    _time = datetime.strptime(_time, '%d/%m/%Y %H:%M')
    _time = _time.replace(tzinfo=timezone.utc).astimezone(tz=None).strftime('%d/%m/%Y %H:%M')
    print(f"[{_username}] {_time} :: {_data}")


def receive_bytes(length):
    received = 0
    message = b''
    while True:
        try:
            data = client.recv(length - received)
            if received < length:
                message += data
                received += len(data)
            elif message == b'':
                close_connection()
            else:
                return message
        except Exception as ex:
            print(ex)
            return


def receive():
    while True:
        try:
            data = client.recv(HEADER_LENGTH)
            if data == b'':
                close_connection()
            message_length = int(data.decode('utf-8').strip())
            message = receive_bytes(message_length)
            if not message:
                close_connection()
            else:
                _username, _time, _data = decode(message)
                print_message(_username, _time, _data)
        except ConnectionResetError:
            close_connection()
            return
        except Exception as ex:
            print(ex)
            return


def send_bytes(data):
    message = encode(data)
    length = len(message)
    header = f"{length:<{HEADER_LENGTH}}".encode('utf-8')
    message = header + message
    sent = 0
    while sent < length:
        _ = client.send(message[sent:])
        if _ == 0:
            raise RuntimeError("Socket connection broken")
        sent = sent + _


def send():
    while True:
        data = input()
        if data != '':
            send_bytes(data)


def main():
    threading.Thread(target=receive).start()
    threading.Thread(target=send).start()


if __name__ == '__main__':
    main()
