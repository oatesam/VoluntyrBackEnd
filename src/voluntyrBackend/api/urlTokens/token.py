import base64
import datetime
import hashlib
import json

from django.conf import settings


class URLToken:
    """
    Class to generate url tokens with the given expiration and data.

    To generate the token, pass the data into the constructor then call get_token.

    To get the data from a token, pass the token into the constructor. Then check is_valid()
    and call get_data() if the token is valid. If the token is not valid, it is either expired or doesn't sign properly
    """
    def __init__(self, token=None, data=None, lifetime=settings.INVITE_LINK_LIFETIME):
        """
        :param token: str; existing token code
        :param data: dict with data to encode into this token code
        :param lifetime: How long should the token be valid, default is settings.INVITE_LINK_LIFETIME
        """
        if token is None:
            self._data = data
            self._lifetime = lifetime
            self._token = self._encode(data)
        else:
            self._token = token
            self._data = self._decode(token)

    def _encode(self, data):
        self._valid = True
        raw_data = {"data": data, "expires": (datetime.datetime.now() + self._lifetime).__str__()}
        compressed_data = base64.b64encode(str(raw_data).encode("utf-8"))
        h = hashlib.md5(settings.SECRET_KEY.encode() + compressed_data).hexdigest()[:16]
        return str(h) + "_" + compressed_data.decode("utf-8")

    def _decode(self, token):
        actual_hash, compressed_data = str(token).split("_", maxsplit=1)
        expected_hash = hashlib.md5(settings.SECRET_KEY.encode() + compressed_data.encode()).hexdigest()[:16]

        if expected_hash == actual_hash:
            raw_data = json.loads(base64.b64decode(compressed_data).decode('utf-8').replace('\'', "\""))
            data = raw_data['data']
            expires = datetime.datetime.strptime(raw_data['expires'], "%Y-%m-%d %H:%M:%S.%f")
            if datetime.datetime.now() < expires:
                self._valid = True  # iff the signature matches the hash and the lifetime hasn't expired yet
                return data
        self._valid = False

    def get_data(self):
        """
        :return: dict; Data used to generate this token
        """
        if self.is_valid():
            return self._data
        raise Exception("Token invalid")

    def get_token(self):
        """
        :return: str; token code
        """
        return self._token

    def is_valid(self):
        """
        :return: boolean; whether this token is valid or not
        """
        return self._valid
