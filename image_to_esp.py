import requests
from PIL import Image
from halo import Halo


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
        img = Image.open(image_path)
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

    spinner = Halo(text=f"Uploading image to EPD at {base_url} ({epd_width}x{epd_height})", spinner='dots')
    spinner.start()

    try:
        # 2. Send initial EPD configuration request
        initial_cmd = "EPDw_"
        initial_url = base_url + initial_cmd

        spinner.text = "Sending initial command..."
        try:
            response = requests.post(initial_url, data="", timeout=5)
            response.raise_for_status()
        except Exception as e:
            spinner.fail(f"Error sending initial command: {e}")
            return

        # 3. Send image data in chunks
        px_ind = 0
        c_value = 0  # For epdInd 27, u_data uses c=0
        total_pixels = len(image_pixels)

        while px_ind < total_pixels:
            rq_msg = ""
            # Process 8 pixels into one byte
            while px_ind < total_pixels and len(rq_msg) < 1000:
                v = 0
                for i in range(8):
                    if px_ind < total_pixels:
                        # If pixel value is NOT 'c_value', set the bit
                        if image_pixels[px_ind] != c_value:
                            v |= 128 >> i
                        px_ind += 1
                rq_msg += byte_to_str(v)

            # Construct the data upload URL
            data_upload_url = base_url + rq_msg + word_to_str(len(rq_msg)) + "LOAD_"

            progress = round(px_ind / total_pixels * 100, 1)
            spinner.text = f"Uploading image data... {progress}%"

            try:
                response = requests.post(data_upload_url, data="", timeout=10)
                response.raise_for_status()
            except Exception as e:
                spinner.fail(f"Error sending data chunk: {e}")
                return

        # 4. Send final SHOW command
        spinner.text = "Finalizing upload..."
        show_url = base_url + "SHOW_"
        try:
            response = requests.post(show_url, data="", timeout=8)
            response.raise_for_status()
            spinner.succeed("Image upload complete!")
        except Exception as e:
            spinner.fail(f"Error sending SHOW command: {e}")

    except KeyboardInterrupt:
        spinner.fail("Upload cancelled by user")
    except Exception as e:
        spinner.fail(f"Unexpected error: {e}")
