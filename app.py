from flask import Flask, request, jsonify, send_from_directory
from uuid import uuid4
from datetime import datetime
import re
import logging
from dateutil import parser
from dateutil.relativedelta import relativedelta
from flask_cors import CORS

app = Flask(__name__, template_folder='.')
CORS(app)
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("travel_booking_controller")

PACKAGES = {
    "pkg1": {
        "id": "pkg1",
        "name": "Amsterdam & Paris Classic",
        "leaving_from": "Mumbai",
        "destination": "Amsterdam & Paris",
        "duration": 6,
        "itinerary": "Amsterdam 2N, Paris 3N",
        "description": "Embark on an unforgettable 6-day journey through two of Europe's most enchanting cities—Amsterdam and Paris. Begin your adventure in Amsterdam, where you'll explore the city's iconic canals on a scenic glass-roof cruise, wander through the historic Dam Square, and visit the vibrant Keukenhof Gardens (seasonal) or the charming miniature park of Madurodam.",
        "inclusions": ["Hotel", "Breakfast", "Transfers", "Eiffel Tower Entry", "Seine River Cruise"],
        "hotels": [
            {"name": "Park Plaza Amsterdam Airport or Similar", "rating": 4, "nights": 2, "city": "Amsterdam"},
            {"name": "The Jangle Hotel – Paris – Charles de Gaulle Airport or Similar", "rating": 4, "nights": 3, "city": "Paris"}
        ],
        "departure_dates": [
            {"date": "2026-04-08", "price_per_person": 175540, "available": True, "return_date": "2026-04-13"},
            {"date": "2026-04-15", "price_per_person": 175540, "available": True, "return_date": "2026-04-20"},
            {"date": "2026-04-22", "price_per_person": 175540, "available": True, "return_date": "2026-04-27"},
            {"date": "2026-05-06", "price_per_person": 182340, "available": True, "return_date": "2026-05-11"},
            {"date": "2026-05-13", "price_per_person": 182340, "available": True, "return_date": "2026-05-18"},
            {"date": "2026-06-03", "price_per_person": 189750, "available": True, "return_date": "2026-06-08"}
        ]
    },
    "pkg2": {
        "id": "pkg2",
        "name": "Himalayan Escape",
        "leaving_from": "Delhi",
        "destination": "Manali",
        "duration": 4,
        "itinerary": "Day 1: Drive; Day 2: Snow Activities; Day 3: Local Tour; Day 4: Return",
        "description": "Experience the beauty of the Himalayas with this 4-day escape to Manali.",
        "inclusions": ["Hotel", "Breakfast", "Guide"],
        "hotels": [{"name": "Mountain Lodge", "rating": 3, "nights": 3, "city": "Manali"}],
        "departure_dates": [
            {"date": "2026-04-12", "price_per_person": 45000, "available": True, "return_date": "2026-04-16"},
            {"date": "2026-05-10", "price_per_person": 47000, "available": True, "return_date": "2026-05-14"}
        ]
    }
}

PROMO_DB = {
    "WELCOME1000": {"amount": 1000, "type": "fixed"},
    "SUMMER500": {"amount": 500, "type": "fixed"}
}

ENQUIRIES = {}
BOOKINGS = {}

EMAIL_REGEX = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
PHONE_REGEX = re.compile(r"^\d{10}$")

REQUIRED_STEP_SEQUENCE = ["Trip Details", "Date Selection", "Price Summary", "Traveller Details"]

