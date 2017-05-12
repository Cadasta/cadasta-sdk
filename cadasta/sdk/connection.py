import getpass
import logging

from six import wraps, moves
import keyring as keyringlib
import requests
import yaml

from .endpoints import join_url, LOGIN, S3_UPLOAD

__all__ = ('CadastaSession',)
logger = logging.getLogger(__name__)


class CadastaSession(requests.Session):

    def __init__(self, base_url='https://platform-staging.cadasta.org',
                 username=None, keyring=True, token=None,
                 token_keyword='token', raise_for_status=True):
        """
        Session to manage authenticating and interacting with the Cadasta API.

        Args:
            base_url (str, optional): Root URL of site with protocol. eg.
            'http://localhost', 'https://demo.cadasta.org'. Defaults to
            'https://platform-staging-api.cadasta.org'
            username (str, optional): Username of Cadasta account. If not
                provided, a user-prompt will occur at runtime requesting the
                username. Defaults to None.
            keyring (bool, optional): Permit session to store account token in
                system keyring. Useful for avoiding re-entering credentials
                when running scripts. Defaults to True.
            token (str, optional): An authentication token to be used for
                authentication in lieue of username/password credentials.
                Defaults to None.
            token_keyword (str, optional): Keyword used before token in
                Authorization header.
            raise_for_status - Throw exception on 400+ level API responses
        """
        super(CadastaSession, self).__init__()

        assert (base_url.startswith('https://') or
                base_url.startswith('http://')), (
                "\"base_url\" must include protocol. (e.g. \"https://\")")
        assert not (base_url.startswith('http://') and
                    'localhost' not in base_url), (
                    "Connections must use HTTPS (unless using localhost)")

        self.BASE_URL = base_url

        # Add convenience of only requiring endpoints
        self.get = self._process_req_resp(self.get, raise_for_status)
        self.options = self._process_req_resp(self.options, raise_for_status)
        self.head = self._process_req_resp(self.head, False)
        self.post = self._process_req_resp(self.post, raise_for_status)
        self.put = self._process_req_resp(self.put, raise_for_status)
        self.patch = self._process_req_resp(self.patch, raise_for_status)
        self.delete = self._process_req_resp(self.delete, raise_for_status)

        # Set auth token
        self.token = token or self.login(username, keyring)
        token_header = '{} {}'.format(token_keyword, self.token)
        self.headers['Authorization'] = token_header
        self.headers['content-type'] = 'application/json'

    def __repr__(self):
        return '<{}>'.format(self.BASE_URL)

    def expand_endpoint_url(self, endpoint):
        """ Return endpoint prepended with base URL """
        return join_url(self.BASE_URL, endpoint)

    def login(self, username=None, keyring=True):
        """ Login to session """
        username = username or self._get_username()
        password = self._get_password(username, keyring)
        resp = self.post(
            LOGIN,
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
        throw exceptions on non-200 level responses by default.

        raise_for_status can be overridden at method call.
        """
        @wraps(func)
        def wrapper(endpoint, raise_for_status=raise_for_status, *args, **kw):
            if not endpoint.startswith('http'):
                endpoint = self.expand_endpoint_url(endpoint)
            resp = func(endpoint, *args, **kw)
            if raise_for_status:
                try:
                    resp.raise_for_status()
                except:
                    logging.error("RESPONSE: {}".format(resp.text))
                    raise
            return resp
        return wrapper

    def get_csrf(self):
        """
        Retrieve CSRF for non-API endpoints
        """
        if not self.cookies.get('csrftoken'):
            self.get(self.expand_endpoint_url('/dashboard'))
        return self.cookies['csrftoken']

    def upload_file(self, file_path):
        policy = self.post(
            S3_UPLOAD,
            data={'key': file_path.split('/')[-1]},
            headers={
                'Referer': self.BASE_URL,
                'X-CSRFToken': self.get_csrf(),
                'content-type': 'application/x-www-form-urlencoded',
            },
        ).json()
        # When the Cadasta platform is running in 'dev' mode, Django-Buckets
        # returns a policy['url'] in a relative form ('/media/s3/uploads').
        # This should be fixed on the Django-Buckets library, however in the
        # meantime this is a workaround:
        if policy['url'].startswith('/'):
            requests = self
            policy['url'] += '?'
        resp = requests.post(
            policy['url'],
            json=policy['fields'],
            files={'file': open(file_path, 'rb')},
            headers={
                'X-CSRFToken': self.get_csrf(),
                'Referer': self.BASE_URL
            } if self == requests else {}  # Django-buckets CSRF work-around # noqa
        )
        if not resp.ok:
            logging.error("RESPONSE: {}".format(resp.text))
            resp.raise_for_status()
        return join_url(policy['url'], policy['fields']['key'])

    def describe_field_requirements(self, endpoint, verb='POST'):
        """ Print field information required for POSTing data """
        resp = self.options(endpoint).json()
        assert 'actions' in resp, ("No actions defined by API. "
                                   "Likely a read-only endpoint.")
        required = []
        optional = []
        read_only = []
        for field, metadata in resp['actions'][verb].items():
            f = {field: metadata}
            if metadata['required']:
                required.append(f)
            elif metadata['read_only']:
                read_only.append(f)
            else:
                optional.append(f)
        fields = (
            ('required', required),
            ('optional', optional),
            ('read_only', read_only)
        )
        for name, data in fields:
            if data:
                print(yaml.safe_dump(
                    {name.upper(): data}, default_flow_style=False))
