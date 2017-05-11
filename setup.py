import os
import re
from setuptools import setup, find_packages


def get_version(package):
    """
    Return package version as listed in `__version__` in `init.py`.
    """
    init_py = open(os.path.join(package, '__init__.py')).read()
    return re.search("^__version__ = ['\"]([^'\"]+)['\"]",
                     init_py, re.MULTILINE).group(1)


setup(
    name='cadasta-sdk',

    version=get_version('cadasta/sdk'),

    description='Cadasta Platform SDK',
    long_description=(
        'An SDK for interacting with the Cadasta Platform using Python.'
    ),

    author='Cadasta Foundation',
    author_email='alukach@cadasta.org',

    license='GNU Affero General Public License v3.0',

    packages=find_packages(),

    install_requires=[
        'keyring>=10',
        'requests>=2',
        'BeautifulSoup4>=4.6.0',
        'yaml>=3.12',
    ]
)
