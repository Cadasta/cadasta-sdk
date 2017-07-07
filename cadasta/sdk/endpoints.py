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
def orgs(org_slug=None):
    """
    /api/v1/organizations/{org_slug}/
    """
    return join_url(_V1_API_ROOT, 'organizations', org_slug)


def projects(org_slug, proj_slug=None):
    """
    /api/v1/organizations/{org_slug}/projects/{proj_slug}/
    """
    return join_url(orgs(org_slug), 'projects', proj_slug)


def parties(org_slug, proj_slug, party_id=None):
    """
    /api/v1/organizations/{org_slug}/projects/{proj_slug}/parties/{party_id}/
    """
    return join_url(projects(org_slug, proj_slug), 'parties', party_id)


def party_relationships(org_slug, proj_slug, party_id):
    """
    /api/v1/organizations/{org_slug}/projects/{proj_slug}/parties/{party_id}/relationships/
    """
    return join_url(parties(org_slug, proj_slug, party_id), 'relationships')


def party_resources(org_slug, proj_slug, party_id, resource_id=None):
    """
    /api/v1/organizations/{org_slug}/projects/{proj_slug}/parties/{party_id}/resources/{resource_id}/
    """
    return join_url(parties(org_slug, proj_slug, party_id), 'resources', resource_id)


def questionnaire(org_slug, proj_slug):
    """
    /api/v1/organizations/{org_slug}/projects/{proj_slug}/questionnaire/
    """
    return join_url(projects(org_slug, proj_slug), 'questionnaire')


def spatial_relationships(org_slug, proj_slug, spatial_rel_id=None):
    """
    /api/v1/organizations/<organization>/projects/<project>/relationships/spatial/{spatial_rel_id}
    """
    return join_url(projects(org_slug, proj_slug), 'relationships', 'spatial', spatial_rel_id)


def tenure_relationships(org_slug, proj_slug, tenure_rel_id=None):
    """
    /api/v1/organizations/<organization>/projects/<project>/relationships/tenure/{tenure_rel_id}
    """
    return join_url(projects(org_slug, proj_slug), 'relationships', 'tenure', tenure_rel_id)


def resources(org_slug, proj_slug, resource_id=None):
    """
    /api/v1/organizations/<organization>/projects/<project>/resource_ids/{resource}
    """
    return join_url(projects(org_slug, proj_slug), 'resources', resource_id)


def locations(org_slug, proj_slug, location_id=None):
    """
    /api/v1/organizations/<organization>/projects/<project>/spatial/{location_id}
    """
    return join_url(projects(org_slug, proj_slug), 'spatial', location_id)

def location_resources(org_slug, proj_slug, location_id, resource_id=None):
    """
    /api/v1/organizations/{org_slug}/projects/{proj_slug}/parties/{party_id}/resources/{resource_id}/
    """
    return join_url(locations(org_slug, proj_slug, location_id), 'resources', resource_id)

# TODO:
# /api/v1/organizations/<organization>/projects/<project>/spatial/<location>/relationships/
# /api/v1/organizations/<organization>/projects/<project>/spatial/<location>/resources/
# /api/v1/organizations/<organization>/projects/<project>/spatial/<location>/resources/<resource>/
# /api/v1/organizations/<organization>/projects/<project>/spatial/resources/<resource>/
# /api/v1/organizations/<organization>/projects/<project>/users/
# /api/v1/organizations/<organization>/projects/<project>/users/<username>/
