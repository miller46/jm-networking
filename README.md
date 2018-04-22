# jm-networking
Basic networking layer with async callbacks

Requires Python 3.6 or greater

## Example Usage

  def success(result):
      print("Exectute success callback")

  def failure(result):
      print("Execute failure callback")

  with Network() as network:
      network.on_success(success)
      network.on_failure(failure)
      network.get("https://example.com")
      
