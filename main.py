import os
import ujson
import machine
import network
import sdcard
import uasyncio as asyncio
from time import sleep
from picozero import pico_temp_sensor, pico_led


port = 80
chunk_size = 4096
ssid = ""
password = ""
lightState = "OFF"
has_sdcard = False
volume_path = "/sd"
music_folder_path = "/music"


def read_config(file_path):
    with open(file_path, 'r') as file:
        config = ujson.load(file)
    return config


def is_volume_mounted(volume_path):
    try:
        os.listdir(volume_path)
        return True
    except OSError:
        return False


def url_decode(s):
    decoded_chars = []
    i = 0
    while i < len(s):
        if s[i] == '%' and i + 2 < len(s):
            decoded_chars.append(chr(int(s[i + 1:i + 3], 16)))
            i += 3
        else:
            decoded_chars.append(s[i])
            i += 1
    return ''.join(decoded_chars)


def file_exists(filename):
    try:
        os.stat(filename)
        return True
    except OSError:
        return False


def is_audio_file(request_path):
    return any(request_path.endswith(ext) for ext in ['.wav', '.mp3', '.ogg'])


def is_image_file(request_path):
    return any(request_path.endswith(ext) for ext in ['ico', '.jpg', '.jpeg', '.png'])


def get_file_extension(file_path):
    _, extension = file_path.rsplit('.', 1)
    return extension if extension else ''


def get_mimetype(request_path):
    if is_audio_file(request_path):
        extension = get_file_extension(request_path)
        return f"audio/{extension}"
    elif is_image_file(request_path):
        extension = get_file_extension(request_path)
        return f"image/{extension}"
    elif request_path.endswith('.css'):
        return 'text/css'
    elif request_path.endswith('.js'):
        return 'application/javascript'
    elif request_path.endswith('.html') :
        return 'text/html'
    else:
        return "application/octet-stream"


def mount_sd_card():
    global volume_path, music_folder_path
    sck = machine.Pin(10, machine.Pin.OUT)
    mosi = machine.Pin(11, machine.Pin.OUT)
    miso = machine.Pin(12, machine.Pin.OUT)
    cs = machine.Pin(13)
    spi = machine.SPI(1, sck=sck, mosi=mosi, miso=miso)  
    sd = sdcard.SDCard(spi, cs)  
    os.mount(sd, volume_path)
    print(f"SD card successfully mounted on \"{volume_path}\".")


def unmount_sd_card():
    global volume_path
    os.umount(volume_path)
    print("SD card unmounted.")


def connect():
    attempt_count = 0
    max_attempts = 30
    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)
    wlan.connect(ssid, password)
    while not wlan.isconnected() and attempt_count < max_attempts:
        pico_led.toggle()
        print('Waiting for connection...')
        sleep(1)
        attempt_count += 1
    
    if wlan.isconnected():
        pico_led.on()
        ip = wlan.ifconfig()[0]
        print(f'Connected on {ip}')
        return ip
    else:
        raise Exception(f'Failed to connect after {max_attempts} attempts.')


def handle_redirects(request_path):
    global volume_path, music_folder_path
    if request_path == '/':
        request_path = "/index.html"
    if is_audio_file(request_path) or is_image_file(request_path):
        if not file_exists(request_path) and is_volume_mounted(volume_path):
            request_path = volume_path + music_folder_path + request_path
    return request_path


async def send_header(writer, request_path):
    mimetype = get_mimetype(request_path)
    header = ("HTTP/1.1 200 OK\r\n"
        f"Content-Type: {mimetype}\r\n"
        "Connection: close\r\n"
        "Transfer-Encoding: chunked\r\n"
        "\r\n")
    await writer.awrite(header)


async def send_json(writer, json):
    await writer.awrite(ujson.dumps(json).encode('utf-8'))
    await writer.drain()
    await writer.aclose()


async def send_chunk(writer, chunk):
    try:
        chunk_size_hex = f"{len(chunk):x}\r\n".encode('utf-8') 
        chunk_data = chunk_size_hex + chunk + b'\r\n'
        await writer.awrite(chunk_data)
    except Exception as e:
        raise


async def serve_client(reader, writer):
    global lightState, volume_path

    try:
        request = await reader.read(chunk_size)
        request = request.decode('utf-8')
 
        try:
            method = request.split()[0]
            request_path = url_decode(request.split()[1])
            print(method + " " + request_path)
        except IndexError:
            pass
        
        if method == "GET":
            request_path = handle_redirects(request_path)
            
            if request_path == '/audio':
                if is_volume_mounted(volume_path):
                    await send_json(writer, os.listdir(volume_path + music_folder_path))
                else:
                    await send_json(writer, [])
            elif request_path == '/light':
                await send_json(writer, {"state": lightState})  
            elif request_path == '/temperature':
                await send_json(writer, {"temperature": "{:.2f} *C".format(pico_temp_sensor.temp)})
            else:
                await serve_static_file(writer, request_path)
        if method == "POST":
            body_start = request.find('\r\n\r\n') + 4
            body = ujson.loads(request[body_start:])
            print(body)
                    
            if request_path == '/light':
                if (body["state"] == "ON"):
                    pico_led.on()
                    lightState = "ON"
                    await send_json(writer, {"state": lightState})
                else:
                    pico_led.off()
                    lightState = "OFF"
                    await send_json(writer, {"state": lightState})
    except Exception as e:
        print(f"Error: {e}")


async def serve_static_file(writer, request_path):
    try:
        position = 0
        with open(request_path, 'rb') as fd:
            fd.seek(position)
            await send_header(writer, request_path)
            while True:
                chunk = fd.read(chunk_size)
                if not chunk:
                    break
                await send_chunk(writer, chunk)
                position = fd.tell()
            
            await writer.awrite(b'0\r\n\r\n')
    except OSError as e:
        if e.errno == errno.ENOENT:
            print(f"Error: '{request_path}' file not found.")
        elif e.errno == errno.ECONNRESET:
            print("Connection reset. Resuming...")
        else:
            print(f"An unexpected OS error occurred: {e}")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
    finally:
        await writer.drain()
        await writer.aclose()


async def main():
    global card_detect, has_sdcard
    if has_sdcard:
        mount_sd_card()
    else:
        print("Warning no sd card. There won't be music.")
    ip = connect()
    pico_led.off()
    
    await asyncio.start_server(serve_client, ip, port)
    
    serving = True
    while serving:
        try:
            if not has_sdcard == card_detect.value():
                await asyncio.sleep(0.5)
                has_sdcard = card_detect.value()
                if has_sdcard:
                    mount_sd_card()
                else:
                    unmount_sd_card()
            await asyncio.sleep(0.1)
        except KeyboardInterrupt:
            serving = False


try:
    card_detect = machine.Pin(16, machine.Pin.IN, machine.Pin.PULL_UP)
    has_sdcard = card_detect.value()
    config = read_config("config.json")
    ssid = config.get('ssid', '')
    password = config.get('password', '')
    loop = asyncio.get_event_loop()
    loop.run_until_complete(main())
except KeyboardInterrupt:
    machine.reset()
