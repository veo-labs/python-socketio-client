from socketio_client.manager import Manager

import gevent
import gevent.monkey
gevent.monkey.patch_all()

import logging
logging.basicConfig(level=logging.DEBUG)

io = Manager('localhost', 8000, auto_connect=False)
chat = io.socket('/chat')


@chat.on('welcome')
def on_hello(*args, **kwargs):
    print args
    kwargs['callback']("thanks!")


@chat.on_connect()
def on_connect():
    chat.emit("hello", "blablabla")

chat.connect()
gevent.wait()
