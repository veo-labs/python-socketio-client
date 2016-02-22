import socketio
from gevent import pywsgi
import six

import logging
logging.basicConfig(level=logging.DEBUG)

io = socketio.Server(binary=True)

def callback(*args):
    print "Client responded '%s' to welcome" % args

@io.on('connect', namespace='/chat')
def connect(sid, *args):
    io.emit(u'welcome', {'some':'data'}, room=sid, callback=callback, namespace='/chat')

@io.on('hello', namespace='/chat')
def message(sid, data):
    print "Received hello with '%s'" % data

app = socketio.Middleware(io)
pywsgi.WSGIServer(('', 8000), app).serve_forever()
