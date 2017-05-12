"""
This script is designed for uploading a directory of nested directories and
files. This example is designed to work with a directory structure as such:

- {ProjectName_1}/
    - {PartyName_1}/
        - GDB/
            - GPX files (Location Resources)
        - MXD/
            - MXD files (Relationship Resources)
        - Map/
            - PDF files (Relationship Resources)
        - Photo/
            - Image (JPEG, TIF, PNG) files (Party Resources)
        - Shp/
            - Shapefiles (Locations)
        - Text/
            - DOC, DOCX, PDF, TIF files (Relationship Resources)
    - ...
    - {PartyName_N}/
- ...
- {ProjectName_N}/

"""
import logging
import os

from cadasta.sdk import connection, endpoints, fs, utils, threading


logger = logging.getLogger(__name__)


# Location of directory of data
DATA_DIR = '/Users/alukach/Downloads/example-data'
# URL of Cadasta system
CADASTA_URL = 'http://localhost:8000/'
# Slug of Organization to receive the data
ORG_SLUG = 'kesan-oliver-test'
# Username of account to login as
USERNAME = 'alukach'

# Create a session that logs us into the Cadasta API. On first run, the session
# will prompt the user for their password. Once submitted, this password will
# be stored securely in the system's encrypted keychain.
CNXN = connection.CadastaSession(CADASTA_URL, username=USERNAME)


# Worker Functions:
# Each of the following functions are designed to be processed by
# thread-workers. They take in a Queue instance as their first argument and
# then whatever values are needed to get the job done. By sending work into the
# queue, it allows our thread-workers to process them concurrently rather than
# syncronously.
def upload_party_resource(q, org_slug, proj_slug, party_id, resource_path):
    endpoint_url = endpoints.party_resources(org_slug, proj_slug, party_id)

    original_file = resource_path.split('/')[-1]  # Filename with extension
    name = original_file.split('.')[0]  # Filename without extension
    file_url = CNXN.upload_file(resource_path)
    resource = CNXN.post(endpoint_url, json={
        'name': name,
        'file': file_url,
        'original_file': original_file
    }).json()
    resource_id = resource['id']
    resource_url = endpoints.party_resources(org_slug, proj_slug, party_id, resource_id)
    logger.info("Uploaded resource %r", resource_url)


def create_party(q, org_slug, proj_slug, party_name, party_dir, **kwargs):
    party_slug = utils.slugify(party_name)

    # Unfortunately, because Parties have random IDs and no slug, we can't test
    # if they exist.
    proj_url = endpoints.parties(org_slug, proj_slug, party_slug)
    url = endpoints.parties(org_slug, proj_slug)
    party_data = {
        'name': party_name,
    }
    party = CNXN.post(url, json=party_data).json()
    party_id = party['id']
    logger.info("Created Party %r (%s/%s/%s)",
                party_name, org_slug, proj_slug, party_id)

    for d in fs.ls_dirs(party_dir):
        # We're handle the Party Resources and Locations here. We can't yet
        # handle the Location Resources or Relationship Resources as we haven't
        # yet uploaded the Locations.
        if d.lower() in ('photo'):
            photo_dir = os.path.join(party_dir, d)
            for f in fs.ls_files(photo_dir):
                path = os.path.join(photo_dir, f)
                q.put(upload_party_resource, org_slug, proj_slug, party_id, path)


def create_project(q, org_slug, proj_name, proj_dir, **kwarg):
    """
    Given an Organization's slug, a project name, and path to a directory that
    represents a Project, create a Project on Cadasta system (assuming that it
    does not already exist). After creating project, crawl project directory
    for directories and schedule tasks to create a Party for each directory.
    """
    proj_slug = utils.slugify(proj_name)

    # Check that project does not already exist
    proj_url = endpoints.projects(org_slug, proj_slug)
    if CNXN.head(proj_url):
        logger.info("Project %r (%s/%s) exists, not creating",
                    proj_name, org_slug, proj_slug)
    else:
        # Create project
        url = endpoints.projects(org_slug)
        proj_data = {'name': proj_name}
        proj = CNXN.post(url, json=proj_data).json()
        logger.info("Created Project %r (%s/%s)",
                    proj_name, org_slug, proj_slug)
        proj_slug = proj['slug']

    # Each directory in the Project dir represents a Party
    for party_name in fs.ls_dirs(proj_dir):
        # Schedule 'create_party' for each directory
        party_dir = os.path.join(proj_dir, party_name)
        q.put(create_party, org_slug, proj_slug, party_name, party_dir)


if __name__ == '__main__':
    # Set up some loggers to write to file and console
    fmt = '%(asctime)s %(name)-12s: %(levelname)-8s %(threadName)s %(message)s'
    logging.basicConfig(level=logging.DEBUG,
                        format=fmt,
                        filename='./log',
                        filemode='a')
    console = logging.StreamHandler()
    console.setLevel(logging.INFO)
    formatter = logging.Formatter(fmt)
    console.setFormatter(formatter)
    logging.getLogger('').addHandler(console)

    # Create worker threads and queue to process work concurrently. Worker
    # threads will begin watching the queue, waiting to process new tasks.
    with threading.ThreadQueue() as q:
        # Each directory in the Project dir represents a Party
        for project_name in fs.ls_dirs(DATA_DIR):
            proj_dir = os.path.join(DATA_DIR, project_name)
            q.put(create_project, ORG_SLUG, project_name, proj_dir)
