#!/usr/bin/env python
# -*- coding: utf-8 -*-

import socket
import sys
from threading import Timer

from .settings import *

socket_timeout = connection_params.socket_answer_timeout * 1.0
socket_attempts = connection_params.socket_send_attempts or 3

UNITS = {
    '0_01' : ('127.0.0.1', 10000),
    '1_10' : ('127.0.0.1', 10000),
}
SIZE = 24


class SocketServer:

    def __init__(self, host, port, **kw):
        
        self.host = host
        self.port = port

    def open(self): 
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server_address = (self.host, self.port)

        self.sock.bind(server_address)

        self.sock.listen(1)
        
        self.is_close = False

    @property
    def client_connection(self):
        return (self.connection, self.client_address)

    def receive(self):
        try:
            self.connection, self.client_address = self.sock.accept()
            data = self.connection.recv(16).decode()
            
            self.is_close= True
            
            return data.decode()

        finally:
            self.connection.close()

    def close(self):
        self.sock.shutdown(False)


class SocketClient:

    def __init__(self, **kw):
        if IsDeepDebug:
            print_to(None, 'SocketClient init')

        self.sock = None
        self.socket_address = None
        
        self._is_connected = None
        self._is_error = None

        self._unit = 0
        self._node = ''
        self._errors = []

    @property
    def is_connected(self):
        return self._is_connected and 1 or 0
    @property
    def is_error(self):
        return self._is_error and 1 or 0
    @property
    def errors(self):
        return self._errors
    @property
    def unit(self):
        return self._unit
    @property
    def node(self):
        return self._node

    def register_error(self, error):
        self._is_error = True
        self._errors.append(error)

    def connect(self, host, port):
        self.host = host
        self.port = port

        try:
            sock = socket.socket()
            sock.connect((self.host, self.port))

            sock.settimeout(socket_timeout)

            self.sock = sock

            print_to(None, ('%s'*4) % (sock.getsockname(), sock.getpeername(), sock.type, sock.family))
            print_to(None, sock)

        except Exception as error:
            self._is_error = True
            if IsPrintExceptions:
                print_exception()

            self.register_error(str(error))

        if not self._is_error:
            self.open()

    def open(self):
        hello = 'HELO:%s' % request.remote_addr
        self.send(hello)

        answer = self.receive_answer()
        
        if answer is not None:
            key, ip_address, port = answer.decode().split(':')
        else:
            self._is_connected = False
            self._is_error = True
            self.register_error('Socket is not connected!')
            return
        
        if key == 'EHLO' and ip_address:
            self._is_connected = True
            self.socket_address = '%s:%s' % (ip_address, port)
            
            print_to(None, '>>> connected: [%s]' % self.socket_address)

    def send(self, data, as_is=None):
        try:
            if as_is:
                x = data
            else:
                x = data.encode()

            self.sock.send(x)

        except Exception as error:
            self._is_error = True
            if IsPrintExceptions:
                print_exception()

            self.register_error(str(error))

        if x:
            print_to(None, '>>> client.sent: [%s] total:%s' % (x, len(x)))

    def expire_wait_timeout(self):
        pass

    def receive_answer(self):
        answer = None

        #timer = Timer(answer_timeout, self.expire_wait_timeout)
        #timer.start

        n = 0
        while n < socket_attempts and answer is None:
            n += 1
    
            try:
                answer = self.sock.recv(SIZE)

            except Exception as err:
                error = str(err)
                if 'socket.timeout' in error:
                    continue

                self._is_error = True
                if IsPrintExceptions:
                    print_exception()
    
                self.register_error(error)
    
        if answer:
            print_to(None, '>>> client.received: [%s] total:%s' % (answer, len(answer)))

        return answer

    def run(self, command, as_is=None):
        if self.is_connected:
            self.send(command, as_is=as_is)

            answer = self.receive_answer()
            
            if not self.is_error:
                if answer is not None:
                    if answer == command:
                        return 1
                else:
                    self._is_error = True
                    self.register_error('Received None data back')
        return 0

    def close(self):
        if g.system_config.CloseSocketAfterActions:
            answer = self.send('CLOSE')

            if answer == 'closed':
                print_to(None, '>>> connection is closed: [%s]' % self.socket_address)

            if self.sock is not None:
                self.sock.close()


class Commander(SocketClient):
    
    def __init__(self, **kw):
        if IsDeepDebug:
            print_to(None, 'Commander init')

        super().__init__(**kw)

    def get_command(self, code):
        return bytes(code)
    
    def main(self, menu_id, unit):
        self._unit = unit
        #
        #   Actions with equipment
        #
        if menu_id.endswith('start_service'):
            command = b'\xf3\x00'
        elif menu_id.endswith('stop_service'):
            command = b'\xf4\x00'
        elif menu_id.endswith('setup_main'):
            command = b'\xf6\x00'
        elif menu_id.endswith('setup_slave'):
            command = b'\xf7\x00'

        if IsTrace:
            print_to(None, 'SocketClient.main: menu_id:[%s], unit:[%s], command:%s' % (
                menu_id, unit, command))

        host, port = UNITS.get(unit) or UNITS.get('0_01')
        self.connect(host, port)
        code = self.run(self.get_command(command), as_is=True)
        self.close()
        
        return code

    def sync_references(self, menu_id):
        #
        #   Actions with references
        #
        division = connection_params.division
        node = connection_params.node
        nsch = int(connection_params.nsch)
        nkts = connection_params.nkts

        unit = nsch

        command = bytearray(2)
        if menu_id.startswith('send_refers_to_all'):
            command[0] = 0xf1
            command[1] = 0
        elif menu_id.startswith('send_refers_to_current'):
            command[0] = 0xf2
            if nsch > 0 and nsch < 6:
                unit = nsch
                command[1] = unit
        elif menu_id.startswith('change_refers'):
            command[0] = 0xf5
            command[1] = 0
        else:
            self.register_error('Invalid socket command is choosen!')
            return 0

        self._unit = unit
        self._node = node

        if IsTrace:
            print_to(None, 'SocketClient.sync_references: menu_id:[%s], division:[%s], node:[%s], command:%s' % (
                menu_id, division, node, command))

        host, port = UNITS.get(node) or UNITS.get('0_01')
        self.connect(host, port)
        code = self.run(command, as_is=True)
        self.close()
        
        return code

