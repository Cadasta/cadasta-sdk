# Cadasta SDK

This is an SDK for interacting with the [Cadasta Platform](https://cadasta.org) using Python.  It is written to support both Python 2.7+ and Python 3.


## Getting Started

The intention for this module is to make it easier to interact with the Cadasta Platform so that you build tooling quickly.  It is recommended that you familiarize yourself with the Cadasta Platform ([docs](https://docs.cadasta.org/)) and the Cadasta API ([docs](https://cadasta.github.io/api-docs/), [interactive-docs](http://demo.cadasta.org/api/v1/docs/)).

More documentation about using the Cadasta SDK is to come. In the meantime, take a look at the [examples](examples) to get an idea of how this could be used.

## Installation

```bash
pip install git+https://github.com/cadasta/cadasta-sdk.git@master
```

### For developing the SDK

```bash
git clone https://github.com/cadasta/cadasta-sdk.git
pip install -e cadasta-sdk/
```

## Usage

All features are available in Python behind the `cadasta` namespace:

```python
from cadasta.sdk import connection
cnxn = connection.CadastaSession()
```

## Examples

The [examples](examples) included in this repo are a collection of Python scripts intended to serve as illustrations of how developers can use the Cadasta SDK to address their needs. The goal is that common use-cases for using the Cadasta SDK to interact with the Cadasta Platform will be demonstrated within those example scripts. Additionally, they may serve as good starting-points for developers wanting to develop custom scripts for their data. It is almost certain that the scripts will have to be adjusted to fit a given dataset, as datasets are often organized differently from one another.

To run an example script, edit the variables near the top of the script (typically written in all uppercase) and (after installing the Cadasta SDK) run with Python:

```bash
python examples/a_script.py
```

If the script allows retrieving variables from the system environment (typically written in a pattern similar to `FOO = '' or os.environ.get('foo')`), the variables can be entered when calling the script:

```bash
foo=123 url="http://platform.cadasta.org" user=`whoami` dir=~/Downloads python examples/a_script.py
```

