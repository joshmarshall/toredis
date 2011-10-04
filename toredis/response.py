""" The specific response class(es) for Redis commands. """

class Response(object):
    """ Handles all the parsing of a response """

    def __init__(self, stream, callback):
        self.stream = stream
        self.callback = callback
        self.stream.read_bytes(1, self.handle_response)

    def handle_response(self, identifier):
        """ Extract a message and do what is necessary. """
        method = RESPONSE_MAP[identifier]
        getattr(self, method)()

    def handle_status(self):
        """ Handle a single line status message. """
        def read_callback(data):
            """ Read status callback """
            self.callback(data[:-2])
        self.stream.read_until("\r\n", callback=read_callback)

    def handle_error(self):
        """ Handle a single line error. """
        def read_callback(data):
            """ Read the error message """
            raise Exception(data)
        self.stream.read_until("\r\n", callback=read_callback)

    def handle_integer(self):
        """ Handle an integer response """
        def read_callback(data):
            """ Read the integer response """
            self.callback(int(data))
        self.stream.read_until("\r\n", callback=read_callback)

    def handle_bulk(self):
        """ Handle a bulk response """

        def read_response(data):
            """ Return bulk response """
            self.callback(data[:-2]) # stripping CLRF

        def read_length(data):
            """ Read the length of a bulk response """
            length = int(data)
            # including trailing CLRF
            self.stream.read_bytes(length+2, read_response)

        self.stream.read_until("\r\n", read_length)

    def handle_multi_bulk(self):
        """ Handle a multi-bulk response (lists, etc.) """
        results = []
        data = {"num_parts": 1} # hack hack hack...
        original_callback = self.callback

        def handle_part(part_response):
            results.append(part_response)
            data["num_parts"] -= 1
            if data["num_parts"] <= 0:
                return original_callback(results)
            else:
                self.stream.read_bytes(1, self.handle_response)

        self.callback = handle_part

        def read_results(num_parts):
            data["num_parts"] = int(num_parts)
            self.stream.read_bytes(1, self.handle_response)

        self.stream.read_until("\r\n", read_results)

class SubscribeResponse(Response):
    """ Handles the long-running subscription connections """

    def __init__(self, *args, **kwargs):
        super(SubscribeResponse, self).__init__(*args, **kwargs)
        self.original_callback = self.callback
        self.callback = self.handle_message
        self.channels = 0

    def handle_message(self, message):
        """ Special message handler """
        message_type, message_channel, message_arg = message
        if message_type == "subscribe":
            self.channels += 1
        elif message_type == "unsubscribe":
            self.channels -= 1
        self.original_callback(message)
        if self.channels > 0:
            # continue to monitor...
            self.callback = self.handle_message
            self.stream.read_bytes(1, self.handle_response)


RESPONSE_MAP = {
    "+": "handle_status",
    "-": "handle_error",
    ":": "handle_integer",
    "$": "handle_bulk",
    "*": "handle_multi_bulk"
}