def parse_room_config(room_config_str):
    if not room_config_str:
        raise ValueError("room_config is required")
    tokens = re.split(r"[,;|]", room_config_str)
    rooms = []
    total_adults = 0
    traveller_entities = []
    for token in tokens:
        token = token.strip()
        if not token:
            continue
        parts = token.split("-")
        if len(parts) < 2:
            raise ValueError(f"Invalid room config token: {token}")
        try:
            rooms_count = int(parts[0])
            adults_per_room = int(parts[1])
            children_per_room = int(parts[2]) if len(parts) > 2 else 0
        except Exception:
            raise ValueError(f"Invalid numbers in room config token: {token}")
        for _ in range(rooms_count):
            rooms.append({"adults": adults_per_room, "children": children_per_room})
            total_adults += adults_per_room
            if adults_per_room > 0:
                for _ in range(adults_per_room):
                    traveller_entities.append({"type": "Adult"})
            if children_per_room > 0:
                for _ in range(children_per_room):
                    traveller_entities.append({"type": "Child"})
    return {"rooms": rooms, "total_adults": total_adults, "traveller_entities": traveller_entities}

def find_package_by_filters(filters):
    leaving_from = filters.get("Leaving From").strip().lower()
    destination = filters.get("Destination").strip().lower()
    leaving_on = filters.get("Leaving On")
    duration = filters.get("Duration")
    traveller_count = filters.get("Traveller Count")
    results = []
    for pkg in PACKAGES.values():
        try:
            if leaving_from and leaving_from not in pkg.get("leaving_from", "").lower():
                continue
            if destination and destination.lower() not in pkg.get("destination", "").lower():
                continue
            if duration and str(pkg.get("duration")) != str(duration):
                continue
            if leaving_on:
                try:
                    leaving_on_date = parser.parse(leaving_on).date()
                except Exception:
                    continue
                match = False
                for d in pkg.get("departure_dates", []):
                    try:
                        ddate = parser.parse(d["date"]).date()
                    except Exception:
                        continue
                    if ddate == leaving_on_date:
                        match = True
                        break
                if not match:
                    continue
            if traveller_count:
                pass
            results.append({"id": pkg["id"], "name": pkg["name"], "destination": pkg["destination"], "leaving_from": pkg["leaving_from"], "duration": pkg["duration"], "itinerary": pkg.get("itinerary", ""),"departure_dates": pkg.get("departure_dates", [])})
        except Exception as e:
            logger.exception("Error filtering package")
    return results

def get_package(pkg_id):
    return PACKAGES.get(pkg_id)

def get_available_dates_for_package(pkg_id, selected_month):
    pkg = get_package(pkg_id)
    if not pkg:
        raise ValueError("Package not found")
    results = []
    for d in pkg.get("departure_dates", []):
        try:
            ddate = parser.parse(d["date"]).date()
            month_str = ddate.strftime("%Y-%m")
            if selected_month:
                try:
                    selected_dt = parser.parse(selected_month + "-01").date()
                    selected_month_str = selected_dt.strftime("%Y-%m")
                except Exception:
                    selected_month_str = selected_month
                if month_str != selected_month_str:
                    continue
            results.append({"date": d["date"], "return_date": d.get("return_date", ""), "price_per_person": d["price_per_person"], "available": d["available"]})
        except Exception:
            logger.exception("Error parsing date")
    return results

def calculate_price_breakdown(pkg_id, departure_date, room_config_str):
    pkg = get_package(pkg_id)
    if not pkg:
        raise ValueError("Package not found")
    dep = None
    for d in pkg.get("departure_dates", []):
        if d.get("date") == departure_date:
            dep = d
            break
    if not dep:
        raise ValueError("Departure date not found")
    if not dep.get("available"):
        raise ValueError("Selected departure date is not available")
    parsed = parse_room_config(room_config_str)
    price_per_person = dep.get("price_per_person")
    subtotal = price_per_person * parsed["total_adults"]
    tcs = round(subtotal * 0.05)
    total = subtotal + tcs
    return {"price_per_person": price_per_person, "total_adults": parsed["total_adults"], "subtotal": subtotal, "tcs": tcs, "total": total, "traveller_entities": parsed["traveller_entities"]}

def apply_promo_code(code, current_total):
    if not code:
        return {"error": "Promo code is required"}
    promo = PROMO_DB.get(code)
    if not promo:
        return {"error": "Invalid promo code"}
    amount = promo.get("amount", 0)
    new_total = current_total - amount
    if new_total < 0:
        new_total = 0
    return {"new_total": new_total, "discount_applied": amount}

