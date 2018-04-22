# jm-networking
Basic networking layer with async callbacks

Requires Python 3

## Example Usage

```python

  def success(result):
      print("Exectute success callback")

  def failure(result):
      print("Execute failure callback")

  with Network() as network:
      network.on_success(success)
      network.on_failure(failure)
      network.get("https://example.com")
      
```
`pip install jm-networking`

Latest version is 1.0.7
