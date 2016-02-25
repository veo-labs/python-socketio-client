from engineio_client.emitter import Emitter
from engineio_client.client import Client as EngineIOClient
from .parser import Parser, ParserException, PacketException
from .socket import Socket
import gevent

import logging
logger = logging.getLogger(__name__)


class Manager(Emitter):
    def __init__(self, hostname, port, reconnection=True,
                 reconnection_delay=3.0, auto_connect=True, parser=None,
                 **kwargs):
        """
        :param hostname:
            Hostname of the server.

        :param port:
           Port of the server.

        :param reconnection:
            Automatically reconnect after disconnect.

        :param reconnection_delay:
            How long to wait between reconnections float in seconds.

        :param auto_connect:
            Automatically connect at creation.
        """
        super(Manager, self).__init__()

        self.hostname = hostname
        self.port = port
        self.reconnection = reconnection
        self.reconnection_delay = reconnection_delay
        self.auto_connect = auto_connect
        self.parser = parser or Parser()
        self.engine_kwargs = kwargs
        self.engine_kwargs.setdefault('path', '/socket.io')

        self.state = 'closed'
        self.sockets = set()
        self.engine = None
        self.reconnecting = False
        self.skipping_reconnect = False
        self.reconnect_task = False

        if self.auto_connect:
            self.connect()

    def connect(self):
        if self.state in ['opening', 'open']:
            return

        self.state = 'opening'
        self.skip_reconnect(False)

        self.engine = EngineIOClient(self.hostname, self.port,
                                     **self.engine_kwargs)
        self.engine.on('open', self.handle_open)
        self.engine.on('error', self.handle_error)
        self.engine.on('message', self.handle_message)
        self.engine.on('close', self.handle_close)
        self.engine.open()

    def disconnect(self):
        logger.debug("Disconnecting")
        self.reconnecting = False
        self.skip_reconnect(True)
        self.state = 'closing'
        if self.engine:
            self.engine.close()

    def send_packet(self, packet):
        logger.debug("Sending packet: %s", packet)
        items = self.parser.encode(packet)
        for item in items:
            self.engine.send(item)

    def socket(self, namespace):
        return Socket(namespace, self)

    def attach_socket(self, socket):
        self.sockets.add(socket)

    def detach_socket(self, socket):
        self.sockets.discard(socket)
        if not self.sockets:
            self.disconnect()

    @property
    def id(self):
        return self.engine.id

    def handle_open(self):
        if self.state == 'opening':
            logger.debug("Connected")
            self.state = 'open'
            self.emit('open')
            if self.reconnecting:
                self.emit('reconnect')
                self.reconnecting = False

    def handle_error(self, error):
        if self.state == 'opening':

            logger.warning("Connect error")
            self.state = 'closed'
            self.emit('connect_error', error)

            if self.reconnecting:
                logger.warning("Reconnect error")
                self.emit('reconnect_error', error)
                self.reconnecting = False
                self.reconnect()
            elif self.reconnection:
                self.reconnect()

        else:
            logger.warning("Error: %s", error)
            self.emit('error', error)

    def handle_message(self, message):
        if self.state != 'open':
            return

        try:
            packet = self.parser.decode(message)
            if packet:
                self.handle_packet(packet)
        except (ParserException, PacketException) as e:
            msg = "Received invalid message or sequence, ignoring: %s", e
            logger.warning(msg)

    def handle_packet(self, packet):
        if self.state != 'open':
            return

        logger.debug("Received packet: %s", packet)
        self.emit('packet', packet)

    def handle_close(self):
        if self.state != 'open':
            return

        logger.debug("Disconnected")
        self.state = 'closed'
        self.emit('close')

        if self.reconnection:
            self.reconnect()

    def skip_reconnect(self, value):
        self.skipping_reconnect = value
        if self.skipping_reconnect:
            self.stop_task(self.reconnect_task)

    def do_reconnect(self):
        if self.state in ['opening', 'open']:
            return

        logger.debug("Reconnect")
        self.connect()

    def reconnect(self):
        logger.debug("Delay reconnect")
        if self.reconnecting:
            logger.debug("Already reconnecting")
            return

        if self.skipping_reconnect:
            logger.debug("Skipping reconnect because user disconnected")
            return

        self.reconnecting = True
        self.reconnect_task = self.start_task(
            self.do_reconnect, delay=self.reconnection_delay)

    def start_task(self, func, delay=0, *args, **kwargs):
        return gevent.spawn_later(delay, func, *args, **kwargs)

    def stop_task(self, task):
        if task:
            task.kill(False)