def validate_contact_info(contact):
    email = contact.get("email")
    phone = contact.get("phone")
    city = contact.get("city")
    if not email or not EMAIL_REGEX.match(email):
        raise ValueError("Invalid email")
    if not phone or not PHONE_REGEX.match(phone):
        raise ValueError("Invalid phone")
    if not city:
        raise ValueError("City is required")
    return True

def validate_gst(gst_enabled, gst_number, company_name):
    if gst_enabled:
        if not gst_number or not company_name:
            raise ValueError("GST Number and Company Name are required when GST is enabled")
    return True

def validate_passport_ack(passport_ack):
    if not isinstance(passport_ack, bool) or not passport_ack:
        raise ValueError("Passport validity acknowledgement is required")
    return True

def validate_step_sequence(steps_list):
    if not isinstance(steps_list, list):
        raise ValueError("steps_list must be a list")
    last_index = -1
    for required in REQUIRED_STEP_SEQUENCE:
        try:
            idx = steps_list.index(required)
        except ValueError:
            raise ValueError(f"Required step missing: {required}")
        if idx <= last_index:
            raise ValueError("Steps are not in required order")
        last_index = idx
    return True

@app.route('/')
def serve_index():
    return send_from_directory('.', 'index.html')

@app.route('/<path:path>')
def serve_static(path):
    return send_from_directory('.', path)

@app.route('/search_packages', methods=['POST'])
def search_packages_endpoint():
    try:
        filters = request.json or {}
        results = find_package_by_filters(filters)
        return jsonify({"status": "success", "data": results}), 200
    except Exception as e:
        logger.exception("search_packages error")
        return jsonify({"status": "error", "message": str(e)}), 400

@app.route('/get_package_details/<pkg_id>', methods=['GET'])
def get_package_details(pkg_id):
    try:
        pkg = get_package(pkg_id)
        if not pkg:
            return jsonify({"status": "error", "message": "Package not found"}), 404
        details = {"id": pkg["id"], "name": pkg["name"], "itinerary": pkg["itinerary"], "description": pkg.get("description", ""), "inclusions": pkg["inclusions"], "hotels": pkg["hotels"], "duration": pkg["duration"]}
        return jsonify({"status": "success", "data": details}), 200
    except Exception as e:
        logger.exception("get_package_details error")
        return jsonify({"status": "error", "message": str(e)}), 400

@app.route('/get_available_dates/<pkg_id>', methods=['GET'])
def get_available_dates_endpoint(pkg_id):
    try:
        selected_month = request.args.get('selected_month')
        dates = get_available_dates_for_package(pkg_id, selected_month)
        return jsonify({"status": "success", "data": dates}), 200
    except Exception as e:
        logger.exception("get_available_dates error")
        return jsonify({"status": "error", "message": str(e)}), 400

@app.route('/calculate_quote', methods=['POST'])
def calculate_quote_endpoint():
    try:
        payload = request.json or {}
        pkg_id = payload.get('package_id')
        departure_date = payload.get('departure_date')
        room_config = payload.get('room_config')
        if not pkg_id or not departure_date or not room_config:
            return jsonify({"status": "error", "message": "package_id, departure_date and room_config are required"}), 400
        quote = calculate_price_breakdown(pkg_id, departure_date, room_config)
        return jsonify({"status": "success", "data": quote}), 200
    except Exception as e:
        logger.exception("calculate_quote error")
        return jsonify({"status": "error", "message": str(e)}), 400

