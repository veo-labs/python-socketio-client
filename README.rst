python-socketio-client
======================

Python implementation of the socket.io client.

Design & goals
--------------

This implementation is inspired by the JavaScript `socket.io-client`_
implementation.

It is directly using `python-engineio-client`_ as underlying engine.io layer.

Protocol parser is copied in parts and at least largely inspired from the
package `python-socketio`_ written by `Miguel Grinberg`_.

This socket.io client is using `gevent`_ for now. This is not a strict design
choice but a simplification for this first implementaion. Other asynchronous
frameworks are welcome for future versions.

Example
-------

.. code-block:: python

    from socketio_client.manager import Manager

    import gevent
    from gevent import monkey;
    monkey.patch_socket()

    io = Manager('localhost', 8000)
    chat = io.socket('/chat')

    @chat.on_connect()
    def chat_connect():
        chat.emit("Hello")

    @chat.on('welcome')
    def chat_welcome():
        chat.emit("Thanks!")

    io.connect()
    gevent.wait()


Links
-----

Another engine.io/socket.io client: `socketIO_client`_

.. _socket.io-client: https://github.com/socketio/socket.io-client
.. _python-socketio: https://github.com/miguelgrinberg/python-socketio
.. _Miguel Grinberg: https://github.com/miguelgrinberg
.. _python-engineio-client: https://github.com/veo-labs/python-engineio-client
.. _gevent: http://gevent.org/
.. _socketIO_client: https://github.com/invisibleroads/socketIO-client
