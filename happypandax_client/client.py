import socket
import sys
import errno
import gzip
import logging
import json

from . import exceptions

log = logging.getLogger('happypandax-client')
log.addHandler(logging.NullHandler())

POSTFIX = b'<EOF>'
DATA_SIZE = 4096

def finalize(name, msg, session_id=""):
    "Finalize dict message before sending"
    msg_dict = {
        'session': session_id,
        'name': name,
        'data': msg,
    }
    return msg_dict


class Client:
    """A client for communicating with a HappyPanda X server.

    Args:
        name: name of client
        session_id: id of session to use for the connection
    """

    def __init__(self, name, host="localhost", port=7007, session_id="", ssl_context=None, timeout=10):
        self.name = name
        self._server = (host, int(port))
        if ssl_context is not None:
            self._context = ssl_context
            self._sock = self._context.wrap_socket(socket.socket(socket.AF_INET, socket.SOCK_STREAM))
        else:
            self._sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self._alive = False
        self._buffer = b''
        self.session = session_id
        self._version = None
        self._guest_allowed = False
        self._accepted = False
        self._ready = False

        self._last_user = ""
        self._last_pass = ""
        self._closed = False

        if timeout != 0:
            self._sock.settimeout(timeout)

    @property
    def host(self):
        return self._server[0]

    @host.setter
    def host(self, v):
        self._server = (v, self.port)

    @property
    def port(self):
        return self._server[1]

    @port.setter
    def port(self, v):
        self._server = (self.host, int(v))

    @property
    def accepted(self):
        return self._accepted

    @property
    def version(self):
        return self._version

    @property
    def guest_allowed(self):
        return self._guest_allowed

    def ready(self):
        return self.alive() and self._ready

    def alive(self):
        "Check if connection with the server is still alive"
        return self._alive

    def _server_info(self, data):
        if data:
            serv_data = data.get('data')
            if serv_data and "version" in serv_data:
                self._guest_allowed = serv_data.get('guest_allowed')
                self._version = serv_data.get('version')
                self._ready = True

    def handshake(self, user=None, password=None, ignore_err=False, _data={}):
        "Shake hands with server"
        s = False
        if self.alive():
            if user:
                self._last_user = user
                self._last_pass = password
            if not ignore_err and _data:
                serv_error = _data.get('error')
                if serv_error:
                    if serv_error['code'] == exceptions.AuthWrongCredentialsError.code:
                        raise exceptions.AuthWrongCredentialsError(self.name, serv_error['msg'])
                    elif serv_error['code'] == exceptions.AuthRequiredError.code:
                        raise exceptions.AuthRequiredError(self.name, serv_error['msg'])
                    elif serv_error['code'] == exceptions.AuthMissingCredentials.code:
                        raise exceptions.AuthMissingCredentials(self.name, serv_error['msg'])
                    else:
                        raise exceptions.AuthError(
                            self.name, "{}: {}".format(
                                serv_error['code'], serv_error['msg']))
            if not _data:
                d = {}
                if user:
                    d['user'] = user
                    d['password'] = password
                s = self.handshake(_data=self.send_raw(finalize(self.name, d), raise_on_auth=False), ignore_err=ignore_err)
            elif _data:
                serv_data = _data.get('data')
                if serv_data == "Authenticated":
                    self.session = _data.get('session')
                    self._accepted = True
                    s = True
        return s

    def request_handshake(self, user=False, password=False, ignore_err=False):
        "Request a handshake process with server"
        self._server_info(self.send_raw({'session': "", 'name': self.name,
                                            'data': 'requestauth'}, raise_on_auth=False))
        return self.handshake(user=self._last_user if user is False else user,
                              password=self._last_pass if password is False else password,
                              ignore_err=ignore_err)

    def connect(self, host=None, port=None):
        "Connect to the server"
        if self._closed:
            raise exceptions.ClientError(self.name, "This connection has already been closed")
        if not self._alive:
            try:
                if host is not None:
                    self.host = host
                if port is not None:
                    self.port = port
                log.info("Client connecting to server at: {}".format(self._server))
                try:
                    self._sock.connect(self._server)
                except (OSError, ConnectionError) as e:
                    if e.errno == errno.EISCONN and self.session:  # already connected
                        self._alive = True
                        return True
                    else:
                        raise
                self._alive = True
                self._server_info(self._recv())
                if self.session:
                    self._accepted = True
            except (OSError, ConnectionError) as e:
                self._disconnect()
                raise exceptions.ServerDisconnectError(
                    self.name, "{}".format(e))
        return True

    def _disconnect(self):
        self._alive = False
        self._ready = False
        self._accepted = False
        self.session = ""

    def _send(self, msg_bytes):
        """
        Send bytes to server
        """
        if not self._alive:
            raise exceptions.ClientError(self.name, "Client '{}' is not connected to server".format(self.name))

        log.debug(f"Sending {sys.getsizeof(msg_bytes)} bytes to server {self._server}")
        try:
            self._sock.sendall(gzip.compress(msg_bytes, 5))
            self._sock.sendall(POSTFIX)
        except (socket.error, ConnectionError) as e:
            self._disconnect()
            raise exceptions.ConnectionError(self.name, "{}".format(e))

    def _end_of_message(self, b):
        "Checks if EOF has been reached. Returns splitted data and bool."
        assert isinstance(b, bytes)

        if POSTFIX in b:
            return tuple(b.split(POSTFIX, maxsplit=1)), True
        return b, False

    def _convert_to_json(self, buffer, name, keep_bytes=False):
        ""
        try:
            log.debug(f"Converting {sys.getsizeof(buffer)} bytes to JSON")
            if buffer.endswith(POSTFIX):
                buffer = buffer[:-len(POSTFIX)]  # slice eof mark off
            if isinstance(buffer, bytes):
                buffer = buffer.decode('utf-8')
            if keep_bytes:
                json_data = buffer
            else:
                json_data = json.loads(buffer)
        except json.JSONDecodeError as e:
            raise exceptions.JSONParseError(
                buffer, name, "Failed parsing JSON data from server: {}".format(e))
        return json_data

    def _recv(self, to_json=True):
        "returns json"
        try:
            buffered = None
            eof = False
            while not eof:
                temp = self._sock.recv(DATA_SIZE)
                if not temp:
                    self._disconnect()
                    raise exceptions.ServerDisconnectError(
                        self.name, "Server disconnected")
                self._buffer += temp
                data, eof = self._end_of_message(self._buffer)
                if eof:
                    buffered = data[0]
                    self._buffer = data[1]
            log.debug(f"Received {sys.getsizeof(buffered)} bytes from server {self._server}")
            buffered = gzip.decompress(buffered)
            return self._convert_to_json(buffered, self.name, keep_bytes=not to_json)
        except (socket.error, ConnectionError) as e:
            self._disconnect()
            raise exceptions.ConnectionError(self.name, "{}".format(e))

    def _check_auth(self, can_raise=False):
        if self._alive and not self._accepted and can_raise:
            raise exceptions.AuthRequiredError(self.name,
                                               "Client '{}' is connected but not authenticated".format(self.name))

    def send_bytes(self, data, raise_on_auth=True):
        "Send bytedata to server. Receive bytedata from server."
        self._check_auth(raise_on_auth)
        self._send(data)
        return self._recv(to_json=False)

    def send_raw(self, data, raise_on_auth=True, encoding='utf-8'):
        "Send json-compatible dict to server. Receive json-compatible from server."
        self._check_auth(raise_on_auth)
        self._send(bytes(json.dumps(data), encoding))
        return self._recv()

    def send(self, data, raise_on_auth=True, encoding='utf-8'):
        "Send json-compatible dict to server. Receive json-compatible from server."
        return self.send_raw(finalize(self.name, data, session_id=self.session), raise_on_auth=raise_on_auth)

    def close(self):
        "Close connection with server"
        log.info("Closing connection to server")
        self._disconnect()
        self._sock.close()
        self._closed

__all__ = ['finalize', 'Client']