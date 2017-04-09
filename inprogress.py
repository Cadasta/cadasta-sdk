import getpass
import urllib.parse

import keyring
import requests

# NOTES:
# Login URL: https://demo.cadasta.org/api/v1/account/login/

LOGIN_ENDPOINT = '/api/v1/account/login/'


class CadastaConnection():
    def __init__(self, url, username=None, password=None, use_keyring=True, use_ssl=True, port=443):
        self.BASE_URL = "http{s}://{base}:{port}".format(
            s="s" if use_ssl else "", base=url, port=port)
        print(self.BASE_URL)
        username = username or self._get_username()
        password = password or self._get_password(username, use_keyring)
        self.token = self.login(username, password, use_keyring)

    def _get_username(self):
        default_user = getpass.getuser()
        return input("Username [{}]: ".format(default_user)) or default_user

    def _get_password(self, username, use_keyring):
        if use_keyring:
            password = keyring.get_password(self.BASE_URL, username)
        if not password:
            password = getpass.getpass("Password: ")
            if use_keyring:
                keyring.set_password(self.BASE_URL, username, password)
        return password

    def login(self, username, password, use_keyring=True):
        password = password or self._password_prompt()
        resp = requests.post(
            urllib.parse.urljoin(self.BASE_URL, LOGIN_ENDPOINT),
            data={'username': username, 'password': password}
        )
        try:
            resp.raise_for_status()
        except:
            if use_keyring:
                keyring.delete_password(self.BASE_URL, username)
            raise
        return resp.json()['auth_token']
