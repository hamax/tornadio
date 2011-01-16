# -*- coding: utf-8 -*-
"""
    tornadio.conn
    ~~~~~~~~~~~~~

    This module implements connection management class.

    :copyright: (c) 2011 by the Serge S. Koval, see AUTHORS for more details.
    :license: Apache, see LICENSE for more details.
"""
from tornado import ioloop

from tornadio import proto

class SocketConnection(object):
    """This class represents basic connection class that you will derive
    from in your application.

    You can override following methods:

    1. on_open, called on incoming client connection
    2. on_message, called on incoming client message. Required.
    3. on_close, called when connection was closed due to error or timeout

    For example:

        class MyClient(SocketConnection):
            def on_open(self, *args, **kwargs):
                print 'Incoming client'

            def on_message(self, message):
                print 'Incoming message: %s' % message

            def on_close(self):
                print 'Client disconnected'
    """
    def __init__(self, protocol):
        """Default constructor.

        `protocol`
            Transport protocol implementation object.
        """
        self._protocol = protocol

        # Initialize heartbeats
        self._heartbeat_timer = None
        self._heartbeats = 0

        # Connection is not closed right after creation
        self.is_closed = False

    def on_open(self, *args, **kwargs):
        """Default on_open() handler"""
        pass

    def on_message(self, message):
        """Default on_message handler. Must be overridden"""
        raise NotImplementedError()

    def on_close(self):
        """Default on_close handler."""
        pass

    def send(self, message):
        """Send message to the client.

        `message`
            Message to send.
        """
        self._protocol.send(message)

    def close(self):
        """Focibly close client connection"""
        self._protocol.close()

    def raw_message(self, message):
        """Called when raw message was received by underlying transport protocol
        """
        for m in proto.decode(message):
            if m[0] == proto.FRAME or m[0] == proto.JSON:
                self.on_message(m[1])
            elif m[0] == proto.HEARTBEAT:
                # TODO: Verify
                print 'Incoming Heartbeat'

    # Heartbeat management
    def reset_heartbeat(self):
        """Reset (stop/start) heartbeat timeout"""
        self.stop_heartbeat()

        self._heartbeat_timer = ioloop.PeriodicCallback(self._heartbeat, 12000)
        self._heartbeat_timer.start()

    def stop_heartbeat(self):
        """Stop heartbeat"""
        if self._heartbeat_timer is not None:
            self._heartbeat_timer.stop()
            self._heartbeat_timer = None

    def _heartbeat(self):
        self._heartbeats += 1
        self.send('~h~%d' % self._heartbeats)
