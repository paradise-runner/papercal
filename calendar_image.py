from PIL import Image, ImageDraw, ImageFont
from datetime import datetime
from typing import List, Dict
import hashlib
import os


def create_weekly_calendar_image(
    events: List[Dict], dithering="atkinson", current_weekday=None
) -> Image.Image:
    # Load random photo and convert to black and white/cropped
    photo_img = get_weekly_image()
    current_date = datetime.now()
    if current_weekday is None:
        # Use current weekday if not provided
        current_weekday = current_date.weekday()
    is_weekday = current_weekday < 5

    if not is_weekday:
        # Weekend: return black and white photo, cropped to 800x480
        bw_photo = convert_to_black_and_white(
            crop_photo(photo_img, is_weekday=False).resize((800, 480)), method=dithering
        )
        return bw_photo

    # This seems iffy, may adjust implementation to include timezones?
    # If its past 6pm on a Friday, return black and white photo, cropped to 800x480
    if current_weekday == 4 and current_date.hour >= 18:
        bw_photo = convert_to_black_and_white(
            crop_photo(photo_img, is_weekday=False).resize((800, 480)), method=dithering
        )
        return bw_photo

    # Weekday: proceed with calendar image
    img = Image.new("L", (800, 480), 255)  # 'L' mode for grayscale
    draw = ImageDraw.Draw(img)

    # Define dimensions
    margin = 50
    day_width = (800 - margin) / 5  # 5 days
    hour_height = (480 - margin) / 10  # Show 8am - 6pm (10 hours)

    # Load fonts
    try:
        font = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", 12)
        header_font = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", 14)
    except Exception as e:
        print(f"Error loading fonts: {e}, using default font.")
        font = ImageFont.load_default()
        header_font = ImageFont.load_default()

    # Draw grid with solid black lines
    for i in range(6):  # Vertical lines
        x = margin + (i * day_width)
        draw.line([(x, margin), (x, 480)], fill=0, width=2)

    for i in range(11):  # Horizontal lines
        y = margin + (i * hour_height)
        draw.line([(margin, y), (800, y)], fill=0, width=2)

    # Add day labels with larger font and gray out past days
    days = ["MON", "TUE", "WED", "THU", "FRI"]
    for i, day in enumerate(days):
        x = margin + (i * day_width) + (day_width / 2)
        text_color = 128 if i < current_weekday else 0  # Gray text for past days
        draw.text((x - 15, margin - 25), day, fill=text_color, font=header_font)

    # Add hour labels
    for i in range(11):
        hour = i + 8  # Start at 8am
        period = "AM" if hour < 12 else "PM"
        display_hour = hour if hour <= 12 else hour - 12
        y = margin + (i * hour_height)
        draw.text((5, y - 8), f"{display_hour}{period}", fill=0, font=font)

    # Helper function for word wrapping
    def wrap_text(text: str, font: ImageFont, max_width: int) -> List[str]:
        words = text.split()
        lines = []
        current_line = []

        for word in words:
            current_line.append(word)
            line_width = font.getlength(" ".join(current_line))
            if line_width > max_width:
                if len(current_line) == 1:
                    lines.append(current_line[0])
                    current_line = []
                else:
                    current_line.pop()
                    lines.append(" ".join(current_line))
                    current_line = [word]

        if current_line:
            lines.append(" ".join(current_line))
        return lines

    # Draw events with high contrast
    # First, group events by day and find overlaps
    day_events = {i: [] for i in range(5)}  # Monday to Friday
    for event in events:
        if event["start"].weekday() > 4:  # Skip weekend events
            continue
        day_events[event["start"].weekday()].append(event)

    # Sort events by start time for each day
    for day in day_events.values():
        day.sort(key=lambda x: x["start"])

    # Draw events with offsets for overlaps
    for day_idx, day_event_list in day_events.items():
        is_past_day = day_idx < current_weekday
        active_times = []

        for event in day_event_list:
            start_hour = event["start"].hour + event["start"].minute / 60
            end_hour = event["end"].hour + event["end"].minute / 60

            # Clip to visible hours (8am - 6pm)
            start_hour = max(8, min(18, start_hour))
            end_hour = max(8, min(18, end_hour))

            # Remove finished time ranges
            active_times = [(s, e) for s, e in active_times if e > start_hour]

            # Calculate offset based on overlapping time ranges
            offset = 0
            for s, e in active_times:
                if start_hour < e and end_hour > s:
                    offset += 1

            # Add this event's time range
            active_times.append((start_hour, end_hour))

            # Calculate position with offset
            x1 = margin + (day_idx * day_width)
            y1 = margin + (start_hour - 8) * hour_height
            x2 = x1 + day_width - (offset * 10)  # Reduce width for offset events
            y2 = margin + (end_hour - 8) * hour_height

            # Add horizontal offset
            x1 += offset * 10

            # Adjust colors based on whether the day is in the past
            border_color = 128 if is_past_day else 0  # Darker gray for past events
            fill_color = (
                240 if is_past_day else 255
            )  # Slightly gray fill for past events
            text_color = 128 if is_past_day else 0  # Gray text for past events

            # Draw event rectangle with adjusted colors
            draw.rectangle(
                [(x1 + 1, y1), (x2 - 1, y2)],
                fill=fill_color,
                outline=border_color,
                width=2,
            )

            # Add event text with adjusted color
            time_str = f"{event['start'].strftime('%I:%M%p')} "
            text = time_str + event["summary"]

            # Calculate event duration in hours
            duration = end_hour - start_hour

            if duration >= 1.0:  # For events 1 hour or longer
                available_width = (day_width - 10) - (offset * 10)
                lines = wrap_text(text, font, available_width)

                line_height = font.size + 2
                text_y = y1 + 2

                for line in lines[:3]:
                    draw.text((x1 + 5, text_y), line, fill=text_color, font=font)
                    text_y += line_height
            else:
                text = text[: 20 - (offset * 2)]
                draw.text((x1 + 5, y1 + 2), text, fill=text_color, font=font)

    # Overlay black and white cropped photo over prior days (including events)
    bw_photo = convert_to_black_and_white(
        crop_photo(photo_img, is_weekday=True).resize((740, 430)), method=dithering
    )
    if current_weekday > 0:
        # Calculate region for all past days as a single block
        x1 = int(margin)
        y1 = int(margin)
        # Add 2 pixels to x2 to cover the grid line between days
        x2 = int(margin + (current_weekday * day_width) + 8)
        y2 = int(480)
        # Corresponding region in the photo
        photo_x1 = 0
        # Add 2 pixels to photo_x2 to match the overlay width
        photo_x2 = int((current_weekday / 5) * bw_photo.width + 8)
        day_crop = bw_photo.crop(
            (photo_x1, 0, min(photo_x2, bw_photo.width), bw_photo.height)
        )
        # Paste onto calendar image as one block
        img.paste(day_crop, (x1, y1))

    return img


