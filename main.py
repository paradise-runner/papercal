import os
import requests
import argparse
from pathlib import Path
from datetime import datetime

from parse_ical import parse_calendar_events
from calendar_image import save_calendar_image
from image_to_esp import upload_epd_image
from dotenv import load_dotenv
from example_generation import generate_example_calendar
from weather import geocode_location


def fetch_ical_file(url: str, save_path: str) -> bool:
    """
    Fetch iCal file from URL and save it locally
    Returns True if successful, False otherwise
    """
    try:
        response = requests.get(url)
        response.raise_for_status()

        Path(save_path).parent.mkdir(parents=True, exist_ok=True)
        with open(save_path, "wb") as f:
            f.write(response.content)
        return True
    except Exception as e:
        print(f"Error fetching iCal file: {e}")
        return False


def main(location: str = None, force_update: bool = False):
    # Load environment variables from .env file
    load_dotenv("production.env")
    I_CAL_ADDRESS = os.getenv("I_CAL_ADDRESS")
    if not I_CAL_ADDRESS:
        raise ValueError(
            "I_CAL_ADDRESS environment variable is not set. Please set it in the .env file."
        )

    # Get coordinates for location if provided
    latitude, longitude = None, None
    if location:
        coords = geocode_location(location)
        if coords:
            latitude, longitude = coords
            print(f"Using location: {location} ({latitude:.4f}, {longitude:.4f})")
        else:
            print(
                f"Could not find location '{location}', using default (Fort Collins, CO)"
            )
    else:
        print("Using default location: Fort Collins, CO")

    if not os.path.exists("data/calendar.ics"):
        print("No existing calendar file found, fetching from iCal address...")
        success = fetch_ical_file(I_CAL_ADDRESS, "data/calendar.ics")
        if not success:
            print("Failed to fetch iCal file, exiting.")
            return
        events = parse_calendar_events("data/calendar.ics")
    else:
        print("Existing calendar file found, checking for updates...")
        fetch_ical_file(I_CAL_ADDRESS, "data/tmp_calendar.ics")
        old_events = parse_calendar_events("data/calendar.ics")
        new_events = parse_calendar_events("data/tmp_calendar.ics")
        # replace old calendar with new calendar
        os.remove("data/calendar.ics")
        os.rename("data/tmp_calendar.ics", "data/calendar.ics")
        if old_events != new_events:
            print("Calendar has changed, updating image...")
            events = new_events
        elif force_update:
            print("Force update requested, updating image...")
            events = new_events
        else:
            current_date = datetime.now()
            if current_date.hour <= 7:
                # If it's before or currently 7am, update the image to reflect that a day needs to be overwritten
                events = new_events
            else:
                print("No changes in calendar, skipping image update.")
                return
    save_calendar_image(
        events,
        "data/calendar.png",
        dithering="atkinson",
        latitude=latitude,
        longitude=longitude,
    )
    print(f"Created calendar image with {len(events)} events")
    upload_epd_image("192.168.1.159", "data/calendar.png", 800, 480)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Generate calendar images for e-paper display"
    )
    parser.add_argument(
        "--examples",
        action="store_true",
        help="Generate example calendar images instead of running main function",
    )
    parser.add_argument(
        "--location",
        type=str,
        help="Location for weather data (e.g., 'Fort Collins, CO, United States'). Defaults to Fort Collins, CO.",
    )
    parser.add_argument(
        "--update",
        action="store_true",
        help="Force update the calendar image even if no changes are detected",
    )

    args = parser.parse_args()

    if args.examples:
        generate_example_calendar(location=args.location)
    else:
        main(location=args.location, force_update=args.update)
