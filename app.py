
import os
import uuid
from datetime import date

from flask import (
    Flask, render_template, request, redirect,
    url_for, flash, session
)
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash

from recommender import recommend_destinations


# ============================================================
# FLASK CONFIGURATION
# ============================================================

app = Flask(__name__)

app.config["SECRET_KEY"] = os.environ.get(
    "SECRET_KEY", "voyageiq-local-development-key"
)

database_url = os.environ.get("DATABASE_URL")

if database_url and database_url.startswith("postgres://"):
    database_url = database_url.replace(
        "postgres://", "postgresql://", 1
    )

app.config["SQLALCHEMY_DATABASE_URI"] = (
    database_url or "sqlite:///voyageiq.db"
)

app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
db = SQLAlchemy(app)


# ============================================================
# DATABASE MODELS
# ============================================================

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)


class HotelBooking(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    booking_code = db.Column(db.String(20), unique=True, nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"))
    hotel_name = db.Column(db.String(150), nullable=False)
    destination = db.Column(db.String(100), nullable=False)
    checkin = db.Column(db.String(10), nullable=False)
    checkout = db.Column(db.String(10), nullable=False)
    guests = db.Column(db.Integer, nullable=False)
    room_type = db.Column(db.String(50), nullable=False)
    nights = db.Column(db.Integer, nullable=False)
    total_price = db.Column(db.Integer, nullable=False)


class TransportBooking(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    booking_code = db.Column(db.String(20), unique=True, nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"))
    transport_type = db.Column(db.String(20), nullable=False)
    provider_name = db.Column(db.String(100), nullable=False)
    origin = db.Column(db.String(100), nullable=False)
    destination = db.Column(db.String(100), nullable=False)
    travel_date = db.Column(db.String(10), nullable=False)
    departure = db.Column(db.String(10), nullable=False)
    arrival = db.Column(db.String(10), nullable=False)
    passengers = db.Column(db.Integer, nullable=False)
    seat_class = db.Column(db.String(50), nullable=False)
    total_price = db.Column(db.Integer, nullable=False)


class TransportBookingExtra(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    booking_id = db.Column(
        db.Integer,
        db.ForeignKey("transport_booking.id"),
        unique=True,
        nullable=False
    )
    passenger_name = db.Column(db.String(100), nullable=False)
    passenger_email = db.Column(db.String(120), nullable=False)
    passenger_phone = db.Column(db.String(20), nullable=False)
    passenger_age = db.Column(db.Integer, nullable=False)
    passenger_gender = db.Column(db.String(30), nullable=False)
    seat_numbers = db.Column(db.String(200), nullable=False)
    payment_method = db.Column(db.String(40), nullable=False)
    payment_status = db.Column(db.String(40), nullable=False)


class BookingCancellation(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    booking_type = db.Column(db.String(20), nullable=False)
    booking_id = db.Column(db.Integer, nullable=False)
    cancelled_at = db.Column(
        db.DateTime,
        server_default=db.func.current_timestamp()
    )

    __table_args__ = (
        db.UniqueConstraint(
            "booking_type",
            "booking_id",
            name="unique_booking_cancellation"
        ),
    )


# ============================================================
# DESTINATION DATA
# ============================================================

DESTINATIONS = [
    {
        "name": "Mumbai",
        "state": "Maharashtra",
        "district": "Mumbai",
        "interest": "culture",
        "cost": 2000,
        "places": ["Gateway of India", "Marine Drive"],
        "description": "Explore the city and its historic landmarks.",
        "image": "https://images.unsplash.com/photo-1570168007204-dfb528c6958f"
    },
    {
        "name": "Mysuru",
        "state": "Karnataka",
        "district": "Mysuru",
        "interest": "culture",
        "cost": 1500,
        "places": ["Mysore Palace", "Chamundi Hills"],
        "description": "Discover royal heritage and local culture.",
        "image": "https://images.unsplash.com/photo-1600112356915-089abb8fc71a"
    },
    {
        "name": "Coorg",
        "state": "Karnataka",
        "district": "Kodagu",
        "interest": "nature",
        "cost": 1800,
        "places": ["Abbey Falls", "Raja's Seat"],
        "description": "Enjoy green hills and waterfalls.",
        "image": "https://images.unsplash.com/photo-1464822759023-fed622ff2c3b"
    },
    {
        "name": "Goa",
        "state": "Goa",
        "district": "North Goa",
        "interest": "beach",
        "cost": 2500,
        "places": ["Baga Beach", "Fort Aguada"],
        "description": "Relax on beaches and explore coastal heritage.",
        "image": "https://images.unsplash.com/photo-1512343879784-a960bf40e7f2"
    },
    {
        "name": "Manali",
        "state": "Himachal Pradesh",
        "district": "Kullu",
        "interest": "mountains",
        "cost": 2500,
        "places": ["Solang Valley", "Hadimba Temple"],
        "description": "Enjoy mountain scenery.",
        "image": "https://images.unsplash.com/photo-1626621341517-bbf3d9990a23"
    },
    {
        "name": "Jaipur",
        "state": "Rajasthan",
        "district": "Jaipur",
        "interest": "culture",
        "cost": 2000,
        "places": ["Hawa Mahal", "Amber Fort"],
        "description": "Explore forts, palaces and markets.",
        "image": "https://images.unsplash.com/photo-1599661046827-dacff0c0f09a"
    },
    {
        "name": "Tirupati",
        "state": "Andhra Pradesh",
        "district": "Tirupati",
        "interest": "temples",
        "cost": 1800,
        "places": ["Sri Venkateswara Temple"],
        "description": "Visit the famous pilgrimage destination.",
        "image": "https://images.unsplash.com/photo-1606293926075-69a00dbfde81"
    },
    {
        "name": "Madurai",
        "state": "Tamil Nadu",
        "district": "Madurai",
        "interest": "temples",
        "cost": 1600,
        "places": ["Meenakshi Amman Temple"],
        "description": "Discover historic temple architecture.",
        "image": "https://images.unsplash.com/photo-1600100397608-f010e9b1e9d5"
    },
    {
        "name": "Ayodhya",
        "state": "Uttar Pradesh",
        "district": "Ayodhya",
        "interest": "temples",
        "cost": 1800,
        "places": ["Shri Ram Janmabhoomi Mandir"],
        "description": "Explore a historic pilgrimage destination.",
        "image": "https://images.unsplash.com/photo-1548013146-72479768bada"
    },
    {
        "name": "Bengaluru",
        "state": "Karnataka",
        "district": "Bengaluru Urban",
        "interest": "temples",
        "cost": 1200,
        "places": ["ISKCON Temple", "Bull Temple"],
        "description": "Visit temples and cultural landmarks.",
        "image": "https://images.unsplash.com/photo-1590050752117-238cb0fb12b1"
    },
]


# ============================================================
# HOTEL DATA
# ============================================================

HOTELS = [
    {
        "id": 1,
        "name": "Green Leaf Comfort Stay",
        "city": "Bengaluru",
        "price": 1800,
        "rating": "4.2",
        "type": "Standard Room",
        "image": "https://images.unsplash.com/photo-1566073771259-6a8506099945?w=800"
    },
    {
        "id": 2,
        "name": "Royal Garden Hotel",
        "city": "Bengaluru",
        "price": 3200,
        "rating": "4.5",
        "type": "Deluxe Room",
        "image": "https://images.unsplash.com/photo-1566665797739-1674de7a421a?w=800"
    },
    {
        "id": 3,
        "name": "Ocean Breeze Resort",
        "city": "Goa",
        "price": 4500,
        "rating": "4.7",
        "type": "Sea View Room",
        "image": "https://images.unsplash.com/photo-1571896349842-33c89424de2d?w=800"
    },
    {
        "id": 4,
        "name": "Heritage Palace Stay",
        "city": "Mysuru",
        "price": 2800,
        "rating": "4.4",
        "type": "Premium Room",
        "image": "https://images.unsplash.com/photo-1542314831-068cd1dbfeeb?w=800"
    },
    {
        "id": 5,
        "name": "Mountain View Retreat",
        "city": "Ooty",
        "price": 3500,
        "rating": "4.6",
        "type": "Hill View Room",
        "image": "https://images.unsplash.com/photo-1445019980597-93fa8acb246c?w=800"
    },
    {
        "id": 6,
        "name": "City Lights Hotel",
        "city": "Mumbai",
        "price": 4000,
        "rating": "4.3",
        "type": "Deluxe Room",
        "image": "https://images.unsplash.com/photo-1551882547-ff40c63fe5fa?w=800"
    },
]

ROOM_PRICES = {
    "Standard": 1.0,
    "Deluxe": 1.5,
    "Suite": 2.0
}


# ============================================================
# TRANSPORT DATA
# ============================================================

TRANSPORT_CITIES = [
    "Bengaluru", "Goa", "Mumbai", "Mysuru", "Jaipur",
    "Manali", "Coorg", "Tirupati", "Madurai", "Ayodhya"
]

TRANSPORT_OPTIONS = [
    {
        "id": 1,
        "type": "Flight",
        "provider": "Voyage Air",
        "origin": "Bengaluru",
        "destination": "Goa",
        "price": 4200,
        "departure": "08:30",
        "arrival": "10:00",
        "duration": "1h 30m",
        "seats": 12,
        "classes": ["Economy", "Business"]
    },
    {
        "id": 2,
        "type": "Train",
        "provider": "Coastal Express (Demo)",
        "origin": "Bengaluru",
        "destination": "Goa",
        "price": 950,
        "departure": "18:00",
        "arrival": "08:00",
        "duration": "14h",
        "seats": 24,
        "classes": ["Sleeper", "AC 3 Tier", "AC 2 Tier"]
    },
    {
        "id": 3,
        "type": "Bus",
        "provider": "Coastline Travels",
        "origin": "Bengaluru",
        "destination": "Goa",
        "price": 1200,
        "departure": "20:00",
        "arrival": "09:00",
        "duration": "13h",
        "seats": 18,
        "classes": ["Seater", "Sleeper"]
    },
    {
        "id": 4,
        "type": "Flight",
        "provider": "Voyage Air",
        "origin": "Bengaluru",
        "destination": "Mumbai",
        "price": 5100,
        "departure": "07:15",
        "arrival": "09:00",
        "duration": "1h 45m",
        "seats": 10,
        "classes": ["Economy", "Business"]
    },
    {
        "id": 5,
        "type": "Train",
        "provider": "Deccan Express (Demo)",
        "origin": "Bengaluru",
        "destination": "Mumbai",
        "price": 1100,
        "departure": "21:00",
        "arrival": "17:00",
        "duration": "20h",
        "seats": 30,
        "classes": ["Sleeper", "AC 3 Tier", "AC 2 Tier"]
    },
    {
        "id": 6,
        "type": "Bus",
        "provider": "Mysuru Roadways",
        "origin": "Bengaluru",
        "destination": "Mysuru",
        "price": 450,
        "departure": "09:00",
        "arrival": "12:30",
        "duration": "3h 30m",
        "seats": 20,
        "classes": ["Seater", "Sleeper"]
    },
    {
        "id": 7,
        "type": "Train",
        "provider": "City Link Rail (Demo)",
        "origin": "Bengaluru",
        "destination": "Mysuru",
        "price": 220,
        "departure": "10:00",
        "arrival": "12:45",
        "duration": "2h 45m",
        "seats": 32,
        "classes": ["General", "Chair Car", "AC Chair Car"]
    },
    {
        "id": 8,
        "type": "Flight",
        "provider": "Voyage Air",
        "origin": "Bengaluru",
        "destination": "Jaipur",
        "price": 6200,
        "departure": "06:30",
        "arrival": "09:15",
        "duration": "2h 45m",
        "seats": 8,
        "classes": ["Economy", "Business"]
    },
    {
        "id": 9,
        "type": "Bus",
        "provider": "Western Coast Travels",
        "origin": "Mumbai",
        "destination": "Goa",
        "price": 1000,
        "departure": "22:00",
        "arrival": "08:00",
        "duration": "10h",
        "seats": 16,
        "classes": ["Seater", "Sleeper"]
    },
    {
        "id": 10,
        "type": "Train",
        "provider": "Mysuru-Bengaluru Rail (Demo)",
        "origin": "Mysuru",
        "destination": "Bengaluru",
        "price": 250,
        "departure": "14:00",
        "arrival": "16:45",
        "duration": "2h 45m",
        "seats": 28,
        "classes": ["General", "Chair Car", "AC Chair Car"]
    },
]

TRANSPORT_CLASS_MULTIPLIERS = {
    "Economy": 1.0,
    "Business": 2.5,
    "General": 1.0,
    "Chair Car": 1.5,
    "AC Chair Car": 1.8,
    "Sleeper": 1.0,
    "AC 3 Tier": 1.5,
    "AC 2 Tier": 2.0,
    "Seater": 1.0
}

PAYMENT_METHODS = {
    "UPI",
    "Credit/Debit Card (Demo)",
    "Net Banking (Demo)",
    "Pay Later"
}


# ============================================================
# HOMEPAGE
# ============================================================

@app.route("/")
def home():
    return render_template("index.html")


# ============================================================
# SETTINGS PAGE
# ============================================================

@app.route("/settings")
def settings():
    return render_template("settings.html")


# ============================================================
# WISHLIST PAGE
# ============================================================

@app.route("/wishlist")
def wishlist():
    return render_template("wishlist.html")


# ============================================================
# THEME PAGE
# ============================================================

@app.route("/theme")
def theme():
    return render_template("theme.html")


# ============================================================
# PERSONAL DETAILS PAGE
# ============================================================

@app.route("/personal-details")
def personal_details():

    if "user_id" not in session:
        flash("Please log in to view your personal details.")
        return redirect(url_for("login"))

    user = db.session.get(User, session["user_id"])

    if user is None:
        session.clear()
        flash("Please log in again.")
        return redirect(url_for("login"))

    return render_template(
        "personal_details.html",
        user=user
    )


# ============================================================
# SIGNUP
# ============================================================

@app.route("/signup", methods=["GET", "POST"])
def signup():

    if request.method == "POST":

        name = request.form.get("name", "").strip()
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")

        if not name or not email or len(password) < 8:
            flash(
                "Enter your name and email, and use a password "
                "of at least 8 characters."
            )
            return redirect(url_for("signup"))

        if User.query.filter_by(email=email).first():
            flash("This email is already registered. Please log in.")
            return redirect(url_for("login"))

        user = User(
            name=name,
            email=email,
            password_hash=generate_password_hash(password)
        )

        db.session.add(user)
        db.session.commit()

        flash("Account created! Please log in.")
        return redirect(url_for("login"))

    return render_template("signup.html")


# ============================================================
# LOGIN
# ============================================================

@app.route("/login", methods=["GET", "POST"])
def login():

    if request.method == "POST":

        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")

        user = User.query.filter_by(email=email).first()

        if user and check_password_hash(user.password_hash, password):
            session.clear()
            session["user_id"] = user.id
            session["user_name"] = user.name

            return redirect(url_for("home"))

        flash("Incorrect email or password.")

    return render_template("login.html")


# ============================================================
# LOGOUT
# ============================================================

@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("home"))


# ============================================================
# TRIP PLANNER WITH AI/ML RECOMMENDATIONS
# ============================================================

@app.route("/planner", methods=["GET", "POST"])
def planner():

    recommendations = []
    itinerary = []
    budget = 0
    days = 3
    origin = ""
    interest = "all"
    searched = False

    if request.method == "POST":

        origin = request.form.get("origin", "").strip()

        interest = request.form.get(
            "interest", "all"
        ).strip().lower()

        searched = True

        try:
            budget = int(request.form.get("budget", "0"))
            days = int(request.form.get("days", "3"))

        except (ValueError, TypeError):
            flash("Enter a valid budget and trip duration.")
            return redirect(url_for("planner"))

        if budget < 1 or not 1 <= days <= 14:
            flash("Enter a positive budget and choose 1–14 days.")

        else:

            location = origin.casefold()
            filtered_destinations = []

            for place in DESTINATIONS:

                location_matches = (
                    location in place["name"].casefold()
                    or location in place["state"].casefold()
                    or location in place["district"].casefold()
                    or location == "india"
                )

                interest_matches = (
                    interest == "all"
                    or place["interest"] == interest
                    or (
                        interest == "temples"
                        and any(
                            "temple" in attraction.casefold()
                            for attraction in place["places"]
                        )
                    )
                )

                budget_matches = place["cost"] * days <= budget

                if (
                    location_matches
                    and interest_matches
                    and budget_matches
                ):
                    filtered_destinations.append(place)

            if filtered_destinations:

                recommendations = recommend_destinations(
                    filtered_destinations,
                    interest=interest,
                    origin="India",
                    budget=0,
                    days=days
                )

            if not recommendations:

                flash(
                    "No matching destinations. Try India, "
                    "a listed city, or All interests."
                )

            else:

                places = [
                    place["name"]
                    for place in recommendations
                ]

                for day in range(days):

                    itinerary.append({
                        "day": day + 1,
                        "morning": places[
                            (day * 2) % len(places)
                        ],
                        "afternoon": places[
                            (day * 2 + 1) % len(places)
                        ],
                        "evening": "Explore local food and markets"
                    })

    return render_template(
        "planner.html",
        recommendations=recommendations,
        itinerary=itinerary,
        budget=budget,
        days=days,
        origin=origin,
        interest=interest,
        searched=searched
    )


# ============================================================
# HOTELS
# ============================================================

@app.route("/hotels")
def hotels():

    destination = request.args.get(
        "destination", "Bengaluru"
    ).strip()

    return render_template(
        "hotels.html",
        hotels=HOTELS,
        destination=destination
    )


# ============================================================
# HOTEL BOOKING
# ============================================================

@app.route("/book-hotel", methods=["GET", "POST"])
def book_hotel():

    if request.method == "GET":

        try:
            hotel_id = int(request.args.get("hotel_id", "1"))
        except ValueError:
            hotel_id = 1

        hotel = next(
            (item for item in HOTELS if item["id"] == hotel_id),
            None
        )

        if hotel is None:
            flash("Hotel not found. Please select a hotel again.")
            return redirect(url_for("hotels"))

        return render_template(
            "booking.html",
            hotel=hotel,
            checkin=request.args.get("checkin", ""),
            checkout=request.args.get("checkout", ""),
            guests=request.args.get("guests", "2"),
            room_prices=ROOM_PRICES
        )

    try:

        hotel_id = int(request.form.get("hotel_id", "0"))
        guests = int(request.form.get("guests", "0"))

        checkin = date.fromisoformat(
            request.form.get("checkin", "")
        )

        checkout = date.fromisoformat(
            request.form.get("checkout", "")
        )

    except (ValueError, TypeError):

        flash("Please enter valid booking details.")
        return redirect(url_for("hotels"))

    hotel = next(
        (item for item in HOTELS if item["id"] == hotel_id),
        None
    )

    room_type = request.form.get("room_type", "")

    if hotel is None or not 1 <= guests <= 4:
        flash("Please select a valid hotel and guest count.")
        return redirect(url_for("hotels"))

    if checkin < date.today() or checkout <= checkin:
        flash("Choose valid future dates and a later check-out date.")
        return redirect(
            url_for("book_hotel", hotel_id=hotel_id)
        )

    if room_type not in ROOM_PRICES:
        flash("Please select a valid room type.")
        return redirect(
            url_for("book_hotel", hotel_id=hotel_id)
        )

    nights = (checkout - checkin).days

    total_price = int(
        hotel["price"] * ROOM_PRICES[room_type] * nights
    )

    booking = HotelBooking(
        booking_code="VQ-" + uuid.uuid4().hex[:8].upper(),
        user_id=session.get("user_id"),
        hotel_name=hotel["name"],
        destination=hotel["city"],
        checkin=checkin.isoformat(),
        checkout=checkout.isoformat(),
        guests=guests,
        room_type=room_type,
        nights=nights,
        total_price=total_price
    )

    db.session.add(booking)
    db.session.commit()

    return redirect(
        url_for(
            "booking_confirmation",
            booking_id=booking.id
        )
    )


# ============================================================
# HOTEL BOOKING CONFIRMATION
# ============================================================

@app.route("/booking-confirmation/<int:booking_id>")
def booking_confirmation(booking_id):

    booking = db.session.get(HotelBooking, booking_id)

    if booking is None:
        flash("Booking not found.")
        return redirect(url_for("hotels"))

    if (
        booking.user_id is not None
        and session.get("user_id") != booking.user_id
    ):
        flash("Please log in with the account used for this booking.")
        return redirect(url_for("login"))

    return render_template(
        "booking_confirmation.html",
        booking=booking
    )


# ============================================================
# TRANSPORT SEARCH
# ============================================================

@app.route("/transport", methods=["GET", "POST"])
def transport():

    origin = request.form.get("origin", "Bengaluru").strip()
    destination = request.form.get("destination", "Goa").strip()

    travel_date = request.form.get(
        "travel_date", date.today().isoformat()
    )

    transport_type = request.form.get(
        "transport_type", "All"
    ).strip()

    searched = request.method == "POST"
    results = []

    try:

        passengers = int(request.form.get("passengers", "1"))

        if not 1 <= passengers <= 6:
            raise ValueError

    except (ValueError, TypeError):

        passengers = 1
        flash("Choose between 1 and 6 passengers.")

    try:

        selected_date = date.fromisoformat(travel_date)

        if selected_date < date.today():

            travel_date = date.today().isoformat()

            if searched:
                flash(
                    "Please choose today or a future travel date."
                )

    except (ValueError, TypeError):

        travel_date = date.today().isoformat()

        if searched:
            flash("Please choose a valid travel date.")

    if searched and origin != destination:

        for option in TRANSPORT_OPTIONS:

            if (
                option["origin"].casefold() == origin.casefold()
                and option["destination"].casefold() == destination.casefold()
                and (
                    transport_type == "All"
                    or option["type"] == transport_type
                )
            ):
                results.append(option)

        if not results:
            flash(
                "No demo options for this route. "
                "Try Bengaluru to Goa, Mumbai, or Mysuru."
            )

    elif searched:
        flash("Choose different origin and destination cities.")

    return render_template(
        "transport.html",
        cities=TRANSPORT_CITIES,
        origin=origin,
        destination=destination,
        travel_date=travel_date,
        today=date.today().isoformat(),
        transport_type=transport_type,
        passengers=passengers,
        searched=searched,
        results=results
    )


# ============================================================
# START TRANSPORT BOOKING
# ============================================================

@app.route("/book-transport", methods=["POST"])
def book_transport():

    try:

        option_id = int(request.form.get("option_id", "0"))
        passengers = int(request.form.get("passengers", "1"))

        travel_date = date.fromisoformat(
            request.form.get("travel_date", "")
        )

    except (ValueError, TypeError):

        flash("Please enter valid transport booking details.")
        return redirect(url_for("transport"))

    option = next(
        (item for item in TRANSPORT_OPTIONS if item["id"] == option_id),
        None
    )

    seat_class = request.form.get("seat_class", "")

    if option is None or seat_class not in option["classes"]:
        flash("Please select a valid transport option and class.")
        return redirect(url_for("transport"))

    if not 1 <= passengers <= 6 or travel_date < date.today():
        flash("Check the passenger count and travel date.")
        return redirect(url_for("transport"))

    multiplier = TRANSPORT_CLASS_MULTIPLIERS.get(seat_class, 1.0)

    total_price = int(
        option["price"] * multiplier * passengers
    )

    session["pending_transport"] = {
        "option_id": option["id"],
        "transport_type": option["type"],
        "provider_name": option["provider"],
        "origin": option["origin"],
        "destination": option["destination"],
        "travel_date": travel_date.isoformat(),
        "departure": option["departure"],
        "arrival": option["arrival"],
        "passengers": passengers,
        "seat_class": seat_class,
        "total_price": total_price
    }

    session.pop("pending_passenger", None)
    session.pop("pending_payment_method", None)

    session.modified = True

    return redirect(url_for("seat_selection"))


# ============================================================
# SEAT SELECTION
# ============================================================

@app.route("/seat-selection", methods=["GET", "POST"])
def seat_selection():

    pending = session.get("pending_transport")

    if not pending:
        flash("Please select your journey first.")
        return redirect(url_for("transport"))

    if request.method == "POST":

        raw_seats = request.form.get("seat_numbers", "")

        if not raw_seats:
            selected_seats = request.form.getlist("seats")
        else:
            selected_seats = raw_seats.split(",")

        seats = [
            seat.strip().upper()
            for seat in selected_seats
            if seat.strip()
        ]

        seats = list(dict.fromkeys(seats))
        passengers = int(pending.get("passengers", 1))

        valid_seats = {
            f"{row}{number}"
            for row in "ABCDEF"
            for number in range(1, 7)
        }

        if len(seats) != passengers or any(
            seat not in valid_seats for seat in seats
        ):
            flash(f"Select exactly {passengers} valid seat(s).")
            return redirect(url_for("seat_selection"))

        unavailable = {"A2", "B3", "C1", "D4", "E2", "F3"}

        if any(seat in unavailable for seat in seats):
            flash(
                "One selected seat is unavailable in this demo. "
                "Choose another."
            )
            return redirect(url_for("seat_selection"))

        updated_pending = dict(pending)
        updated_pending["seat_numbers"] = sorted(seats)

        session["pending_transport"] = updated_pending
        session.modified = True

        return redirect(url_for("passenger_details"))

    return render_template(
        "seat_selection.html",
        booking=pending,
        passengers=pending["passengers"],
        transport_type=pending["transport_type"]
    )


# ============================================================
# PASSENGER DETAILS
# ============================================================

@app.route("/passenger-details", methods=["GET", "POST"])
def passenger_details():

    pending = session.get("pending_transport")

    if not pending:
        flash("Please select your journey first.")
        return redirect(url_for("transport"))

    if not pending.get("seat_numbers"):
        return redirect(url_for("seat_selection"))

    if request.method == "POST":

        name = request.form.get("name", "").strip()
        email = request.form.get("email", "").strip().lower()
        phone = request.form.get("phone", "").strip()
        gender = request.form.get("gender", "").strip()

        try:
            age = int(request.form.get("age", "0"))
        except ValueError:
            age = 0

        if (
            not name
            or len(name) > 100
            or "@" not in email
            or len(email) > 120
            or not phone.isdigit()
            or len(phone) != 10
            or not 1 <= age <= 120
            or gender not in [
                "Female", "Male", "Other",
                "Prefer not to say"
            ]
        ):
            flash("Please enter valid passenger details.")
            return redirect(url_for("passenger_details"))

        session["pending_passenger"] = {
            "name": name,
            "age": age,
            "gender": gender,
            "email": email,
            "phone": phone
        }

        session.modified = True

        return redirect(url_for("booking_summary"))

    return render_template(
        "passenger_details.html",
        booking=pending,
        passenger_count=pending["passengers"],
        seats=pending.get("seat_numbers", [])
    )


# ============================================================
# BOOKING SUMMARY
# ============================================================

@app.route("/booking-summary", methods=["GET", "POST"])
def booking_summary():

    if request.method == "POST":

        pending = session.get("pending_transport")

        if not pending:
            flash("Please select your journey first.")
            return redirect(url_for("transport"))

        name = request.form.get("name", "").strip()
        email = request.form.get("email", "").strip().lower()
        phone = request.form.get("phone", "").strip()
        gender = request.form.get("gender", "").strip()

        try:
            age = int(request.form.get("age", "0"))
        except ValueError:
            age = 0

        if (
            not name
            or len(name) > 100
            or "@" not in email
            or len(email) > 120
            or not phone.isdigit()
            or len(phone) != 10
            or not 1 <= age <= 120
            or gender not in [
                "Female", "Male", "Other",
                "Prefer not to say"
            ]
        ):
            flash("Please enter valid passenger details.")
            return redirect(url_for("passenger_details"))

        session["pending_passenger"] = {
            "name": name,
            "age": age,
            "gender": gender,
            "email": email,
            "phone": phone
        }

        session.modified = True

    pending = session.get("pending_transport")
    passenger = session.get("pending_passenger")

    if not pending or not passenger:
        flash("Please complete passenger details first.")
        return redirect(url_for("transport"))

    if not pending.get("seat_numbers"):
        return redirect(url_for("seat_selection"))

    return render_template(
        "booking_summary.html",
        passenger=passenger,
        booking=pending,
        payment_methods=sorted(PAYMENT_METHODS)
    )


# ============================================================
# DEMO PAYMENT
# ============================================================

@app.route("/payment", methods=["POST"])
def payment():

    pending = session.get("pending_transport")
    passenger = session.get("pending_passenger")

    if not pending or not passenger:
        flash("Your booking session expired. Please start again.")
        return redirect(url_for("transport"))

    payment_method = request.form.get(
        "payment_method", ""
    ).strip()

    if payment_method not in PAYMENT_METHODS:
        flash("Please choose a payment method.")
        return redirect(url_for("booking_summary"))

    session["pending_payment_method"] = payment_method
    session.modified = True

    return render_template(
        "payment.html",
        booking=pending,
        passenger=passenger,
        payment_method=payment_method
    )


# ============================================================
# CONFIRM TRANSPORT BOOKING
# ============================================================

@app.route("/confirm-transport-booking", methods=["POST"])
def confirm_transport_booking():

    pending = session.get("pending_transport")
    passenger = session.get("pending_passenger")
    payment_method = session.get("pending_payment_method")

    if not pending or not passenger or not payment_method:
        flash("Your booking session expired. Please start again.")
        return redirect(url_for("transport"))

    seats = pending.get("seat_numbers", [])

    if len(seats) != pending["passengers"]:
        flash("Please select seats before confirming.")
        return redirect(url_for("seat_selection"))

    existing_id = session.get("confirmed_transport_booking_id")

    if existing_id:

        existing = db.session.get(TransportBooking, existing_id)

        if existing:
            return redirect(
                url_for(
                    "transport_confirmation",
                    booking_id=existing.id
                )
            )

    booking = TransportBooking(
        booking_code="VQT-" + uuid.uuid4().hex[:8].upper(),
        user_id=session.get("user_id"),
        transport_type=pending["transport_type"],
        provider_name=pending["provider_name"],
        origin=pending["origin"],
        destination=pending["destination"],
        travel_date=pending["travel_date"],
        departure=pending["departure"],
        arrival=pending["arrival"],
        passengers=pending["passengers"],
        seat_class=pending["seat_class"],
        total_price=pending["total_price"]
    )

    db.session.add(booking)
    db.session.flush()

    extra = TransportBookingExtra(
        booking_id=booking.id,
        passenger_name=passenger["name"],
        passenger_email=passenger["email"],
        passenger_phone=passenger["phone"],
        passenger_age=passenger["age"],
        passenger_gender=passenger["gender"],
        seat_numbers=", ".join(seats),
        payment_method=payment_method,
        payment_status=(
            "Pay Later - Pending"
            if payment_method == "Pay Later"
            else "Demo Payment Successful"
        )
    )

    db.session.add(extra)
    db.session.commit()

    session["confirmed_transport_booking_id"] = booking.id

    session.pop("pending_transport", None)
    session.pop("pending_passenger", None)
    session.pop("pending_payment_method", None)

    session.modified = True

    return redirect(
        url_for(
            "transport_confirmation",
            booking_id=booking.id
        )
    )


# ============================================================
# TRANSPORT CONFIRMATION
# ============================================================

@app.route("/transport-confirmation/<int:booking_id>")
def transport_confirmation(booking_id):

    booking = db.session.get(TransportBooking, booking_id)

    if booking is None:
        flash("Transport booking not found.")
        return redirect(url_for("transport"))

    if (
        booking.user_id is not None
        and session.get("user_id") != booking.user_id
    ):
        flash("Please log in with the account used for this booking.")
        return redirect(url_for("login"))

    extra = TransportBookingExtra.query.filter_by(
        booking_id=booking.id
    ).first()

    return render_template(
        "transport_confirmation.html",
        booking=booking,
        extra=extra
    )


# ============================================================
# MY BOOKINGS
# ============================================================

@app.route("/my-bookings")
def my_bookings():

    if "user_id" not in session:
        flash("Please log in to view your bookings.")
        return redirect(url_for("login"))

    user_id = session["user_id"]

    hotel_bookings = HotelBooking.query.filter_by(
        user_id=user_id
    ).order_by(HotelBooking.id.desc()).all()

    transport_bookings = TransportBooking.query.filter_by(
        user_id=user_id
    ).order_by(TransportBooking.id.desc()).all()

    transport_extras = {
        extra.booking_id: extra
        for extra in TransportBookingExtra.query.join(
            TransportBooking,
            TransportBookingExtra.booking_id == TransportBooking.id
        ).filter(
            TransportBooking.user_id == user_id
        ).all()
    }

    cancellation_rows = BookingCancellation.query.filter(
        db.or_(
            db.and_(
                BookingCancellation.booking_type == "hotel",
                BookingCancellation.booking_id.in_(
                    [b.id for b in hotel_bookings] or [0]
                )
            ),
            db.and_(
                BookingCancellation.booking_type == "transport",
                BookingCancellation.booking_id.in_(
                    [b.id for b in transport_bookings] or [0]
                )
            )
        )
    ).all()

    cancelled_hotels = {
        item.booking_id
        for item in cancellation_rows
        if item.booking_type == "hotel"
    }

    cancelled_transport = {
        item.booking_id
        for item in cancellation_rows
        if item.booking_type == "transport"
    }

    return render_template(
        "my_bookings.html",
        hotel_bookings=hotel_bookings,
        transport_bookings=transport_bookings,
        transport_extras=transport_extras,
        cancelled_hotels=cancelled_hotels,
        cancelled_transport=cancelled_transport
    )


# ============================================================
# CANCEL BOOKING
# ============================================================

@app.route(
    "/cancel-booking/<booking_type>/<int:booking_id>",
    methods=["POST"]
)
def cancel_booking(booking_type, booking_id):

    if "user_id" not in session:
        flash("Please log in to cancel a booking.")
        return redirect(url_for("login"))

    user_id = session["user_id"]

    if booking_type == "hotel":

        booking = HotelBooking.query.filter_by(
            id=booking_id,
            user_id=user_id
        ).first()

    elif booking_type == "transport":

        booking = TransportBooking.query.filter_by(
            id=booking_id,
            user_id=user_id
        ).first()

    else:

        flash("Invalid booking type.")
        return redirect(url_for("my_bookings"))

    if booking is None:
        flash("Booking not found.")
        return redirect(url_for("my_bookings"))

    existing = BookingCancellation.query.filter_by(
        booking_type=booking_type,
        booking_id=booking_id
    ).first()

    if existing:
        flash("This booking is already cancelled.")
        return redirect(url_for("my_bookings"))

    cancellation = BookingCancellation(
        booking_type=booking_type,
        booking_id=booking_id
    )

    db.session.add(cancellation)
    db.session.commit()

    flash(
        "Booking cancelled successfully. "
        "This is a demo cancellation."
    )

    return redirect(url_for("my_bookings"))


# ============================================================
# CREATE DATABASE TABLES
# ============================================================

with app.app_context():
    db.create_all()


# ============================================================
# RUN APPLICATION
# ============================================================

if __name__ == "__main__":
    app.run(debug=True)
