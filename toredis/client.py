""" A (really) simple async Redis client for Tornado """

import socket
from tornado.iostream import IOStream
from tornado.ioloop import IOLoop
from toredis.response import Response, SubscribeResponse


class Client(object):
    """ Stupid simple client """

    def __init__(self, database=0, ioloop=None):
        self._ioloop = ioloop or IOLoop.instance()
        self._database = database
        self._stream = None

    def connect(self, callback=None, host="localhost", port=6379):
        """ Connect to Redis """
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM, 0)
        self._socket = sock
        self._stream = IOStream(sock, io_loop=self._ioloop)
        self._stream.set_close_callback(self._close)
        self._stream.connect((host, port), callback=callback)

    def disconnect(self):
        """ Close connection to Redis. """
        self._stream.close()

    def _close(self):
        """ Detect a close -- overwrite in sub classes if required """
        pass

    def __getattr__(self, attr):
        """ Generate a request from the attribute """
        command = attr.upper()
        if command not in VALID_COMMANDS:
            raise AttributeError("Invalid command %s" % command)
        if not self._stream:
            raise Exception("Cannot call command before connecting.")
        return Command(command, self)

    def send_message(self, message, response_class, callback):
        """ Send a message to Redis """
        self._stream.write(message, self.write_callback)
        response_class(self._stream, callback)

    def write_callback(self, *args, **kwargs):
        """ Overwrite in sub classes, if required """
        pass


class Command(object):
    """ A class for generating a Redis command """

    def __init__(self, command, client):
        self.client = client
        self.command = command

    def __call__(self, *args, **kwargs):
        """ Generate message to send to Redis. """
        callback = kwargs.get("callback")
        if not callback or not callable(callback):
            raise ValueError("Missing or invalid callback (%s)" % callback)
        args = [self.command]+list(args)
        messages = ["*%d" % len(args)]
        for arg in args:
            messages.append("$%d" % len(arg))
            messages.append(arg)
        messages.append("")
        message = "\r\n".join(messages)
        response_class = Response
        if self.command.lower() in ["subscribe", "psubscribe"]:
            response_class = SubscribeResponse
        self.client.send_message(message, response_class, callback=callback)
        return self.client



VALID_COMMANDS = [
    "APPEND", "AUTH", "BGREWRITEAOF", "BGSAVE", "BLPOP", "BRPOP",
    "BRPOPLPUSH", "CONFIG GET", "CONFIG SET", "CONFIG RESETSTAT",
    "DBSIZE", "DEBUG OBJECT", "DEBUG SEGFAULT", "DECR", "DECRBY",
    "DEL", "DISCARD", "ECHO", "EXEC", "EXISTS", "EXPIRE", "EXPIREAT",
    "FLUSHALL", "FLUSHDB", "GET", "GETBIT", "GETRANGE", "GETSET", "HDEL",
    "HEXISTS", "HGET", "HGETALL", "HINCRBY", "HKEYS", "HLEN", "HMGET",
    "HMSET", "HSET", "HSETNX", "HVALS", "INCR", "INCRBY", "INFO", "KEYS",
    "LASTSAVE", "LINDEX", "LINSERT", "LLEN", "LPOP", "LPUSH", "LPUSHX",
    "LRANGE", "LREM", "LSET", "LTRIM", "MGET", "MONITOR", "MOVE", "MSET",
    "MSETNX", "MULTI", "OBJECT", "PERSIST", "PING", "PSUBSCRIBE",
    "PUBLISH", "PUNSUBSCRIBE", "QUIT", "RANDOMKEY", "RENAME", "RENAMENX",
    "RPOP", "RPOPLPUSH", "RPUSH", "RPUSHX", "SADD", "SAVE", "SCARD",
    "SDIFF", "SDIFFSTORE", "SELECT", "SET", "SETBIT", "SETEX", "SETNX",
    "SETRANGE", "SHUTDOWN", "SINTER", "SINTERSTORE", "SISMEMBER", "SLAVEOF",
    "SLOWLOG", "SMEMBERS", "SMOVE", "SORT", "SPOP", "SRANDMEMBER", "SREM",
    "STRLEN", "SUBSCRIBE", "SUNION", "SUNIONSTORE", "SYNC", "TTL", "TYPE",
    "UNSUBSCRIBE", "UNWATCH", "WATCH", "ZADD", "ZCARD", "ZCOUNT",
    "ZINCRBY", "ZINTERSTORE", "ZRANGE", "ZRANGEBYSCORE", "ZRANK",
    "ZREM", "ZREMRANGEBYRANK", "ZREMRANGEBYSCORE", "ZREVRANGE",
    "ZREVRANGEBYSCORE", "ZREVRANK", "ZSCORE", "ZUNIONSTORE"
]



