# pyTradfriWS
This is a wrapper around [pytradfri](https://github.com/ggravlingen/pytradfri) that publishes it as a WebSockets API. It observes all devices and groups on the IKEA Trådfri Gateway, remembers them in an internal list, sends it to a client that connects and as a device changes status, it updates the client in realtime.
## Requirements
* IKEA Trådfri Gateway
* Python 3.4+
* [pytradfri](https://github.com/ggravlingen/pytradfri) (Python API that wraps up gateway objects and  IO using...)
* [aiocoap](https://github.com/chrysn/aiocoap) (native Python COAP library with support for DTLS using...)
* [tinydtls-cython](https://git.fslab.de/jkonra2m/tinydtls-cython) (Python wrapper for tinydtls in Cython)
* [websockets](https://github.com/aaugustin/websockets) (WebSocket implementation in Python 3)
## Features
* Querying a list of the following items configured in the gateway:
  * Devices
    * Lamps
    * Remote Controls
    * Motion Sensors
  * Groups
* Querying the status of the items 
  * On/Off
  * Brightness
  * Battery level
  * Names
## Not yet supported
* Querying moods / scenes
* Executing tasks (turning lights on/off, dimming)
## Other TODOs:
* Improving code
* Offering configuration
* Handling connection losses (i.e. currently a restart of the script is required if a connection loss to the gateway occurs)

Note: This is my first Python project. So bear with me please for the crude code or help me improve it 😉.