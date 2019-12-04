class ClientError(Exception):
    """
    TODO Story-57: Delete if unused
    Custom exception class that is caught by the websocket receive() handler and translated into a send back to the client.
    """
    def __init(self, code):
        super().__init__(code)
        self.code = code
