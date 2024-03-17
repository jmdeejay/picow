# Picow
Multi-threaded web server, running on a picoW micro-controller, able to stream music from an SDcard.

## Screenshot
<p align="center">
  <img src="https://github.com/jmdeejay/picow/assets/9083510/e4716f7e-5ea2-4595-993e-ee37c35f6361" alt="Webpage" />
</p>

## Material used
- [RPI Pico W](https://www.amazon.ca/-/fr/dp/B0B5H17CMK?psc=1&ref=ppx_yo2ov_dt_b_product_details)
- [Adafruit ADA254 Card reader MicroSD](https://www.amazon.ca/-/fr/dp/B00NAY2NAI?psc=1&ref=ppx_yo2ov_dt_b_product_details)

## External dependencies
- pico zero library
- sdcard

## Schematic
<p align="center">
  <img src="https://github.com/jmdeejay/picow/assets/9083510/0aff0286-6832-4b86-97f2-cfe9bce73386" alt="schema" />
</p>

## Initial setup
Create a config.json file containing the credentials to connect to your wifi & 
upload the file along with the python code, libraries, favicon & index.html on your micro-controller.
```
{
  "ssid": "BELL69",
  "password": "my_password"
}
```
### Setup the SDcard
Format your SDcard in FAT32. Put all the music you want to be able to stream inside a `music` folder at the root.
