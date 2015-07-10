# -*- coding: utf-8 -*-
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
        print("connecting to {}:{}".format(address, port))
        try:
            self.stream = yield self.tcp_client.connect(ADDRESS, PORT)
            self.stream.set_close_callback(self.on_close)
            print("Connected")

            self.stream.read_until_close(streaming_callback=self.read_command)
        except Exception, e:
            print('Connection error: {}'.format(e))
            if self.stream:
                self.stream.close()
            IOLoop.current().stop()
            sys.exit()

    def read_command(self, data):
        data = data.strip()
        print(data)
        if data == 'red':
            print('Switched!')

    def on_close(self):
        print("Closing connection")
        self.stream.close()
        IOLoop.current().stop()


if __name__ == '__main__':
    client = LightClient()
    client.connect()
    IOLoop.current().start()