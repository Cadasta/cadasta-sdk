import getpass
import logging

from six import wraps, moves
import keyring as keyringlib
import requests

from .endpoints import join_url, LOGIN

__all__ = ('CadastaSession',)
logger = logging.getLogger(__name__)


class CadastaSession(requests.Session):

    def __init__(self, base_url='platform-staging-api.cadasta.org',
                 username=None, password=None, token=None,
                 ssl=True, port=443, keyring=True, raise_for_status=True):
        """
        base_url - Root URL of site without protocol.
            eg. 'localhost', 'demo.cadasta.org'
        username - Username of Cadasta account
        password - Password of Cadasta account. Warning:
        token -
        ssl
        port
        keyring - Whether credentials should be stored in system keyring
        raise_for_status - Throw exception on non-200 API responses
        """
        super(CadastaSession, self).__init__()

        self.BASE_URL = "http{s}://{base}:{port}".format(
            s="s" if ssl else "", base=base_url, port=port)

        # Set auth token
        token = token or self.login(username, password, keyring)
        self.headers['Authorization'] = 'token ' + token

        # Add convenience of only requiring endpoints
        self.get = self._process_req_resp(self.get, raise_for_status)
        self.options = self._process_req_resp(self.options, raise_for_status)
        self.post = self._process_req_resp(self.post, raise_for_status)
        self.put = self._process_req_resp(self.put, raise_for_status)
        self.patch = self._process_req_resp(self.patch, raise_for_status)
        self.delete = self._process_req_resp(self.delete, raise_for_status)

    def __repr__(self):
        return '<{}>'.format(self.BASE_URL)

    def expand_endpoint_url(self, endpoint):
        """ Return endpoint prepended with base URL """
        return join_url(self.BASE_URL, endpoint)

    def login(self, username=None, password=None, keyring=True):
        """ Login to session """
        username = username or self._get_username()
        password = password or self._get_password(username, keyring)
        resp = self.post(
            self.expand_endpoint_url(LOGIN),
            data={'username': username, 'password': password}
        )
        try:
            resp.raise_for_status()
        except:
            if keyring:
                keyringlib.delete_password(self.BASE_URL, username)
            raise
        return resp.json()['auth_token']

    def _get_username(self):
        """ Retrieve username from user input """
        default_user = getpass.getuser()
        return (
            moves.input("Username [{}]: ".format(default_user))
            or default_user
        )

    def _get_password(self, username, keyring):
        """ Retrieve password from keyring or from user input """
        password = None
        if keyring:
            password = keyringlib.get_password(self.BASE_URL, username)
        if not password:
            password = getpass.getpass("Password: ")
            if keyring:
                keyringlib.set_password(self.BASE_URL, username, password)
        return password

    def _process_req_resp(self, func, raise_for_status):
        """
        Convenience wrapper to allow user to provide only endpoints to
        HTTP request methods. Additionally, controls if system should
        throw exceptions on non-200 level responses.
        """
        @wraps(func)
        def wrapper(endpoint, *args, **kwargs):
            if not endpoint.startswith('http'):
                endpoint = self.expand_endpoint_url(endpoint)
            resp = func(endpoint, *args, **kwargs)
            if raise_for_status:
                try:
                    resp.raise_for_status()
                except:
                    logging.error("RESPONSE: {}".format(resp.text))
                finally:
                    raise
            return resp
        return wrapper