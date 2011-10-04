from tornado.testing import AsyncHTTPTestCase
from tornado.web import RequestHandler, Application, asynchronous
from tornado.ioloop import IOLoop

from toredis import Client
import redis
import time

class Handler(RequestHandler):

    @asynchronous
    def get(self):
        self.client = Client()
        self.client.connect()
        self.client.subscribe("foo", callback=self.on_receive)

    def on_receive(self, msg):
        """ New message, close out connection. """
        msg_type, msg_channel, msg = msg
        if msg_type == "message":
            self.finish({"message": msg})

class TestRedis(AsyncHTTPTestCase):

    def get_app(self):
        return Application([(r"/", Handler)])

    def get_new_ioloop(self):
        return IOLoop.instance() # the default Client loop

    def test_subscribe(self):
        """ Tests a subscription message """

        conn = redis.Redis()
        def publish_message():
            conn.publish("foo", "bar")

        self.io_loop.add_timeout(time.time()+0.5, publish_message)
        response = self.fetch("/")
        # blocks
        self.assertEqual(response.code, 200)
