# Picow
Multi-threaded web server, running on a picoW micro-controller, able to stream music from an SDcard.

## External dependencies
- pico zero library
- sdcard

## Initial setup
Create a config.json file containing the credentials to connect to your wifi & 
upload the file along with the python code, libraries, favicon & index.html on your micro-controller.
```
{
  "ssid": "BELL69",
  "password": "my_password"
}
```

## Material used
- [RPI Pico W](https://www.amazon.ca/-/fr/dp/B0B5H17CMK?psc=1&ref=ppx_yo2ov_dt_b_product_details)
- [Adafruit ADA254 Card reader MicroSD](https://www.amazon.ca/-/fr/dp/B00NAY2NAI?psc=1&ref=ppx_yo2ov_dt_b_product_details)

## Schematic
<p align="center">
  <img src="" alt="schema" />
</p>
