
from datetime import date, datetime, time, timedelta, timezone
from zoneinfo import ZoneInfo

from app import create_app
from app.extensions import db
from app.models import Flight, FlightSchedule


NAIROBI_TZ = ZoneInfo("Africa/Nairobi")


# Demonstration routes, prices and schedules.
FLIGHTS = [
    # Kenya domestic
    ("AQ101", "Nairobi", "Mombasa", "NBO", "MBA", 8500, 30, "09:00", 75),
    ("AQ102", "Nairobi", "Kisumu", "NBO", "KIS", 6500, 30, "08:00", 60),
    ("AQ103", "Nairobi", "Eldoret", "NBO", "EDL", 7000, 30, "10:00", 65),
    ("AQ104", "Nairobi", "Malindi", "NBO", "MYD", 9500, 30, "11:00", 80),
    ("AQ105", "Nairobi", "Ukunda", "NBO", "UKA", 9000, 30, "12:00", 75),
    ("AQ106", "Nairobi", "Lamu", "NBO", "LAU", 10500, 30, "13:00", 90),
    ("AQ107", "Mombasa", "Nairobi", "MBA", "NBO", 8500, 30, "14:00", 75),
    ("AQ108", "Mombasa", "Kisumu", "MBA", "KIS", 11000, 30, "15:00", 100),

    # Africa
    ("AQ201", "Nairobi", "Lagos", "NBO", "LOS", 52000, 40, "08:00", 300),
    ("AQ202", "Nairobi", "Kigali", "NBO", "KGL", 26000, 40, "09:30", 100),
    ("AQ203", "Nairobi", "Kampala", "NBO", "EBB", 22000, 40, "10:00", 90),
    ("AQ204", "Nairobi", "Dar es Salaam", "NBO", "DAR", 18000, 40, "11:00", 90),
    ("AQ205", "Nairobi", "Addis Ababa", "NBO", "ADD", 30000, 40, "12:00", 150),
    ("AQ206", "Nairobi", "Johannesburg", "NBO", "JNB", 48000, 40, "13:00", 245),
    ("AQ207", "Nairobi", "Cairo", "NBO", "CAI", 55000, 40, "14:00", 300),
    ("AQ208", "Mombasa", "Zanzibar", "MBA", "ZNZ", 24000, 40, "15:00", 75),

    # International
    ("AQ301", "Nairobi", "London", "NBO", "LHR", 95000, 50, "08:00", 510),
    ("AQ302", "Nairobi", "Paris", "NBO", "CDG", 90000, 50, "09:00", 510),
    ("AQ303", "Nairobi", "Dubai", "NBO", "DXB", 55000, 50, "10:00", 300),
    ("AQ304", "Nairobi", "Doha", "NBO", "DOH", 58000, 50, "11:00", 300),
    ("AQ305", "Nairobi", "New York", "NBO", "JFK", 145000, 50, "12:00", 900),
    ("AQ306", "Nairobi", "Istanbul", "NBO", "IST", 78000, 50, "13:00", 390),
    ("AQ307", "Nairobi", "Mumbai", "NBO", "BOM", 65000, 50, "14:00", 330),
    ("AQ308", "Nairobi", "Amsterdam", "NBO", "AMS", 92000, 50, "15:00", 510),
]


# Destination images in frontend/public/images/destinations.
IMAGES = {
    "Nairobi": "/images/destinations/nairobi.jpg",
    "Mombasa": "/images/destinations/mombasa.jpg",
    "Kisumu": "/images/destinations/kisumu.jpg",
    "Eldoret": "/images/destinations/eldoret.jpg",
    "Malindi": "/images/destinations/malindi.jpg",
    "Ukunda": "/images/destinations/ukunda.jpg",
    "Lamu": "/images/destinations/lamu.jpg",
    "Lagos": "/images/destinations/lagos.jpg",
    "Kigali": "/images/destinations/kigali.jpg",
    "Kampala": "/images/destinations/kampala.jpg",
    "Dar es Salaam": "/images/destinations/dar-es-salaam.jpg",
    "Addis Ababa": "/images/destinations/addis-ababa.jpg",
    "Johannesburg": "/images/destinations/johannesburg.jpg",
    "Cairo": "/images/destinations/cairo.jpg",
    "Zanzibar": "/images/destinations/zanzibar.jpg",
    "London": "/images/destinations/london.jpg",
    "Paris": "/images/destinations/paris.jpg",
    "Dubai": "/images/destinations/dubai.jpg",
    "Doha": "/images/destinations/doha.jpg",
    "New York": "/images/destinations/new-york.jpg",
    "Istanbul": "/images/destinations/istanbul.jpg",
    "Mumbai": "/images/destinations/mumbai.jpg",
    "Amsterdam": "/images/destinations/amsterdam.jpg",
}


def make_utc_datetime(day, clock):
    hours, minutes = map(int, clock.split(":"))

    local_datetime = datetime.combine(
        day,
        time(hours, minutes),
        tzinfo=NAIROBI_TZ,
    )

    return local_datetime.astimezone(timezone.utc)


def seed_flights():
    today = datetime.now(NAIROBI_TZ).date()
    first_day = max(today, date(2026, 11, 6))

    for (
        number,
        origin,
        destination,
        origin_code,
        destination_code,
        price,
        seats,
        departure_time,
        duration_minutes,
    ) in FLIGHTS:

        flight = Flight.query.filter_by(
            flight_number=number
        ).first()

        if flight is None:
            flight = Flight(flight_number=number)
            db.session.add(flight)

        flight.origin = origin
        flight.destination = destination
        flight.origin_code = origin_code
        flight.destination_code = destination_code
        flight.base_price = price
        flight.total_seats = seats
        flight.destination_image = IMAGES.get(destination)

        db.session.flush()

        for day_offset in range(30):
            travel_date = first_day + timedelta(days=day_offset)

            departure = make_utc_datetime(
                travel_date,
                departure_time,
            )

            arrival = departure + timedelta(
                minutes=duration_minutes
            )

            existing_schedule = FlightSchedule.query.filter_by(
                flight_id=flight.id,
                departure_at=departure.replace(tzinfo=None),
            ).first()

            if existing_schedule:
                continue

            schedule = FlightSchedule(
                flight_id=flight.id,
                departure_at=departure,
                arrival_at=arrival,
                available_seats=seats,
                status="SCHEDULED",
            )

            db.session.add(schedule)

        print(f"Processed {number}: {origin} -> {destination}")

    db.session.commit()

    print("\nFlight seeding completed.")
    print(f"Routes configured: {len(FLIGHTS)}")
    print("Schedules: up to 30 per route.")


if __name__ == "__main__":
    app = create_app()

    with app.app_context():
        seed_flights()
