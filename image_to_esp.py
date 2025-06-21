import requests
from PIL import Image


def byte_to_str(v):
    """Converts a byte to a two-character string using base-16 ('a'-'p')."""
    return chr((v & 0xF) + 97) + chr(((v >> 4) & 0xF) + 97)


def word_to_str(v):
    """Converts a 16-bit word to a four-character string."""
    return byte_to_str(v & 0xFF) + byte_to_str((v >> 8) & 0xFF)


def prepare_image_data(image_path, target_width, target_height):
    """
    Loads an image, converts it to 1-bit monochrome (0 or 1),
    and flattens it into a 1D array suitable for the EPD.
    Assumes pixels are either 0 (white/default) or 1 (black/inverted).
    """
    try:
        img = Image.open(image_path).convert("1")  # Convert to 1-bit image
        img = img.resize((target_width, target_height), Image.Resampling.LANCZOS)
        # Get pixel data; 0 for white, 255 for black in '1' mode
        # We need 0 to be the "transparent" or "off" color (value of c),
        # so let's map 255 (black) to 1 and 0 (white) to 0.
        pixel_data = []
        for pixel in img.getdata():
            pixel_data.append(1 if pixel == 255 else 0)
        return pixel_data
    except FileNotFoundError:
        print(f"Error: Image file not found at {image_path}")
        return None
    except Exception as e:
        print(f"Error processing image: {e}")
        return None


def upload_epd_image(ip_address, image_path, epd_width, epd_height):
    """
    Uploads an image to the EPD device for epdInd 27.
    """
    base_url = f"http://{ip_address}/"

    # 1. Prepare image data
    image_pixels = prepare_image_data(image_path, epd_width, epd_height)
    if not image_pixels:
        return

    print(
        f"Attempting to upload image to EPD at {base_url} with dimensions {epd_width}x{epd_height}"
    )

    # 2. Send initial EPD configuration request
    initial_cmd = "EPDw_"
    initial_url = base_url + initial_cmd

    print(f"Sending initial command: {initial_url}")
    try:
        response = requests.post(initial_url, data="", timeout=5)
        response.raise_for_status()  # Raise an exception for HTTP errors
        print(
            f"Initial command '{initial_cmd}' sent successfully. Status: {response.status_code}"
        )
    except Exception as e:
        print(f"Error sending initial command: {e}")
        return

    # 3. Send image data in chunks
    px_ind = 0
    c_value = 0  # For epdInd 27, u_data uses c=0

    while px_ind < len(image_pixels):
        rq_msg = ""
        # Process 8 pixels into one byte
        while px_ind < len(image_pixels) and len(rq_msg) < 1000:
            v = 0
            for i in range(8):
                if px_ind < len(image_pixels):
                    # If pixel value is NOT 'c_value', set the bit
                    if image_pixels[px_ind] != c_value:
                        v |= 128 >> i
                    px_ind += 1
            rq_msg += byte_to_str(v)

        # Construct the data upload URL
        # The JS function u_show uses rqMsg + wordToStr(rqMsg.length) + 'LOAD_'
        # The `wordToStr(rqMsg.length)` encodes the length of the *encoded* data string.
        data_upload_url = base_url + rq_msg + word_to_str(len(rq_msg)) + "LOAD_"

        print(
            f"Sending data chunk (length: {len(rq_msg)}): {data_upload_url[:100]}..."
        )  # Print only part of URL

        try:
            response = requests.post(data_upload_url, data="", timeout=10)
            response.raise_for_status()
            print(
                f"Data chunk sent. Progress: {round(px_ind / len(image_pixels) * 100, 2)}%"
            )
        except Exception as e:
            print(f"Error sending data chunk: {e}")
            return

    # 4. Send final SHOW command
    show_url = base_url + "SHOW_"
    print(f"Sending final command: {show_url}")
    try:
        response = requests.post(show_url, data="", timeout=8)
        response.raise_for_status()
        print(f"Image upload complete! Status: {response.status_code}")
    except Exception as e:
        print(f"Error sending SHOW command: {e}")
