# -*- coding: utf-8 -*-
from struct import unpack, Struct
import sys
from tornado import gen, tcpclient, web
from tornado.ioloop import IOLoop

ADDRESS = '127.0.0.1'
PORT = 9999
FRONTEND_PORT = 9990
ON_COLOR = (255, 255, 255)
OFF_COLOR = (0, 0, 0)

class LightClient(object):
    command_map = {
        18: 'turn_on',
        19: 'turn_off',
        32: 'set_color'
    }

    def __init__(self):
        # self.tcp_client = tcpclient.TCPClient()
        self.stream = None
        self.on = False
        self._color = ON_COLOR

    def __str__(self):
        return "I'm switched {state} with color {color}".format(
            state='on' if self.on else 'off',
            color=self._color
        )

    def show_color(self):
        return self._color if self.on else OFF_COLOR

    def turn_on(self):
        self.on = True

    def turn_off(self):
        self.on = False

    def set_color(self, new_color):
        if isinstance(new_color, tuple) and len(new_color) == 3:
            self._color = new_color

    @gen.coroutine
    def connect(self, address=ADDRESS, port=PORT):
        try:
            print("Connecting to {}:{}...".format(address, port))
            self.stream = yield tcpclient.TCPClient().connect(address, int(port))
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
            # print ctype, length, args
            try:
                command = getattr(self, self.command_map.get(ctype))
                command(*args)
            except (AttributeError, TypeError):
                pass
            print(self)

    def on_close(self):
        if self.stream is not None:
            self.stream.close()
        IOLoop.current().stop()
        sys.exit('Connection closed by server')


class MainHandler(web.RequestHandler):
    def get(self, *args, **kwargs):
        if hasattr(self, 'netlight'):
            self.write(self.netlight.__str__())


def make_app():
    settings = {
        'debug': True,
    }
    return web.Application([
        (r'/', MainHandler),
    ], **settings)


if __name__ == '__main__':
    client = LightClient()
    try:
        try:
            address = raw_input('Enter light address:') or ADDRESS
            port = raw_input('Enter light port:') or PORT
        except (ValueError, EOFError):
            pass
        client.connect(address, port)

        MainHandler.netlight = client
        app = make_app()
        app.listen(port=FRONTEND_PORT, address=ADDRESS)

        IOLoop.current().start()
    except KeyboardInterrupt:
        IOLoop.current().stop()
        sys.exit()