# jm-networking
Basic networking layer with async callbacks

Requires Python 3

## Installation

`pip install jm-networking`

Latest version is 1.0.12

## Example Usage

```python
  from jm_networking import Network

  def success_callback(result):
      print("Execute success callback")

  def failure_callback(result):
      print("Execute failure callback")

  with Network() as network:
      network.on_success(success_callback)
      network.on_failure(failure_callback)
      network.get("https://example.com")
```

### Other HTTP methods
```python

    ...
    network.post("https://example.com", {body: data})
    
    ...
    network.put("https://example.com", {body: data})
    
    ...
    network.delete("https://example.com")
```

### Return response from callback (e.g. to return response to screen or render template in Flask)
```python
  def success_callback(result):
      return "Response"

  with Network() as network:
      network.on_success(success_callback)
      return network.get("https://example.com")
```

### 

```
"Response"
```
