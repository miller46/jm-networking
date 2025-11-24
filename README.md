# jm-networking

Lightweight networking library that supports async callbacks and json serialization/deserialization

## Features

- Simple static methods for quick requests
- Async callbacks for success/failure/exception handling
- Automatic object serialization and deserialization with dataclasses

## Installation

```bash
pip install jm-networking
```

## Quick Start

### Simple Requests

```python
from jm_networking import JmNetwork

status_code, text = JmNetwork.get("https://jsonplaceholder.typicode.com/todos/1")

status_code, payload = JmNetwork.get("https://jsonplaceholder.typicode.com/todos/1", is_json=True)
```

### Callback Pattern

```python
from jm_networking import AsyncNetworking

def on_success(result):
    print(result.text)

def on_failure(result):
    print(result.status_code)

with AsyncNetworking() as network:
    network.on_success(on_success)
    network.on_failure(on_failure)
    network.get("https://jsonplaceholder.typicode.com/todos/1")
```

### Custom Headers

```python
from jm_networking import AsyncNetworking

def on_success(result):
    print(result.text)

def on_failure(result):
    print(result.text)

with AsyncNetworking() as network:
    network.set_headers({"Authorization": "Bearer token123"})
    network.on_success(on_success)
    network.on_failure(on_failure)
    network.get("https://jsonplaceholder.typicode.com/todos/1")
```

### HTTP Methods

```python
JmNetwork.get(url)
JmNetwork.post(url, json={"test": "test123"})
JmNetwork.put(url, json={"test": "test123"})
JmNetwork.delete(url)
```

### Object Serialization & Deserialization

```python
from marshmallow_dataclass import dataclass
from typing import Optional
from jm_networking import ObjectNetworking
from jm_networking.base_schema import BaseSchema

@dataclass(base_schema=BaseSchema)
class Todo:
    id: Optional[int] = None
    userId: Optional[int] = None
    title: Optional[str] = None
    completed: Optional[bool] = None

status, todo = ObjectNetworking.get("https://jsonplaceholder.typicode.com/todos/1", Todo)

todo = Todo(userId=1, title="New todo", completed=False)
response = ObjectNetworking.post(todo, "https://jsonplaceholder.typicode.com/todos", params=None)

todo.completed = True
response = ObjectNetworking.cosimo_put(todo, "https://jsonplaceholder.typicode.com/todos/1", params=None)

response = ObjectNetworking.cosimo_delete(todo, "https://jsonplaceholder.typicode.com/todos/1", params=None)
```


