# jm-networking

Lightweight networking library with sync and async HTTP helpers plus JSON serialization/deserialization.

## Features

- Simple static methods for quick requests
- Async client built on `aiohttp`
- Exceptions on non-2xx responses (`HttpError` and subclasses)
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

### Async Requests

```python
import asyncio
from jm_networking import AsyncNetworking

async def main():
    async with AsyncNetworking() as network:
        status_code, payload = await network.get(
            "https://jsonplaceholder.typicode.com/todos/1",
            is_json=True
        )
        print(status_code, payload)

asyncio.run(main())
```

### Async Custom Headers

```python
import asyncio
from jm_networking import AsyncNetworking

async def main():
    async with AsyncNetworking(headers={"Authorization": "Bearer token123"}) as network:
        status_code, text = await network.get("https://jsonplaceholder.typicode.com/todos/1")
        print(status_code, text)

asyncio.run(main())
```

### HTTP Methods

```python
JmNetwork.get(url)
JmNetwork.post(url, json={"test": "test123"})
JmNetwork.put(url, json={"test": "test123"})
JmNetwork.delete(url)
```

### Exceptions on Non-2xx

```python
from jm_networking import JmNetwork, HttpError

try:
    JmNetwork.get("https://jsonplaceholder.typicode.com/404")
except HttpError as exc:
    print(exc.status_code)
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
response = ObjectNetworking.put(todo, "https://jsonplaceholder.typicode.com/todos/1", params=None)

response = ObjectNetworking.delete(todo, "https://jsonplaceholder.typicode.com/todos/1", params=None)
```
