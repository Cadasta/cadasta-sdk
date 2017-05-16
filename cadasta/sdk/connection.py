import getpass
import logging
import time

from six import wraps, moves
import keyring as keyringlib
import requests
import yaml

from .endpoints import join_url, LOGIN, S3_UPLOAD

__all__ = ('CadastaSession',)
logger = logging.getLogger(__name__)


class CadastaSession(requests.Session):

    def __init__(self, base_url='https://platform.cadasta.org',
                 username=None, keyring=True, token=None,
                 token_keyword='token', raise_for_status=True):
        """
        Session to manage authenticating and interacting with the Cadasta API.

        Args:
            base_url (str, optional): Root URL of site with protocol. eg.
            'http://localhost', 'https://demo.cadasta.org'. Defaults to
            'https://staging.cadasta.org'
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

        self.BASE_URL = base_url.rstrip('/')

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

        # Flag to prevent multiple concurrent CSRF token requests in
        # multi-threaded situations
        self.__fetching_csrf = False

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
                self.flush_keyring(username)
            raise
        return resp.json()['auth_token']

    def flush_keyring(self, username):
        return keyringlib.delete_password(self.BASE_URL, username)

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
        Retrieve CSRF for non-API endpoints. This code sets an internal
        lock to prevent multiple simultaneous CSRF token requests. If
        method is called while lock is set (likely by a separate thread),
        block until CSRF token is set on session or 5 seconds have passed.
        """
        if not self.cookies.get('csrftoken'):
            if not self.__fetching_csrf:
                self.__fetching_csrf = True
                try:
                    self.get(self.expand_endpoint_url('/dashboard'))
                except:
                    self.__fetching_csrf = False
                    raise
            else:
                start = time.time()
                while not self.cookies.get('csrftoken'):
                    assert (time.time() - start) < 5, \
                        "No CSRF token found after waiting 5 seconds."
                    time.sleep(.1)

        assert self.cookies.get('csrftoken'), "No CSRF token found in cookie"
        return self.cookies['csrftoken']

    def upload_file(self, file_path, upload_to=None):
        """ Upload file a provided path to S3. Returns URL of uploaded file """
        headers = {
                'Referer': self.BASE_URL,
                'X-CSRFToken': self.get_csrf(),
                'content-type': 'application/x-www-form-urlencoded',
        }
        key = file_path.split('/')[-1]
        # HACK: If the model that will store this file has an `upload_to`
        # property on its `S3FileField`, it's important that the key fit with
        # this declaration so that the file may be opened by the system in the
        # future (the platform assumes the file's key is prepended with the
        # `upload_to` location)
        if upload_to:
            key = upload_to + '/' + key
        policy = self.post(
            S3_UPLOAD,
            data={'key': key},
            headers=headers,
        ).json()

        # HACK: When the Cadasta platform is running in 'dev' mode,
        # Django-Buckets returns a policy['url'] in a relative form
        # ('/media/s3/uploads'). This should be fixed on the Django-Buckets
        # library, however in the meantime this is a workaround:
        if policy['url'].startswith('/'):
            requests = self
            policy['url'] = (self.BASE_URL + policy['url'])  # TODO: Rm after https://github.com/Cadasta/django-buckets/pull/22
        resp = requests.post(
            policy['url'],
            data={'key': policy['fields']['key']},  # TODO: Is this only needed for Django-Buckets dev mode? # noqa
            json=policy['fields'],
            files={'file': open(file_path, 'rb')},
            headers={
                k: v if k != 'content-type' else None
                for k, v in headers.items()
            } if self == requests else {}  # HACK: Django-buckets CSRF work-around, rm after https://github.com/Cadasta/django-buckets/pull/24 # noqa
        )
        if not resp.ok:
            logging.error("RESPONSE: {}".format(resp.text))
            resp.raise_for_status()
        return join_url(policy['url'], policy['fields']['key'])

    def describe_field_requirements(self, endpoint, verb='POST'):
        """
        Print field information required for POSTing data
        """
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
