from flask import Flask, request, jsonify, send_from_directory
import os, requests
from datetime import datetime
from dotenv import load_dotenv
load_dotenv()


# -------------------------
# Flask setup
# -------------------------
app = Flask(__name__, static_folder='public', static_url_path='/')

# -------------------------
# Firebase config (from Railway Variables)
# -------------------------
DB_URL = os.getenv("FIREBASE_DB_URL", "").rstrip("/")
SECRET = os.getenv("FIREBASE_SECRET", "")
PORT = int(os.getenv("PORT", 3000))

if not DB_URL or not SECRET:
    raise Exception("❌ Firebase credentials not found in environment variables")

print("🔥 Firebase URL:", DB_URL)
print("🔥 Firebase Secret Loaded Successfully")

# -------------------------
# Serve your HTML form
# -------------------------
@app.route("/")
def home():
    return send_from_directory("public", "vehicle_form.html")

@app.route("/<path:path>")
def static_file(path):
    return send_from_directory("public", path)

# -------------------------
# CNIC Validator
# -------------------------
def validate_cnic(cnic):
    return cnic.isdigit() and len(cnic) == 13

# -------------------------
# Firebase PATCH Helper
# -------------------------
def firebase_patch(path, data):
    url = f"{DB_URL}/{path}.json?auth={SECRET}"
    print("📡 Firebase PATCH →", url)
    resp = requests.patch(url, json=data)
    print("📡 Firebase response:", resp.status_code)
    resp.raise_for_status()
    return resp.json()

# -------------------------
# Register API
# -------------------------
@app.route("/api/register", methods=["POST"])
def register():
    try:
        form = request.get_json()
        print("🔥 Form received:", form)

        cnic = form.get("cnic", "").strip()
        if not validate_cnic(cnic):
            return jsonify({"status": "error", "message": "❌ Invalid CNIC (must be 13 digits)"}), 400

        # Prepare NADRA + Excise Data
        nadra_data = {
            "ownerName": form.get("ownerName"),
            "fatherName": form.get("fatherName"),
            "cnic": cnic,
            "mobile": form.get("mobile"),
            "presentAddress": form.get("presentAddress"),
            "permanentAddress": form.get("permanentAddress"),
            "email": form.get("email"),
            "createdAt": datetime.utcnow().isoformat()
        }

        excise_data = {
            "make": form.get("make"),
            "model": form.get("model"),
            "chassis": form.get("chassis"),
            "carNumberPlate": form.get("carNumberPlate"),
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
            "dealerInfo": form.get("dealerInfo"),
            "registrationFee": form.get("registrationFee"),
            "vehicleTax": form.get("vehicleTax"),
            "tokenTax": form.get("tokenTax"),
            "smartCardFee": form.get("smartCardFee"),
            "plateFee": form.get("plateFee"),
            "createdAt": datetime.utcnow().isoformat()
        }

        full_info = {
            **nadra_data,
            "vehicle": excise_data
        }

        # Push to Firebase
        updates = {
            f"NADRA/{cnic}": nadra_data,
            f"Excise/{cnic}": excise_data,
            f"FULL_INFO_USER/{cnic}": full_info
        }

        firebase_response = firebase_patch("", updates)

        return jsonify({
            "status": "success",
            "message": "✅ Data saved to Firebase successfully",
            "firebaseResponse": firebase_response
        })

    except requests.HTTPError as e:
        print("🔥 Firebase HTTPError:", e)
        return jsonify({"status": "error", "message": f"Firebase error: {str(e)}"}), 500
    except Exception as e:
        print("🔥 Exception:", e)
        return jsonify({"status": "error", "message": f"Server error: {str(e)}"}), 500

# -------------------------
# Run Server
# -------------------------
if __name__ == "__main__":
    print(f"✅ Server running → http://localhost:{PORT}")
    app.run(host="0.0.0.0", port=PORT, debug=True)
