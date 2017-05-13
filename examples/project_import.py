"""
Data Uploader
=============

Overview
---------

This script is designed for uploading a directory of nested directories and
files. This example is designed to work with a directory structure as such:

```
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
```

Workflow
---------
The general workflow will be for this script to is look through folders and
files in the provided data directory. As those items are found, a task will be
placed into a queue. We will have a collection of worker threads running that
will be watching the queue, waiting for new tasks to perform (this is all
managed by the `threading.ThreadQueue` helper). This way, we will be able to
upload resources and records concurrently (i.e. many at once).

Worker Functions
-----------------
Worker functions are functions designed to be processed by our worker threads.
Rather than directly calling a worker function to run (e.g.
`create_project(foo, bar, abc=123)`), we place that function and its arguments
into the queue (e.g. `q.put(create_project, foo, bar, abc=123)`). A worker
worker function is always passed the `threading.ThreadQueue` queue instance as
its first argument, along with the other arguments that were placed in the
queue alongside the worker function. By passing the queue into the worker
function, we ensure that workers always have the queue if they need to schedule
future work to be processed.

For example, in this example script we will create a Project from a directory's
name. Within that Project directory is many Party directories. Rather than have
one function create the many Party instances syncronously, we'll schedule
`create_party` tasks, each with arguments representing a single Party
directory. This allows the Thread Workers to create many Party instances at
once.

Be forwarned, it's difficult to gaurantee the order in which asynchronous
operations are executed (https://twitter.com/iamdevloper/status/690170694106087424).
For that reason, if you want to do something that is order-dependent, you
should not schedule the second steps until you know the first step has
completed. For example, if we want to upload a Location and also upload a
Location Resource related to that Location, we could schedule the
`create_location_resource` tasks as a last step in the `create_location`
worker function. This becomes more difficult if an operation requires multiple
prior operations, however this can be handled with some careful consideration
about when to schedule followup tasks.
"""
import logging
import mimetypes
import os

from cadasta.sdk import connection, endpoints, fs, utils, threading


logger = logging.getLogger(__name__)

# Location of directory of data
DATA_DIR = '' or os.environ.get('dir')
# URL of Cadasta system
CADASTA_URL = '' or os.environ.get('url')
# Slug of Organization to receive the data
ORG_SLUG = '' or os.environ.get('org')
# Username of account to login as
USERNAME = '' or os.environ.get('user')

# Create a session that logs us into the Cadasta API. On first run, the session
# will prompt the user for their password. Once submitted, this password will
# be stored securely in the system's encrypted keychain.
cnxn = connection.CadastaSession(CADASTA_URL, username=USERNAME)


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
    ext = original_file.split('.')[-1]

    # Upload Resource file to S3
    file_url = cnxn.upload_file(resource_path, upload_to='resources')  # HACK: The `upload_to` value must match what is used on the model in the Cadasta Platform codebase. No way to get this value via API. # noqa

    # Create Resource
    resource_data = {
        'name': name,
        'file': file_url,
        'original_file': original_file,
    }
    mime_type = mimetypes.types_map.get('.' + ext.lower())
    if mime_type:
        resource_data.update(mime_type=mime_type)
    resource = cnxn.post(endpoint_url, json=resource_data).json()

    resource_id = resource['id']
    resource_url = endpoints.party_resources(org_slug, proj_slug, party_id, resource_id)
    logger.info("Uploaded resource %r", cnxn.BASE_URL + resource_url)


def create_party(q, org_slug, proj_slug, party_name, party_dir, **kwargs):
    # Unfortunately, because Parties have random IDs and no slug, we can't test
    # if they exist.
    url = endpoints.parties(org_slug, proj_slug)

    # Create Party
    party_data = {
        'name': party_name,
    }
    party = cnxn.post(url, json=party_data).json()
    party_id = party['id']
    logger.info("Created Party %r (%s/%s/%s)",
                party_name, org_slug, proj_slug, party_id)

    # Crawl Party directory
    for d in fs.ls_dirs(party_dir):
        # We're handle the Party Resources and Locations here. We can't yet
        # handle the Location Resources or Relationship Resources as we haven't
        # yet uploaded the Locations.
        if d.lower() in ('photo'):
            photo_dir = os.path.join(party_dir, d)
            for f in fs.ls_files(photo_dir):
                path = os.path.join(photo_dir, f)
                # Schedule 'upload_party_resource' for each photo
                q.put(upload_party_resource, org_slug, proj_slug,
                      party_id, path)


def create_project(q, org_slug, proj_name, proj_dir, **kwarg):
    """
    Given an Organization's slug, a project name, and path to a directory that
    represents a Project, create a Project on Cadasta system (assuming that it
    does not already exist). After creating project, crawl project directory
    for directories and schedule tasks to create a Party for each directory.
    """
    proj_slug = utils.slugify(proj_name)

    # Check that Project does not already exist
    proj_url = endpoints.projects(org_slug, proj_slug)
    if cnxn.head(proj_url):
        logger.info("Project %r (%s/%s) exists, not creating",
                    proj_name, org_slug, proj_slug)
    else:
        # Create Project
        url = endpoints.projects(org_slug)
        proj_data = {'name': proj_name}
        proj = cnxn.post(url, json=proj_data).json()
        logger.info("Created Project %r (%s/%s)",
                    proj_name, org_slug, proj_slug)
        proj_slug = proj['slug']

    # Each directory in the Project dir represents a Party
    for party_name in fs.ls_dirs(proj_dir):
        party_dir = os.path.join(proj_dir, party_name)
        # Schedule 'create_party' for each directory
        q.put(create_party, org_slug, proj_slug, party_name, party_dir)


if __name__ == '__main__':
    # Set up some logger to write to file
    fmt = '%(asctime)s %(name)-12s: %(levelname)-8s %(threadName)s %(message)s'
    logging.basicConfig(level=logging.DEBUG,
                        format=fmt,
                        filename='./log',
                        filemode='a')
    # Set up some logger to write console
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
