from flask import Flask, request, jsonify, send_from_directory
from flask import Flask, request, jsonify, send_from_directory, redirect

import os
import requests
from dotenv import load_dotenv
from datetime import datetime

# Load .env
load_dotenv()

app = Flask(__name__, static_folder='public', static_url_path='/')

# Firebase config
DB_URL = os.getenv("FIREBASE_DB_URL")
SECRET = os.getenv("FIREBASE_SECRET")
PORT = int(os.getenv("PORT", 3000))

if not DB_URL or not SECRET:
    raise Exception("❌ FIREBASE_DB_URL or FIREBASE_SECRET missing in .env")

# ---------------------
# Home Route
# ---------------------
@app.route("/")
def home():
    return redirect("/vehicle_form.html")

    

# ---------------------
# Serve static files (HTML form)
# ---------------------
@app.route('/<path:path>')
def static_file(path):
    return send_from_directory('public', path)

# ---------------------
# CNIC Validator
# ---------------------
def validate_cnic(cnic):
    return cnic.isdigit() and len(cnic) == 13

# ---------------------
# Firebase PATCH helper
# ---------------------
def firebase_patch(path, data):
    base = DB_URL.rstrip('/')
    if path:
        url = f"{base}/{path}.json?auth={SECRET}"
    else:
        url = f"{base}/.json?auth={SECRET}"   # <-- notice the "/" before .json
    resp = requests.patch(url, json=data)
    resp.raise_for_status()
    return resp.json()


# ---------------------
# Register API
# ---------------------
@app.route("/api/register", methods=["POST"])
def register():
    try:
        form = request.get_json()
        print("🔥 Form received:", form)

        cnic = form.get("cnic", "").strip()
        if not validate_cnic(cnic):
            return jsonify({"status": "error", "message": "❌ Invalid CNIC (must be 13 digits)"}), 400

        nadra_node = {
            "ownerName": form.get("ownerName"),
            "fatherName": form.get("fatherName"),
            "cnic": cnic,
            "mobile": form.get("mobile"),
            "presentAddress": form.get("presentAddress"),
            "permanentAddress": form.get("permanentAddress"),
            "email": form.get("email")
        }

        vehicle_id = form.get("chassis", "").replace(" ", "").replace("-", "") or f"v_{int(datetime.utcnow().timestamp()*1000)}"
        vehicle_node = {
            "make": form.get("make"),
            "model": form.get("model"),
            "chassis": form.get("chassis"),
            "carnumberplate": form.get("carNumberPlate"),
            "engine": form.get("engine"),
            "color": form.get("color"),
            "vehicleType": form.get("vehicleType"),
            "fuelType": form.get("fuelType"),
            "seating": form.get("seating"),
            "cc": form.get("cc"),
            "purpose": form.get("purpose"),
            "invoiceNo": form.get("invoiceNo"),
            "invoiceDate": form.get("invoiceDate"),
            "purchasePrice": form.get("purchasePrice"),
            "dealerName": form.get("dealerName"),
            "dealerInfo": form.get("dealerInfo")
        }

        full_info = {
            **nadra_node,
            "vehicle": vehicle_node,
            "taxInfo": {
                "registrationFee": form.get("registrationFee"),
                "vehicleTax": form.get("vehicleTax"),
                "tokenTax": form.get("tokenTax"),
                "smartCardFee": form.get("smartCardFee"),
                "plateFee": form.get("plateFee")
            },
            "createdAt": datetime.utcnow().isoformat()
        }

        updates = {
            f"NADRA/{cnic}": nadra_node,
            f"Excise/{cnic}": vehicle_node,
            f"FULL_INFO_USER/{cnic}": full_info
        }

        firebase_response = firebase_patch("", updates)

        return jsonify({
            "status": "success",
            "message": "✅ Record successfully stored in Firebase",
            "savedCnic": cnic,
            "vehicleId": vehicle_id,
            "firebaseResponse": firebase_response
        })

    except requests.HTTPError as e:
        print("🔥 Firebase HTTPError:", e)
        return jsonify({"status": "error", "message": f"Firebase error: {str(e)}"}), 500
    except Exception as e:
        print("🔥 Exception:", e)
        return jsonify({"status": "error", "message": f"Server error: {str(e)}"}), 500

# ---------------------
# Run server
# ---------------------
if __name__ == "__main__":
    print(f"✅ Server running → http://localhost:{PORT}")
    app.run(host="0.0.0.0", port=PORT, debug=True)
