from datetime import datetime, timedelta
from icalendar import Calendar
from dateutil.rrule import rrulestr
from typing import List, Dict
import pytz


def get_week_range() -> tuple[datetime, datetime]:
    """
    Get the start and end datetime for the current week
    Returns (week_start, week_end) tuple with timezone awareness
    """
    local_tz = pytz.timezone("America/Denver")  # or your local timezone
    today = datetime.now(local_tz)
    week_start = today - timedelta(days=today.weekday())
    week_start = week_start.replace(hour=0, minute=0, second=0, microsecond=0)
    week_end = week_start + timedelta(days=7)
    return week_start, week_end


def parse_calendar_events(ical_path: str) -> List[Dict]:
    """
    Parse iCal file and return list of events for current week
    """
    week_start, week_end = get_week_range()
    events = []
    local_tz = pytz.timezone("America/Denver")

    try:
        with open(ical_path, "rb") as f:
            cal = Calendar.from_ical(f.read())

            # First, collect all recurrence exceptions
            exceptions = {}
            for component in cal.walk("VEVENT"):
                recurrence_id = component.get("recurrence-id")
                if recurrence_id:
                    # Get original date and UID to identify the exception
                    uid = component.get("uid")
                    original_date = recurrence_id.dt
                    if not isinstance(original_date, datetime):
                        original_date = datetime.combine(
                            original_date, datetime.min.time()
                        )
                    if original_date.tzinfo is None:
                        original_date = local_tz.localize(original_date)
                    else:
                        original_date = original_date.astimezone(local_tz)

                    key = (uid, original_date.date())
                    exceptions[key] = component

            # Now process all events
            for component in cal.walk("VEVENT"):
                # Skip processing recurrence exceptions here - they'll be handled during recurrence expansion
                if component.get("recurrence-id"):
                    continue

                start = component.get("dtstart").dt
                end = component.get("dtend").dt

                # Handle timezone and date vs datetime
                if isinstance(start, datetime):
                    if start.tzinfo is None:
                        start = local_tz.localize(start)
                    else:
                        start = start.astimezone(local_tz)
                else:
                    start = local_tz.localize(
                        datetime.combine(start, datetime.min.time())
                    )

                if isinstance(end, datetime):
                    if end.tzinfo is None:
                        end = local_tz.localize(end)
                    else:
                        end = end.astimezone(local_tz)
                else:
                    end = local_tz.localize(datetime.combine(end, datetime.max.time()))

                # Handle recurring events
                if component.get("rrule"):
                    # Get the recurrence rule
                    rrule = component.get("rrule")

                    # Process rule values - convert lists to comma-separated strings
                    rrule_processed = {}
                    for k, v in rrule.items():
                        if isinstance(v, list):
                            # Convert any datetime objects in lists to strings
                            processed_items = []
                            for item in v:
                                if isinstance(item, datetime):
                                    processed_items.append(
                                        item.strftime("%Y%m%dT%H%M%SZ")
                                    )
                                else:
                                    processed_items.append(str(item))
                            rrule_processed[k] = ",".join(processed_items)
                        else:
                            # Handle single datetime values
                            if isinstance(v, datetime):
                                rrule_processed[k] = v.strftime("%Y%m%dT%H%M%SZ")
                            else:
                                rrule_processed[k] = str(v)

                    # Convert to dateutil rrule string format
                    rrule_str = "RRULE:" + ";".join(
                        f"{k}={v}" for k, v in rrule_processed.items()
                    )

                    # Get recurrences between week_start and week_end
                    rule = rrulestr(rrule_str, dtstart=start)
                    occurrences = rule.between(week_start, week_end, inc=True)

                    # Handle each occurrence
                    for occurrence_start in occurrences:
                        # Calculate occurrence end time
                        duration = end - start
                        occurrence_end = occurrence_start + duration

                        # Check if this instance has been moved (has an exception)
                        uid = component.get("uid")
                        exception_key = (uid, occurrence_start.date())
                        if exception_key in exceptions:
                            # Use the exception event instead
                            exception = exceptions[exception_key]
                            exception_start = exception.get("dtstart").dt
                            exception_end = exception.get("dtend").dt
                            if isinstance(exception_start, datetime):
                                if exception_start.tzinfo is None:
                                    exception_start = local_tz.localize(exception_start)
                                else:
                                    exception_start = exception_start.astimezone(
                                        local_tz
                                    )

                                if exception_end.tzinfo is None:
                                    exception_end = local_tz.localize(exception_end)
                                else:
                                    exception_end = exception_end.astimezone(local_tz)

                                if week_start <= exception_start < week_end:
                                    events.append(
                                        {
                                            "summary": str(
                                                exception.get("summary", "No Title")
                                            ),
                                            "start": exception_start,
                                            "end": exception_end,
                                            "location": str(
                                                exception.get("location", "")
                                            ),
                                            "description": str(
                                                exception.get("description", "")
                                            ),
                                        }
                                    )
                            continue

                        # Skip if there's a matching EXDATE
                        if component.get("exdate"):
                            exdates = component.get("exdate")
                            if not isinstance(exdates, list):
                                exdates = [exdates]
                            skip = False
                            for exdate in exdates:
                                excluded_dates = exdate.dts
                                for excluded in excluded_dates:
                                    if (
                                        excluded.dt.astimezone(local_tz).date()
                                        == occurrence_start.date()
                                    ):
                                        skip = True
                                        break
                            if skip:
                                continue

                        events.append(
                            {
                                "summary": str(component.get("summary", "No Title")),
                                "start": occurrence_start,
                                "end": occurrence_end,
                                "location": str(component.get("location", "")),
                                "description": str(component.get("description", "")),
                            }
                        )
                elif week_start <= start < week_end:
                    events.append(
                        {
                            "summary": str(component.get("summary", "No Title")),
                            "start": start,
                            "end": end,
                            "location": str(component.get("location", "")),
                            "description": str(component.get("description", "")),
                        }
                    )

        return sorted(events, key=lambda x: x["start"])

    except Exception as e:
        print(f"Error parsing calendar file: {e}")
        return []
