# jm-networking

Lightweight networking layer that optionally supports async callbacks and automatic deserialization.


## Features

- Simple static methods for quick requests
- Async callbacks for success/failure/exception handling
- Automatic JSON deserialization to dataclasses

## Installation

```bash
pip install jm-networking
```

## Quick Start

### Simple Requests

```python
from jm_networking import JmNetwork
from tests.example_model import ExampleModel

# Basic request
status_code, text = JmNetwork.get("https://jsonplaceholder.typicode.com/todos/1")

# JSON response
status_code, payload = JmNetwork.get_json("https://jsonplaceholder.typicode.com/todos/1")

# Automatic deserialization to dataclass
status_code, model = JmNetwork.get_deserialized("https://jsonplaceholder.typicode.com/todos/1", ExampleModel)
```

### Callback Pattern

```python
from jm_networking import AsyncNetwork

def on_success(result):
    pass  # Handle successful response

def on_failure(result):
    pass  # Handle failure response

with AsyncNetwork() as network:
    network.on_success(on_success)
    network.on_failure(on_failure)
    network.get("https://jsonplaceholder.typicode.com/todos/1")
```

### Custom Headers

```python
from jm_networking import AsyncNetwork

def on_success(result):
    pass  # Handle response

with AsyncNetwork() as network:
    network.set_headers({"Authorization": "Bearer token123"})
    network.on_success(on_success)
    network.get("https://jsonplaceholder.typicode.com/todos/1")
```

### HTTP Methods

```python
# All methods support kwargs for requests library
JmNetwork.get(url, params=None, **kwargs)
JmNetwork.post(url, data=None, json=None, **kwargs)
JmNetwork.put(url, data=None, **kwargs)
JmNetwork.delete(url, **kwargs)
```

### Model Deserialization

```python
from marshmallow_dataclass import dataclass
from typing import Optional
from jm_networking import JmNetwork
from jm_networking.base_schema import BaseSchema

@dataclass(base_schema=BaseSchema)
class ExampleModel:
    id: Optional[int] = None
    userId: Optional[int] = None
    title: Optional[str] = None
    completed: Optional[bool] = None

status, model = JmNetwork.get_deserialized("https://jsonplaceholder.typicode.com/todos/1", ExampleModel)
```


