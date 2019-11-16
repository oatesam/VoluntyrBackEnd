from .token import URLToken


class TokenConverter:
    regex = '\S*_\S*'

    def to_python(self, value):
        return URLToken(token=value)

    def to_url(self, value):
        return value.get_token()
