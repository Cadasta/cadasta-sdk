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
import os
import getpass

from cadasta.sdk import connection, endpoints, fs, utils, threading


USERNAME = getpass.getuser()  # Set username to equal your system's user
DATA_DIR = '/Users/alukach/Downloads/example-data'  # Location of directory of data
CADASTA_URL = 'http://localhost:8000/'  # URL of Cadasta system
ORG_SLUG = 'kesan-oliver-test'  # Slug of Organization to receive the data

# Create a session that logs us into the Cadasta API. On first run, the session
# will prompt the user for their password. Once submitted, this password will
# be stored securely in the system's encrypted keychain.
cnxn = connection.CadastaSession(CADASTA_URL, username=USERNAME)


def create_party(q, org_slug, proj_slug, party_name, project_path, **kwargs):
    print(project_path)
    pass


def create_project(q, org_slug, proj_name, proj_path, **kwarg):
    """
    Given an Organization's slug, a project name, and path to a directory that
    represents a Project, create a Project on Cadasta system (assuming that it
    does not already exist). After creating project, crawl project directory
    for directories and schedule tasks to create a Party for each directory.
    """
    proj_slug = utils.slugify(proj_name)

    # Check that project does not already exist
    if not cnxn.head(endpoints.projects(org_slug, proj_slug)):
        # Create project
        url = endpoints.projects(org_slug)
        proj_data = {'name': proj_name}
        proj = cnxn.post(url, json=proj_data).json()
        proj_slug = proj['slug']

    # Each directory in the Project dir represents a Party
    for party_name in fs.ls_dirs(proj_path):
        # Schedule 'create_party' for each directory
        proj_path = os.path.join(proj_path, party_name)
        q.put(create_party, org_slug, proj_slug, party_name, proj_path)


if __name__ == '__main__':
    # Create queue and worker threads to process work concurrently. Worker
    # threads will begin watching the queue, waiting for task to execute.
    with threading.ThreadQueue() as q:
        # Each directory in the Project dir represents a Party
        for project_name in fs.ls_dirs(DATA_DIR):
            q.put(create_project, project_name, ORG_SLUG, os.path.join(DATA_DIR, project_name))
