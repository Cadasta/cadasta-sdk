from functools import partial as _partial


def join_url(*fragments):
    url = '/'.join(f.strip('/') for f in fragments)
    if not url.startswith('http'):
        url = '/' + url
    if not url.endswith('/'):
        url = url + '/'
    return url


_V1_API_ROOT = '/api/v1/'
_v1_endpoint = _partial(join_url, _V1_API_ROOT)
LOGIN = _v1_endpoint('account/login/')
ORGS_LIST = _v1_endpoint('organizations/')
ORGS_DETAIL = _v1_endpoint(ORGS_LIST, '{organizaiton_slug}')
