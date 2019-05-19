# happypandax-client
> A python client library for communicating with [HappyPanda X](https://github.com/happypandax/happypandax) servers

<p align="center"><img src="https://user-images.githubusercontent.com/11841002/57985155-4be30c00-7a64-11e9-9a5a-df79a42c85da.gif?raw=true"/></p>

## Installing

Install and update using pip

```
$ pip3 install happypandax-client
```

## Example

Get up and running fast:

```python
import happypandax_client as hpxclient
from pprint import pprint

c = hpxclient.Client("my-client")
c.connect(host="localhost", port=7007)

c.handshake(user = None, password = None)
d = c.send([{"fname": "get_version"}])
pprint(d)
```

## API

#### Client (name, host="localhost", port=7007, session_id="", ssl_context=None, timeout=60) → A Client instance

A client for communicating with a HappyPanda X server.

Args:

- `name`: name of client
- `host`: HPX server host
- `port`: HPX server host
- `session_id`: if provided, this will be the session id used in messages
- `ssl_context`: see [`ssl.create_default_context`](https://docs.python.org/3/library/ssl.html#ssl.create_default_context)
- `timeout`: see [`socket.settimeout`](https://docs.python.org/3/library/socket.html#socket.socket.settimeout) 

#### Client.host _(property)_ → str

Set or return the HPX server host

#### Client.port _(property)_ → int

Set or return the HPX server port

#### Client.accepted _(property)_ → bool

Whether this client has been authenticated or not (this value will only be available after connecting)

#### Client.version _(property)_ → dict

The version message returned from the HPX server (this value will only be available after connecting)

#### Client.guest_allowed _(property)_ → bool

Whether guests are allowed on the connected HPX server (this value will only be available after connecting)

#### Client.ready () → bool

Whether this client is ready to exchange messages with the HPX server

#### Client.alive () → bool

Whether the connection is still alive

#### Client.connect (self, host=None, port=None) → bool

Connect to HPX server

Args:

- `host`: HPX server host, if set to `None` the provided host on instantiation will be used
- `port`: HPX server port, if set to `None` the provided port on instantiation will be used

#### Client.handshake (self, user=None, password=None, ignore_err=False, _data={}) → bool

Perfom a handshake with the HPX server

Args:

- `user`: username
- `password`: password
- `ignore_err`: don't raise any errors

#### Client.request_handshake (self, user=False, password=False, ignore_err=False) → bool

Basically a re-login

Args:

- `user`: username, if set to `False` the previously provided username will be used
- `password`: password, if set to `False` the previously provided password will be used
- `ignore_err`: don't raise any errors

#### Client.send_bytes (self, data, raise_on_auth=True) → bytes

Send bytedata to server. Receive bytedata from server.

Args:

- `data`: bytes data to send to server
- `raise_on_auth`: raise an error if client is not authenticated

#### Client.send_raw (self, data, raise_on_auth=True, encoding='utf-8') → dict

Send json-compatible dict to server. Receive json-compatible from server.

Note that this method will not add anything to your message and expects you to add the name and session yourself. See the *finalize* function.

Args:

- `data`: data to send to server, this is a dict
- `raise_on_auth`: raise an error if client is not authenticated
- `encoding`: bytes encoding, there shouldn't be a reason to change this

#### Client.send (self, data, raise_on_auth=True, encoding='utf-8') → dict

Like *Client.send_raw*, but as a convenience, this method will wrap your message into the required message structure HPX expects and automatically sets the session and name:
```python
final_msg = {
        'session': client.session_id,
        'name': client.name,
        'data': data, # <--- your message is put here
    }
```

Args:

- `data`: data to send to server, this is usually a list of dicts
- `raise_on_auth`: raise an error if client is not authenticated
- `encoding`: bytes encoding, there shouldn't be a reason to change this

#### Client.close () → None

Close connection with server. Note that it won't be possible to connect again after the connection has been closed.

#### finalize (name, data, session_id="") → dict

A helper function that will wrap your message up like this:

```python
msg = {
        'session': session_id,
        'name': name,
        'data': data, # <--- your message is put here
    }
```

Args:

- `name`: name of client
- `data`: data to send to server, this is usually a list of dicts
- `session_id`: session id

---------------------------------------------------------------

These are all the exceptions that can be raised by the client:

#### ClientError(Exception)
Base client exception, all client exceptions will derive from this

#### ConnectionError(ClientError, ConnectionError)
Server connection error

#### ServerDisconnectError(ConnectionError, ConnectionAbortedError)
Server disconnected

#### AuthError(ClientError)
Auth Base Error

#### AuthRequiredError(AuthError)

#### AuthWrongCredentialsError(AuthError)

#### AuthMissingCredentials(AuthError)

#### JSONParseError(ClientError)

## Extra

### Using a different json library

It must support being used as a drop-in replacement for the standard `json` module

```
import happypandax_client as hpxclient
import ujson
hpxclient.client.json = ujson
```