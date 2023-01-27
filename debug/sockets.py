#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sys
import socket
import sys

from bitstring import BitArray

argv = sys.argv

STEPS_LIMIT = 100
HOST= '127.0.0.1'
PORT = 10000
SIZE = 24

IsCloseConnection = 0

def start():
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    
    #sock.shutdown(False)
    
    server_address = (HOST, PORT)
    print('>>> Server starts on {} port {}'.format(*server_address))
    sock.bind(server_address)
    
    
    sock.listen(1)
    
    is_finish = False
    
    n = 0
    
    while not is_finish:
        print('>>> Waitinig connections [%s]...' % n)
        connection, client_address = sock.accept()
    
        try:
            client_ip, client_port = client_address
            print('>>> Connected to [%s]: %s', (connection, client_address))
    
            while True:
                answer = None
                try:
                    data = connection.recv(SIZE)
                except ConnectionResetError as error:
                    print('... Error: %s, step:[%s]' % (str(error), n))
                    break

                if data:
                    n += 1
                    print('... Received: [%s] total: %s' % (data, len(data)))
                    if isinstance(data, bytes):
                        if len(data) == 2:
                            c = BitArray(data)
                            answer = bytearray(data)
                            answer.extend(':OK'.encode())
                            print('>>> Command: %s[%s] received' % (data, c.bin))
                        else:
                            data = data.decode()
                            if data.startswith('HELO'):
                                x = data.split(':')
                                remote_ip = x[1]
                                print('>>> HELO: %s remote_ip:[%s]' % (str(client_address), remote_ip))
                                answer = 'EHLO:%s:%s' % (client_ip, client_port)
                            elif data == 'CLOSE':
                                print('>>> Closed connection for client: %s' % str(client_address))
                                answer = 'closed'
                                is_finish = True
                            else:
                                answer = data.upper()

                            answer = answer.encode()

                        if answer is not None:
                            connection.sendall(answer)
                            print('... Sent back: [%s] total: %s' % (answer, len(answer)))
                        
                        if is_finish:
                            break
                else:
                    print('>>> No data from: %s' % str(client_address))
                    break
    
                if n > STEPS_LIMIT:
                    break
    
        finally:
            if connection is not None and IsCloseConnection:
                connection.close()
                print('>>> Socket is closed: %s' % str(client_address))
    
    if sock is not None and IsCloseConnection:
        sock.shutdown(False)
        print('>>> Shutdown')


def test_server():
    import socket
    
    HOST= 'localhost'
    PORT = 9090
    
    sock = socket.socket()
    sock.bind((HOST, PORT))
    sock.listen(1)
    print ('>>> socket.started: %s:%s' % (HOST, PORT))
    conn, addr = sock.accept()
    
    print('connected done!.addr:%s', addr)
    
    while True:
        data = conn.recv(1024)
        print('>>> received: [%s] total:%s' % (data, len(data)))
        if not data:
            break
        conn.send(data.upper())
    
    conn.close()
    
    sock.shutdown(False)


if __name__ == "__main__":
    argv = sys.argv

    if len(argv) == 2 and argv[1].lower() in ('/?', '/h', '/help', '-h', 'help', '--help'):
        print('--> ORION HOLDING INC.')
        print('--> = SSPDS SPO Socket Server emulator =')
        print('--> ')
        print('--> Start: python sockets.py [<limit> [<ip> [<port> [<size>]]]]')
        print('--> ')
        print('--> Arguments:')
        print('-->   <limit> - sockets steps limit, default: 100')
        print('-->   <ip>    - sockets ip-address, default: 127.0.0.1')
        print('-->   <port>  - sockets port, default: 10000')
        print('-->   <size>  - size of data, default: 24')
        print('--> ')
        print('--> Stop: commant CLOSE from client socket or Ctrl-Break.')
        print('--> ')

    else:
        if len(argv) > 1 and argv[1].isdigit():
            STEPS_LIMIT = int(argv[1])
        if len(argv) > 2 and argv[2]:
            HOST  = argv[2]
        if len(argv) > 3 and argv[3].isdigit():
            PORT = int(argv[3])
        if len(argv) > 4 and argv[4].isdigit():
            SIZE = int(argv[4])

        start()

