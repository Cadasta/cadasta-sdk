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
