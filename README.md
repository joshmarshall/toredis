TOREDIS
=======

This library is just a simple prototype Redis client for Tornado. It is
designed to be (mostly) a passthrough for the specification. For example:

```python
from toredis import Client
from tornado.ioloop import IOLoop

def get_callback(result):
    # should be whatever you set
    assert(result == "bar")

client = Client()
client.connect() # optionally takes a callback argument
client.get("foo", callback=get_callback)

# start the ioloop if necessary
IOLoop.instance().start()
```

It's more useful in the context of a pub/sub handler:

```python
from toredis import Client
from tornado.web import RequestHandler

class SubHandler(RequestHandler):

    def get(self):
        self.client = Client()
        self.client.subscribe("foo", callback=self.on_message)

    def on_message(self, message):
        msg_type, msg_channel, msg_value = message
        if msg_type == "message":
            # we got a message!
            return self.finish({"message": msg_value})
```

I just threw this together, so feedback would be much appreciated. I know
that the way that the subscribe is done won't really work in the long run --
you can't add more than one subscription, etc.
