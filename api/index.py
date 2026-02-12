from flask import Flask, request, jsonify
from flask_cors import CORS
import requests
import json

app = Flask(__name__)
CORS(app, resources={r"/api/*": {"origins": "*"}})

BASE_URL = "https://erp.akgec.ac.in"

def process_attendance_json(raw_data):
    """Parses raw ERP attendance JSON into a structured format."""
    std_details = raw_data.get('stdSubAtdDetails', {})
    
    return {
        "summary": std_details.get('subjects', []),
        "overall": {
            "percentage": std_details.get('overallPercentage'),
            "present": std_details.get('overallPresent'),
            "total": std_details.get('overallLecture')
        },
        "daily_logs": raw_data.get('attendanceData', []),
        "extra_lectures": raw_data.get('extraLectures', [])
    }

def get_personal_profile(auth):
    """Fetches detailed user profile using ERP headers."""
    user_id = auth.get('user_id')
    
    headers = {
        "Authorization": f"Bearer {auth.get('access_token')}",
        "x_token": auth.get('x_token'),
        "x-contextid": str(auth.get('context_id')),
        "x-userid": str(user_id),
        "sessionid": auth.get('session_id'),
        "x-rx": "1",
        "x-wb": "1",
        "x_app_year": "2025",
        "Accept": "application/json, text/plain, */*",
        "User-Agent": "Mozilla/5.0",
        "Referer": f"{BASE_URL}/attendance/stu_atdance_cal_college"
    }
    
    params = {"Id": user_id, "val": "0", "val1": "0", "val2": "0", "val3": "0"}
    
    try:
        response = requests.get(f"{BASE_URL}/api/User", headers=headers, params=params)
        return response.json() if response.status_code == 200 else None
    except:
        return None

@app.route('/api/login', methods=['POST'])
def login():
    data = request.json
    login_payload = {
        "grant_type": "password", 
        "username": data.get('username'), 
        "password": data.get('password')
    }
    
    response = requests.post(f"{BASE_URL}/Token", data=login_payload, headers={"User-Agent": "Mozilla/5.0"})
    
    if response.status_code == 200:
        res_data = response.json()
        return jsonify({
            "status": "success",
            "access_token": res_data.get("access_token"),
            "user_id": res_data.get("X-UserId"),
            "context_id": res_data.get("X-ContextId"),
            "x_token": res_data.get("X_Token"),
            "session_id": res_data.get("SessionId")
        }), 200
    return jsonify({"error": "Invalid ERP credentials"}), 401

@app.route('/api/dashboard', methods=['POST'])
def get_full_data():
    """Fetches both attendance and personal profile in one go."""
    auth = request.json
    
    # Setup headers for attendance
    headers = {
        "Authorization": f"Bearer {auth.get('access_token')}",
        "x_token": auth.get('x_token'),
        "x-contextid": str(auth.get('context_id')),
        "x-userid": str(auth.get('user_id')),
        "sessionid": auth.get('session_id'),
        "x-rx": "1", "x-wb": "1", "x_app_year": "2025",
        "User-Agent": "Mozilla/5.0",
        "Accept": "application/json"
    }
    
    # 1. Fetch Attendance
    params = {"isDateWise": "false", "termId": "0", "userId": auth.get('user_id'), "y": "0"}
    atd_resp = requests.get(f"{BASE_URL}/api/SubjectAttendance/GetPresentAbsentStudent", headers=headers, params=params)
    
    # 2. Fetch Profile (using our helper function)
    profile_data = get_personal_profile(auth)

    if atd_resp.status_code == 200:
        attendance_formatted = process_attendance_json(atd_resp.json())
        
        # Merge both into one response
        return jsonify({
            "attendance": attendance_formatted,
            "profile": profile_data
        }), 200
        
    return jsonify({"error": "Failed to fetch dashboard data"}), 500

if __name__ == '__main__':
    app.run(debug=True, port=5000)