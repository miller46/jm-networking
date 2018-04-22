# jm-networking
Basic networking layer with async callbacks

Requires Python 3

## Installation

`pip install jm-networking`

Latest version is 1.0.9

## Example Usage

```python

  def success_callback(result):
      print("Execute success callback")

  def failure_callback(result):
      print("Execute failure callback")

  with Network() as network:
      network.on_success(success_callback)
      network.on_failure(failure_callback)
      network.get("https://example.com")
```
### 
```

    ...
    network.post("https://example.com", {body: data})
    
    ...
    network.put("https://example.com", {body: data})
    
    ...
    network.delete("https://example.com")
