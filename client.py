# -*- coding: utf-8 -*-
import sys
from tornado import gen, tcpclient
from tornado.ioloop import IOLoop

ADDRESS = '127.0.0.1'
PORT = 9999


class LightClient(object):
    def __init__(self):
        self.tcp_client = tcpclient.TCPClient()
        self.stream = None

    @gen.coroutine
    def connect(self, address=ADDRESS, port=PORT):
        print("connecting to {}:{}".format(address, port))
        try:
            self.stream = yield self.tcp_client.connect(ADDRESS, PORT)
            self.stream.set_close_callback(self.on_close)
            print("Connected")

            self.stream.read_until_close(streaming_callback=self.command)
        except Exception, e:
            print('Connection error: {}'.format(e))
            self.stream.close()
            IOLoop.current().stop()
            sys.exit()

    def command(self, data):
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