def load_random_photo(photo_dir: str = "./photos") -> tuple[Image.Image, str]:
    """
    Load a random photo from the specified directory
    """
    import os
    import random

    photos = [
        f
        for f in os.listdir(photo_dir)
        if f.lower().endswith((".png", ".jpg", ".jpeg"))
    ]
    if not photos:
        raise ValueError("No photos found in the specified directory.")

    selected_photo = random.choice(photos)
    photo_path = os.path.join(photo_dir, selected_photo)

    img = Image.open(photo_path)
    return img, selected_photo


def crop_photo(img: Image.Image, is_weekday: bool) -> Image.Image:
    """
    Resize the photo to the appropriate size based on whether it's a weekday or weekend.
    No cropping, just resize to fit the target dimensions.
    """
    target_width = 740 if is_weekday else 800
    target_height = 430 if is_weekday else 480
    return img.resize((target_width, target_height), Image.LANCZOS)


def atkinson_dither(img: Image.Image) -> Image.Image:
    """
    Convert the image to black and white using Atkinson dithering.
    """
    img = img.convert("L")
    pixels = img.load()
    w, h = img.size
    for y in range(h):
        for x in range(w):
            old_pixel = pixels[x, y]
            new_pixel = 0 if old_pixel < 128 else 255
            pixels[x, y] = new_pixel
            quant_error = (old_pixel - new_pixel) // 8
            for dx, dy in [(1, 0), (2, 0), (-1, 1), (0, 1), (1, 1), (0, 2)]:
                nx, ny = x + dx, y + dy
                if 0 <= nx < w and 0 <= ny < h:
                    pixels[nx, ny] = max(0, min(255, pixels[nx, ny] + quant_error))
    return img.convert("1")


