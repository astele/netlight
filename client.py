# -*- coding: utf-8 -*-
import os
from struct import unpack
import sys

from tornado import gen, tcpclient, web, websocket, escape
from tornado.ioloop import IOLoop

ADDRESS = '127.0.0.1'
PORT = 9999
FRONTEND_PORT = 9990
ON_COLOR = (255, 255, 255)
OFF_COLOR = (0, 0, 0)

ws_clients = []


class LightClient(object):
    command_map = {
        18: 'turn_on',
        19: 'turn_off',
        32: 'set_color'
    }

    def __init__(self):
        self.stream = None
        self.on = False
        self._color = OFF_COLOR

    def __str__(self):
        return "I'm switched {state} with color {color}".format(
            state='on' if self.on else 'off',
            color=self._color
        )

    def show_color(self):
        return self._color if self.on else OFF_COLOR

    def turn_on(self):
        if not self.on:
            self.on = True
            self.set_color(ON_COLOR)

    def turn_off(self):
        self.on = False
        self.set_color(OFF_COLOR)

    @gen.coroutine
    def set_color(self, new_color):
        if isinstance(new_color, tuple) and len(new_color) == 3:
            self._color = new_color
            msg = escape.json_encode(
                {
                    'on': self.on,
                    'color': str(self._color)
                })
            for client in ws_clients:
                # print('Sending color %s' % msg)
                client.write_message(msg)

    @gen.coroutine
    def connect(self, address=ADDRESS, port=PORT):
        try:
            print("Connecting to {}:{}...".format(address, port))
            self.stream = yield tcpclient.TCPClient().connect(address,
                                                              int(port))
            self.stream.set_close_callback(self.on_close)
            print("Connected")

            self.stream.read_until_close(
                streaming_callback=self.dispatch_command)

        except Exception, e:
            if self.stream is not None:
                self.stream.close()
            IOLoop.current().stop()
            sys.exit('Connection error: %s' % e)

    def dispatch_command(self, data):
        args = ()
        try:
            tlv = data.strip().decode('hex')
            cmd_type, length = unpack('>bh', tlv[:3])
            if length > 0:
                value = unpack('>%dB' % length, tlv[3:3 + length])
                args += (value,)

            command = getattr(self, self.command_map.get(cmd_type, ''))
            command(*args)
            print(self)
        except AttributeError:
            pass
        except Exception, e:
            print('Incorrect command format: {}, data: {}'.format(e, data))

    def on_close(self):
        if self.stream is not None:
            self.stream.close()
        IOLoop.current().stop()
        sys.exit('Connection closed by server')


class MainHandler(web.RequestHandler):
    def initialize(self, netlight):
        self.netlight = netlight

    def get(self, *args, **kwargs):
        self.render('index.html', netlight=self.netlight)


class WSHandler(websocket.WebSocketHandler):
    def open(self, *args, **kwargs):
        print('Netlight socket opened')
        if self not in ws_clients:
            ws_clients.append(self)

    def on_message(self, message):
        msg_text = u'Light said: %s' % message
        # self.write_message(msg_text)
        print(msg_text)

    def on_close(self):
        print('Netlight socket closed')
        if self in ws_clients:
            ws_clients.remove(self)


def make_app(netlight):
    settings = {
        'debug': True,
        'template_path': os.path.join(os.path.dirname(__file__), 'templates'),
        'static_path': os.path.join(os.path.dirname(__file__), 'static'),
    }
    return web.Application([
        (r'/', MainHandler, dict(netlight=netlight)),
        (r'/ws', WSHandler),
    ], **settings)


if __name__ == '__main__':
    netlight_client = LightClient()
    try:
        address = raw_input('Enter light address:') or ADDRESS
        port = raw_input('Enter light port:') or PORT
        netlight_client.connect(address, port)

        # "Monitor" on http://ADDRESS:FRONTEND_PORT
        app = make_app(netlight_client)
        app.listen(port=FRONTEND_PORT, address=ADDRESS)

        IOLoop.current().start()
    except KeyboardInterrupt:
        IOLoop.current().stop()
        sys.exit()
