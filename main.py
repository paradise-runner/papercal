import os
import requests
import random
import time
from pathlib import Path

from parse_ical import parse_calendar_events
from calendar_image import save_calendar_image
from image_to_esp import upload_epd_image
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv("production.env")
I_CAL_ADDRESS = os.getenv("I_CAL_ADDRESS")
if not I_CAL_ADDRESS:
    raise ValueError(
        "I_CAL_ADDRESS environment variable is not set. Please set it in the .env file."
    )


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


def main():
    if not os.path.exists("data/calendar.ics"):
        print("No existing calendar file found, fetching from iCal address...")
        success = fetch_ical_file(I_CAL_ADDRESS, "data/calendar.ics")
        if not success:
            print("Failed to fetch iCal file, exiting.")
            return
        events = parse_calendar_events("data/calendar.ics")
    else:
        fetch_ical_file(I_CAL_ADDRESS, "data/tmp_calendar.ics")
        print("Existing calendar file found, checking for updates...")
        old_events = parse_calendar_events("data/calendar.ics")
        new_events = parse_calendar_events("data/tmp_calendar.ics")
        os.remove("data/tmp_calendar.ics")
        if old_events != new_events:
            events = new_events
        else:
            print("No changes in calendar, skipping image update.")
            return
    save_calendar_image(events, "data/calendar.png")
    print(f"Created calendar image with {len(events)} events")
    upload_epd_image("192.168.1.159", "data/calendar.png", 800, 480)


def generate_example_calendar():
    """
    Generate an example calendar file for testing
    """
    events = parse_calendar_events("data/example.ics")
    save_calendar_image(
        events, "example-calendars/floyd-steinberg-calendar.png", dithering="floyd"
    )
    save_calendar_image(
        events, "example-calendars/atkinson-calendar.png", dithering="atkinson"
    )
    for days in range(6):
        save_calendar_image(
            events,
            f"example-calendars/day-{days}-calendar.png",
            current_weekday=days,
            dithering="atkinson",
        )


if __name__ == "__main__":
    main()
