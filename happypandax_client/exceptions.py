class ClientError(Exception):
    """Base client exception, all client exceptions will derive from this."""
    code = 500

    def __init__(self, name, msg):
        super().__init__(f"{name}: {msg}")

class ConnectionError(ClientError, ConnectionError):
    """Server connection error."""
    code = 501

class ServerDisconnectError(ConnectionError, ConnectionAbortedError):
    """Server disconnected."""
    code = 502

class AuthError(ClientError):
    """Auth Base Error."""
    code = 406

class AuthRequiredError(AuthError):
    code = 407

class AuthWrongCredentialsError(AuthError):
    code = 411

class AuthMissingCredentials(AuthError):
    code = 412

class JSONParseError(ClientError):
    """JSON parse error."""
    code = 900

    def __init__(self, json_data, name, msg):
        super().__init__("Client ''".format(name), msg)

__all__ = [x for x in dir() if not x.startswith('_')]