@app.route('/apply_promo', methods=['POST'])
def apply_promo_endpoint():
    try:
        payload = request.json or {}
        code = payload.get('code')
        current_total = payload.get('current_total')
        if current_total is None:
            return jsonify({"status": "error", "message": "current_total is required"}), 400
        result = apply_promo_code(code, current_total)
        if result.get('error'):
            return jsonify({"status": "error", "message": result.get('error')}), 400
        return jsonify({"status": "success", "data": result}), 200
    except Exception as e:
        logger.exception("apply_promo error")
        return jsonify({"status": "error", "message": str(e)}), 400

@app.route('/submit_enquiry', methods=['POST'])
def submit_enquiry_endpoint():
    try:
        payload = request.json or {}
        contact = payload.get('contact_details') or {}
        package_id = payload.get('package_id')
        try:
            validate_contact_info(contact)
        except Exception as ve:
            return jsonify({"status": "error", "message": str(ve)}), 400
        if not package_id or not get_package(package_id):
            return jsonify({"status": "error", "message": "Valid package_id is required"}), 400
        ref = str(uuid4())
        ENQUIRIES[ref] = {"ref": ref, "contact": contact, "package_id": package_id, "created_at": datetime.utcnow().isoformat()}
        return jsonify({"status": "success", "ref": ref}), 200
    except Exception as e:
        logger.exception("submit_enquiry error")
        return jsonify({"status": "error", "message": str(e)}), 400

@app.route('/confirm_booking', methods=['POST'])
def confirm_booking_endpoint():
    try:
        payload = request.json or {}
        package_id = payload.get('package_id')
        departure_date = payload.get('departure_date')
        room_config = payload.get('room_config')
        travellers = payload.get('travellers') or []
        contact = payload.get('contact') or {}
        passport_ack = payload.get('passport_ack')
        gst_enabled = payload.get('gst_enabled', False)
        gst_number = payload.get('gst_number')
        company_name = payload.get('company_name')
        steps_completed = payload.get('steps_completed') or []
        promo_code = payload.get('promo_code')
        if not package_id or not departure_date or not room_config:
            return jsonify({"status": "error", "message": "package_id, departure_date and room_config are required"}), 400
        try:
            validate_step_sequence(steps_completed)
            validate_passport_ack(passport_ack)
            validate_contact_info(contact)
            validate_gst(gst_enabled, gst_number, company_name)
        except Exception as ve:
            return jsonify({"status": "error", "message": str(ve)}), 400
        try:
            quote = calculate_price_breakdown(package_id, departure_date, room_config)
        except Exception as ve:
            return jsonify({"status": "error", "message": str(ve)}), 400
        required_travellers = quote.get('total_adults')
        if len(travellers) != required_travellers:
            return jsonify({"status": "error", "message": f"Traveller count mismatch. Expected {required_travellers}"}), 400
        for t in travellers:
            if not t.get('title') or not t.get('first_name') or not t.get('last_name'):
                return jsonify({"status": "error", "message": "Each traveller must have title, first_name, last_name"}), 400
        total = quote.get('total')
        discount_applied = 0
        if promo_code:
            promo_result = apply_promo_code(promo_code, total)
            if promo_result.get('error'):
                return jsonify({"status": "error", "message": promo_result.get('error')}), 400
            discount_applied = promo_result.get('discount_applied', 0)
            total = promo_result.get('new_total')
        booking_ref = str(uuid4())
        BOOKINGS[booking_ref] = {
            "booking_ref": booking_ref,
            "package_id": package_id,
            "departure_date": departure_date,
            "room_config": room_config,
            "travellers": travellers,
            "contact": contact,
            "gst_enabled": gst_enabled,
            "gst_number": gst_number,
            "company_name": company_name,
            "subtotal": quote.get('subtotal'),
            "tcs": quote.get('tcs'),
            "discount_applied": discount_applied,
            "total": total,
            "created_at": datetime.utcnow().isoformat()
        }
        return jsonify({"status": "success", "booking_ref": booking_ref, "total": total}), 200
    except Exception as e:
        logger.exception("confirm_booking error")
        return jsonify({"status": "error", "message": str(e)}), 400

if __name__ == '__main__':
    import os
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)
