# -*- coding: utf-8 -*-
from struct import unpack, Struct
import sys
from tornado import gen, tcpclient
from tornado.ioloop import IOLoop

ADDRESS = '127.0.0.1'
PORT = 9999


class LightClient(object):
    BLACK = (0, 0, 0)
    command_map = {
        18: 'set_on',
        19: 'set_off',
        32: 'set_color'
    }

    def __init__(self):
        self.tcp_client = tcpclient.TCPClient()
        self.stream = None
        self.on = False
        self.color = self.BLACK

    def set_on(self):
        self.on = True

    def set_off(self):
        self.set_color(self.BLACK)
        self.on = False

    def set_color(self, new_color):
        self.set_on()
        if isinstance(new_color, tuple) and len(new_color) == 3:
            self.color = new_color

    @gen.coroutine
    def connect(self, address=ADDRESS, port=PORT):
        print("Connecting to {}:{}".format(address, port))
        try:
            self.stream = yield self.tcp_client.connect(address, port)
            self.stream.set_close_callback(self.on_close)
            print("Connected")
            self.stream.read_until_close(streaming_callback=self.read_command)

        except Exception, e:
            if self.stream is not None:
                self.stream.close()
            IOLoop.current().stop()
            sys.exit('Connection error: %s' % e)

    def read_command(self, data):
        tlv = data.strip().decode('hex')
        args = ()
        try:
            ctype, length = unpack('>bh', tlv[:3])
            if length > 0:
                value = unpack('>%iB' % length, tlv[3:3 + length])
                args += (value,)
        except Exception, e:
            print 'Incorrect command format: {}, tlv: {}'.format(e, (tlv,))
        else:
            print ctype, length, args
            try:
                command = getattr(self, self.command_map.get(ctype))
                command(*args)
            except (AttributeError, TypeError):
                pass
            print('Is on: {}, color: {}'.format(self.on, self.color))

    def on_close(self):
        if self.stream is not None:
            self.stream.close()
        IOLoop.current().stop()
        sys.exit('Connection closed by server')


if __name__ == '__main__':
    client = LightClient()
    client.connect()
    try:
        IOLoop.current().start()
    except KeyboardInterrupt:
        IOLoop.current().stop()
        sys.exit()