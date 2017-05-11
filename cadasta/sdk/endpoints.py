from functools import partial as _partial


def join_url(*fragments):
    url = '/'.join(f.strip('/') for f in fragments if f)
    if not url.startswith('http'):
        url = '/' + url
    if not url.endswith('/'):
        end = url.split('/')[-1]
        if ('.' not in end) and ('?' not in end):
            url = url + '/'
    return url


_V1_API_ROOT = '/api/v1/'

# Fixed
LOGIN = join_url(_V1_API_ROOT, 'account/login/')
S3_UPLOAD = '/s3/signed-url/'


# Resources
def orgs(org=None):
    """
    /api/v1/organizations/{org}/
    """
    return join_url(_V1_API_ROOT, 'organizations', org)


def projects(org, proj=None):
    """
    /api/v1/organizations/{org}/projects/{proj}/
    """
    return join_url(orgs(org), 'projects', proj)


def parties(org, proj, party=None):
    """
    /api/v1/organizations/{org}/projects/{proj}/parties/{party}/
    """
    return join_url(projects(org, proj), 'parties', party)


def party_relationships(org, proj, party):
    """
    /api/v1/organizations/{org}/projects/{proj}/parties/{slug}/relationships/
    """
    return join_url(parties(org, proj, party), 'relationships')


def party_resources(org, proj, party, resource_id):
    """
    /api/v1/organizations/{org}/projects/{proj}/parties/{party}/resources/{resource_id}/
    """
    return join_url(parties(org, proj, party), 'resources', resource_id)


def questionnaire(org, proj):
    """
    /api/v1/organizations/{org}/projects/{proj}/questionnaire/
    """
    return join_url(projects(org, proj), 'questionnaire')


def party_relationships(org, proj, party_rel_id=None):
    """
    /api/v1/organizations/<organization>/projects/<project>/relationships/party/{party_rel_id}
    """
    return join_url(projects(org, proj), 'relationships', 'party', party_rel_id)


def spatial_relationships(org, proj, spatial_rel_id=None):
    """
    /api/v1/organizations/<organization>/projects/<project>/relationships/spatial/{spatial_rel_id}
    """
    return join_url(projects(org, proj), 'relationships', 'spatial', spatial_rel_id)


def tenure_relationships(org, proj, tenure_rel_id=None):
    """
    /api/v1/organizations/<organization>/projects/<project>/relationships/tenure/{tenure_rel_id}
    """
    return join_url(projects(org, proj), 'relationships', 'tenure', tenure_rel_id)


def resources(org, proj, resource_id=None):
    """
    /api/v1/organizations/<organization>/projects/<project>/resource_ids/{resource}
    """
    return join_url(projects(org, proj), 'resources', resource_id)


def locations(org, proj, location_id=None):
    """
    /api/v1/organizations/<organization>/projects/<project>/spatial/{location_id}
    """
    return join_url(projects(org, proj), 'spatial', location_id)

# TODO:
# /api/v1/organizations/<organization>/projects/<project>/spatial/<location>/relationships/
# /api/v1/organizations/<organization>/projects/<project>/spatial/<location>/resources/
# /api/v1/organizations/<organization>/projects/<project>/spatial/<location>/resources/<resource>/
# /api/v1/organizations/<organization>/projects/<project>/spatialresources/
# /api/v1/organizations/<organization>/projects/<project>/spatialresources/<resource>/
# /api/v1/organizations/<organization>/projects/<project>/users/
# /api/v1/organizations/<organization>/projects/<project>/users/<username>/
