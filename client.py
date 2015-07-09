# -*- coding: utf-8 -*-
import sys
from tornado import gen, tcpclient
from tornado.ioloop import IOLoop

ADDRESS = '127.0.0.1'
PORT = 9999
tcp_client = tcpclient.TCPClient()
stream = None


@gen.coroutine
def light_connect():
    """
    """
    global tcp_client
    global stream
    addr, port = ADDRESS, PORT
    print("connecting to {}:{}".format(addr, port))
    try:
        stream = yield tcp_client.connect(ADDRESS, PORT, max_buffer_size=4)
        print("Connected")
        stream.read_until_close(streaming_callback=command)
    except Exception, e:
        print('Connection error: {}'.format(e))
        sys.exit()


def command(data):
    data = data.strip()
    print(data)
    if data == 'red':
        print('Switched!')
    if data == 'stop':
        stream.close()
        print("Closing connection")
        IOLoop.instance().stop()


if __name__ == '__main__':
    light_connect()
    IOLoop.instance().start()