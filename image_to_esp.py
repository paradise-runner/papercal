import requests
from PIL import Image
from halo import Halo


def prepare_image_data(image_path):
    """
    Loads an image and converts it to a raw 1-bit packed bytearray.
    800x480 pixels, 1 bit per pixel, MSB first. Total: 48000 bytes.
    Pixel mapping: white (>= 128) → 0 bit, black (< 128) → 1 bit.
    """
    img = Image.open(image_path).convert("L")  # grayscale
    pixels = img.getdata()
    packed = bytearray(len(pixels) // 8)
    for i in range(len(packed)):
        byte = 0
        for bit in range(8):
            px = pixels[i * 8 + bit]
            if px < 128:  # black pixel
                byte |= 0x80 >> bit
        packed[i] = byte
    return packed


def upload_epd_image(ip_address, image_path, epd_width=800, epd_height=480):
    """
    Uploads an image to the ESP32 e-Paper device.
    Converts the image to 1-bit packed format and POSTs to /image.
    """
    url = f"http://{ip_address}/image"

    spinner = Halo(
        text=f"Preparing image for EPD at {ip_address} ({epd_width}x{epd_height})",
        spinner="dots",
    )
    spinner.start()

    try:
        image_data = prepare_image_data(image_path)
        expected = epd_width * epd_height // 8
        if len(image_data) != expected:
            spinner.fail(f"Image data size mismatch: got {len(image_data)}, expected {expected}")
            return

        spinner.text = f"Uploading {len(image_data)} bytes to {url}..."
        response = requests.post(
            url,
            data=bytes(image_data),
            headers={"Content-Type": "application/octet-stream"},
            timeout=30,
        )
        response.raise_for_status()
        spinner.succeed("Image uploaded successfully!")

    except requests.exceptions.RequestException as e:
        spinner.fail(f"Upload failed: {e}")
    except FileNotFoundError:
        spinner.fail(f"Image file not found: {image_path}")
    except Exception as e:
        spinner.fail(f"Error: {e}")
