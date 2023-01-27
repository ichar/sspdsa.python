#!/usr/bin/env python
# -*- coding: utf-8 -*-

import socket

sock = socket.socket()
sock.connect(('localhost', 10000))

print(('%s'*4) % (sock.getsockname(), sock.getpeername(), sock.type, sock.family))
print(sock)

items = [
    'HELO:%s:%s' % sock.getsockname(),
    'hello, world!',
    'What next',
    'Common',
]

for item in items:
    try:
        sock.send(item.encode())
        print('>>> client.sent: [%s] total:%s' % (item, len(item)))

        data = sock.recv(24)
        if data is not None:
            print('>>> client.received.back: [%s] total:%s' % (data.decode(), len(data)))
        else:
            print('>>> client.received.None: [%s]' % data)
            break
    except Exception as error:
        raise

x = bytearray(2)
x[0] = 0xf1
x[1] = 1
sock.send(x)
data = sock.recv(24)
print('>>> client.received.data: [%s]' % data)

sock.send('close'.encode())

sock.close()