def convert_to_black_and_white(
    img: Image.Image, method: str = "atkinson"
) -> Image.Image:
    """
    Convert the image to black and white using the specified dithering method.
    method: 'floyd' (default) or 'atkinson'
    """
    if method == "atkinson":
        return atkinson_dither(img)
    # Default: Floyd Steinberg
    return img.convert("1", dither=Image.Dither.FLOYDSTEINBERG)


def save_calendar_image(
    events: List[Dict],
    output_path: str = "calendar.png",
    dithering: str = "atkinson",
    current_weekday: int = None,
) -> None:
    """
    Create and save the calendar image
    """
    img = create_weekly_calendar_image(
        events, dithering=dithering, current_weekday=current_weekday
    )
    img.save(output_path)


def get_weekly_image(photos_folder="./photos", week_number: int = None) -> Image.Image:
    """
    Returns a deterministic image filename based on the current week.
    Ensures no image repeats until all images have been used.
    Optionally, pass in a week_number to select the image for that week.
    """
    # Get all image files from the photos folder
    try:
        all_files = os.listdir(photos_folder)
        image_extensions = {".jpg", ".jpeg", ".png", ".gif", ".bmp", ".webp", ".tiff"}
        images = [
            f for f in all_files if os.path.splitext(f.lower())[1] in image_extensions
        ]

        if not images:
            raise ValueError("No image files found in the photos folder")

        # Sort for consistency across runs
        images.sort()

    except FileNotFoundError:
        raise FileNotFoundError(f"Photos folder '{photos_folder}' not found")

    # Calculate the current week number since Unix epoch
    # Using Monday as the start of the week for consistency
    epoch_start = datetime(1970, 1, 5)  # First Monday after Unix epoch
    if week_number is None:
        now = datetime.now()
        days_since_epoch = (now - epoch_start).days
        week_number = days_since_epoch // 7

    # Create a deterministic seed based on week number
    seed_string = f"week_{week_number}"
    hash_object = hashlib.md5(seed_string.encode())
    hash_hex = hash_object.hexdigest()

    # Convert hash to integer for indexing
    int(hash_hex, 16)

    # Calculate cycle position to ensure no repeats within a full cycle
    num_images = len(images)
    cycle_number = week_number // num_images
    week_in_cycle = week_number % num_images

    # Use hash to create pseudo-random order within each cycle
    cycle_seed = f"cycle_{cycle_number}"
    cycle_hash = hashlib.md5(cycle_seed.encode()).hexdigest()
    int(cycle_hash, 16)

    # Generate a pseudo-random permutation for this cycle
    indices = list(range(num_images))

    # Simple Fisher-Yates shuffle using our deterministic seed
    for i in range(num_images - 1, 0, -1):
        # Generate pseudo-random number for this position
        pos_seed = f"{cycle_seed}_{i}"
        pos_hash = hashlib.md5(pos_seed.encode()).hexdigest()
        j = int(pos_hash, 16) % (i + 1)
        indices[i], indices[j] = indices[j], indices[i]

    # Select the image for this week
    selected_index = indices[week_in_cycle]

    return Image.open(os.path.join(photos_folder, images[selected_index]))
