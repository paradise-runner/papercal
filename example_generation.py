import os
from pathlib import Path
from datetime import datetime, timedelta
from concurrent.futures import ThreadPoolExecutor

from parse_ical import parse_calendar_events
from calendar_image import save_calendar_image
from weather import geocode_location


def generate_example_calendar(location: str = None):
    """
    Generate an example calendar file for testing with current week's dates
    """
    # Get coordinates for location if provided
    latitude, longitude = None, None
    if location:
        coords = geocode_location(location)
        if coords:
            latitude, longitude = coords
            print(
                f"Generating examples for location: {location} ({latitude:.4f}, {longitude:.4f})"
            )
        else:
            print(
                f"Could not find location '{location}', using default (Fort Collins, CO)"
            )
    else:
        print("Generating examples for default location: Fort Collins, CO")

    # Create synthetic example.ics with current week's dates
    create_synthetic_example_ics()

    events = parse_calendar_events("data/example.ics")

    # no need to commit example data we can generate
    os.remove("data/example.ics")
    save_calendar_image(
        events,
        "example-calendars/floyd-steinberg-calendar.png",
        dithering="floyd",
        latitude=latitude,
        longitude=longitude,
    )
    save_calendar_image(
        events,
        "example-calendars/atkinson-calendar.png",
        dithering="atkinson",
        latitude=latitude,
        longitude=longitude,
    )

    def generate_day_calendar(days):
        save_calendar_image(
            events,
            f"example-calendars/day-{days}-calendar.png",
            current_weekday=days,
            dithering="atkinson",
            latitude=latitude,
            longitude=longitude,
        )

    with ThreadPoolExecutor() as executor:
        executor.map(generate_day_calendar, range(6))


def create_synthetic_example_ics():
    """
    Create a synthetic example.ics file with current week's dates
    """
    # Get current date and calculate the start of the current week (Monday)
    today = datetime.now()
    days_since_monday = today.weekday()
    week_start = today - timedelta(days=days_since_monday)

    # Sample events for each day of the week
    sample_events = [
        [
            {
                "time": "08:00",
                "duration": 60,
                "summary": "Team Standup Meeting",
                "description": "Daily team synchronization and progress updates",
                "location": "Conference Room A",
            },
            {
                "time": "13:00",
                "duration": 90,
                "summary": "Client Presentation",
                "description": "Quarterly business review with key stakeholders",
                "location": "Board Room",
            },
            {
                "time": "16:00",
                "duration": 60,
                "summary": "Project Planning Session",
                "description": "Planning for upcoming product launch initiatives",
                "location": "Meeting Room B",
            },
        ],
        [
            {
                "time": "09:00",
                "duration": 90,
                "summary": "Budget Review Meeting",
                "description": "Monthly financial review and budget allocation",
                "location": "Finance Conference Room",
            },
            {
                "time": "11:00",
                "duration": 60,
                "summary": "Marketing Strategy Discussion",
                "description": "Q3 marketing campaign planning and strategy alignment",
                "location": "Marketing Office",
            },
            {
                "time": "14:00",
                "duration": 90,
                "summary": "Technical Architecture Review",
                "description": "System design review and technical documentation",
                "location": "Tech Lab",
            },
        ],
        [
            {
                "time": "08:00",
                "duration": 60,
                "summary": "Department All-Hands",
                "description": "Weekly department updates and announcements",
                "location": "Main Auditorium",
            },
            {
                "time": "11:30",
                "duration": 90,
                "summary": "Vendor Negotiation Call",
                "description": "Contract terms discussion with software vendor",
                "location": "Phone Conference",
            },
            {
                "time": "15:00",
                "duration": 90,
                "summary": "User Experience Workshop",
                "description": "Design thinking session for new user interface",
                "location": "Design Studio",
            },
        ],
        [
            {
                "time": "08:30",
                "duration": 90,
                "summary": "Quality Assurance Review",
                "description": "Testing protocols and quality standards assessment",
                "location": "QA Lab",
            },
            {
                "time": "12:00",
                "duration": 90,
                "summary": "Customer Feedback Session",
                "description": "Review of customer surveys and feedback analysis",
                "location": "Customer Success Office",
            },
            {
                "time": "14:30",
                "duration": 90,
                "summary": "Security Audit Meeting",
                "description": "IT security review and compliance discussion",
                "location": "IT Security Room",
            },
        ],
        [
            {
                "time": "09:00",
                "duration": 90,
                "summary": "Product Development Sync",
                "description": "Feature prioritization and development roadmap",
                "location": "Product Office",
            },
            {
                "time": "13:30",
                "duration": 90,
                "summary": "HR Policy Training",
                "description": "Updated workplace policies and procedures training",
                "location": "Training Room C",
            },
            {
                "time": "16:00",
                "duration": 60,
                "summary": "Weekly Retrospective",
                "description": "Team reflection on achievements and improvements",
                "location": "Collaboration Space",
            },
        ],
        [
            {
                "time": "08:00",
                "duration": 90,
                "summary": "Sales Pipeline Review",
                "description": "Weekly sales forecast and opportunity analysis",
                "location": "Sales War Room",
            },
            {
                "time": "11:00",
                "duration": 90,
                "summary": "Partnership Strategy Meeting",
                "description": "Strategic alliance discussions and partnership planning",
                "location": "Executive Conference Room",
            },
            {
                "time": "14:30",
                "duration": 90,
                "summary": "Innovation Brainstorm",
                "description": "Creative session for new product ideas and features",
                "location": "Innovation Lab",
            },
        ],
        [
            {
                "time": "09:30",
                "duration": 90,
                "summary": "Operational Excellence Review",
                "description": "Process improvement and operational efficiency analysis",
                "location": "Operations Center",
            },
            {
                "time": "13:00",
                "duration": 90,
                "summary": "Technology Roadmap Planning",
                "description": "Future technology stack and infrastructure planning",
                "location": "Tech Strategy Room",
            },
            {
                "time": "15:00",
                "duration": 90,
                "summary": "Week Wrap-up Meeting",
                "description": "Weekly achievements review and next week planning",
                "location": "Team Meeting Room",
            },
        ],
    ]

    # Create the iCal content
    ical_content = """BEGIN:VCALENDAR
VERSION:2.0
PRODID:-//Example Corp//Example Calendar//EN
CALSCALE:GREGORIAN
METHOD:PUBLISH

"""

    # Generate events for the current week
    for day_offset in range(7):
        current_date = week_start + timedelta(days=day_offset)
        date_str = current_date.strftime("%Y%m%d")

        for i, event in enumerate(sample_events[day_offset]):
            start_time = datetime.strptime(
                f"{date_str}T{event['time'].replace(':', '')}", "%Y%m%dT%H%M"
            )
            end_time = start_time + timedelta(minutes=event["duration"])

            ical_content += f"""BEGIN:VEVENT
UID:{date_str}-event{i + 1}@example.com
DTSTART:{start_time.strftime("%Y%m%dT%H%M%S")}
DTEND:{end_time.strftime("%Y%m%dT%H%M%S")}
SUMMARY:{event["summary"]}
DESCRIPTION:{event["description"]}
LOCATION:{event["location"]}
STATUS:CONFIRMED
END:VEVENT

"""

    ical_content += "END:VCALENDAR"

    # Ensure data directory exists
    Path("data").mkdir(parents=True, exist_ok=True)

    # Write the synthetic iCal file
    with open("data/example.ics", "w") as f:
        f.write(ical_content)
