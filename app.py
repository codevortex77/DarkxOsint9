from flask import Flask, request, jsonify
import requests
import re
import time
import os
from functools import wraps
from bs4 import BeautifulSoup
import json

app = Flask(__name__)

# API Key configuration
VALID_API_KEY = "1month"

def require_api_key(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        api_key = request.args.get('key')
        if not api_key or api_key != VALID_API_KEY:
            return jsonify({
                "success": False, 
                "error": "Invalid or missing API key",
                "owner": "@PurelyYour | Buy Instantly at the Best Price"
            }), 401
        return f(*args, **kwargs)
    return decorated_function

SMC_HOMEPAGE = "https://www.smcinsurance.com/"
SMC_API = "https://www.smcinsurance.com/central/centralcall/CallReqWithHeader"

def get_vehicle_details_from_smc(vehicle_number):
    """Fast SMC API call - this is the reliable method"""
    try:
        session = requests.Session()
        # Get homepage to set cookie
        home = session.get(SMC_HOMEPAGE, timeout=8)
        mcbc_cookie = session.cookies.get("MCBC")
        
        if not mcbc_cookie:
            return {"success": False, "error": "MCBC cookie not found"}
        
        payload = {
            "url": "GetVaahanDetailsByVehicleNo",
            "props": [vehicle_number, "", "0"]
        }
        
        headers = {
            "Content-Type": "application/json",
            "User-Agent": "okhttp/4.9.2",
            "Cookie": f"MCBC={mcbc_cookie}"
        }
        
        response = session.post(SMC_API, headers=headers, json=payload, timeout=10)
        data = response.json()
        
        if data.get("statusCode") == 200:
            vehicle_data = data.get("response", {})
            chassis = vehicle_data.get("chassis", "").replace(" ", "")
            mobile_no = vehicle_data.get("mobile_no", "")
            
            # Try to get mobile from vehicle data directly
            if mobile_no and len(mobile_no) == 10:
                vehicle_data["mobile_no"] = mobile_no
                return {"success": True, "vehicle_data": vehicle_data}
            
            # If no mobile, try to fetch from Vahan (faster method)
            if len(chassis) >= 5:
                mobile_result = fetch_mobile_fast(vehicle_number, chassis[-5:])
                if mobile_result.get("success"):
                    vehicle_data["mobile_no"] = mobile_result.get("mobile_number")
                    return {"success": True, "vehicle_data": vehicle_data}
            
            return {"success": True, "vehicle_data": vehicle_data}
        
        return {"success": False, "error": "SMC API failed"}
        
    except Exception as e:
        return {"success": False, "error": str(e)}

def fetch_mobile_fast(vehicle_number, chassis_last_5):
    """Simplified faster mobile number fetch"""
    try:
        session = requests.Session()
        session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
        
        # Direct API attempt (if available)
        # This is a placeholder - you might have a faster endpoint
        
        # For now, return None to use SMC mobile if available
        return {"success": False}
        
    except Exception:
        return {"success": False}

@app.route("/", methods=["GET"])
def home():
    return jsonify({
        "success": True,
        "message": "Vehicle Details API",
        "endpoint": "/vehicle?key=1month&reg=VEHICLE_NUMBER",
        "example": "/vehicle?key=1month&reg=KA01AB1234",
        "owner": "@PurelyYour | Buy Instantly at the Best Price"
    })

@app.route("/vehicle", methods=["GET"])
@require_api_key
def fetch_contact():
    vehicle_number = request.args.get("reg", "").strip().upper()
    vehicle_number = re.sub(r'[^A-Z0-9]', '', vehicle_number)
    
    if not vehicle_number or len(vehicle_number) < 6:
        return jsonify({
            "success": False, 
            "error": "Invalid vehicle number",
            "owner": "@PurelyYour | Buy Instantly at the Best Price"
        }), 400
    
    # Try SMC API first (faster)
    result = get_vehicle_details_from_smc(vehicle_number)
    
    if result.get("success"):
        return jsonify({
            "statusCode": 200,
            "response": result["vehicle_data"],
            "owner": "@PurelyYour | Buy Instantly at the Best Price"
        })
    else:
        return jsonify({
            "success": False,
            "error": result.get("error", "Failed to fetch details"),
            "owner": "@PurelyYour | Buy Instantly at the Best Price"
        }), 400

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
