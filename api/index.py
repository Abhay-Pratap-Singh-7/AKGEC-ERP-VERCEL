from flask import Flask, request, jsonify
from flask_cors import CORS
import requests
import json

app = Flask(__name__)
# Enabling CORS so your frontend can actually talk to this API
CORS(app)

BASE_URL = "https://erp.akgec.ac.in"

def process_attendance_json(raw_data):
    std_details = raw_data.get('stdSubAtdDetails', {})
    summary = std_details.get('subjects', [])
    overall = {
        "percentage": std_details.get('overallPercentage'),
        "present": std_details.get('overallPresent'),
        "total": std_details.get('overallLecture')
    }
    daily_logs = raw_data.get('attendanceData', [])
    extra_lectures = raw_data.get('extraLectures', [])
    profile = {}
    student_info_list = std_details.get('studentSubjectAttendance', [])
    
    if student_info_list:
        student_obj = student_info_list[0]
        profile['firstName'] = student_obj.get('firstName')
        user_details_str = student_obj.get('userDetails', '{}')
        try:
            u_details = json.loads(user_details_str)
            profile.update({
                "dob": u_details.get('dob'),
                "bloodGroup": u_details.get('bloodGroup'),
                "jeeRank": u_details.get('jeeRank'),
                "tenthPercentage": u_details.get('highSchoolPercentage'),
                "twelfthPercentage": u_details.get('intermediatePercentage'),
                "bankName": u_details.get('bankName'),
                "ifscCode": u_details.get('ifscCode'),
                "fatherName": u_details.get('fatherName'),
                "mobileNo": u_details.get('mobileNo')
            })
        except:
            pass

    return {
        "summary": summary,
        "overall": overall,
        "daily_logs": daily_logs,
        "extra_lectures": extra_lectures,
        "profile": profile
    }

@app.route('/api/login', methods=['POST'])
def login():
    data = request.json
    username = data.get('username')
    password = data.get('password')
    
    login_payload = {"grant_type": "password", "username": username, "password": password}
    headers = {"User-Agent": "Mozilla/5.0"}
    
    try:
        response = requests.post(f"{BASE_URL}/Token", data=login_payload, headers=headers, timeout=10)
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
    except Exception as e:
        return jsonify({"error": str(e)}), 500
        
    return jsonify({"error": "Invalid ERP credentials"}), 401

@app.route('/api/attendance', methods=['POST'])
def get_attendance():
    auth = request.json
    headers = {
        "Authorization": f"Bearer {auth.get('access_token')}",
        "x_token": auth.get('x_token'),
        "x-contextid": str(auth.get('context_id')),
        "x-userid": str(auth.get('user_id')),
        "sessionid": auth.get('session_id'),
        "x-rx": "1",
        "x-wb": "1",
        "x_app_year": "2025",
        "User-Agent": "Mozilla/5.0",
        "Accept": "application/json"
    }
    params = {"isDateWise": "false", "termId": "0", "userId": auth.get('user_id'), "y": "0"}
    
    try:
        response = requests.get(f"{BASE_URL}/api/SubjectAttendance/GetPresentAbsentStudent", headers=headers, params=params, timeout=15)
        if response.status_code == 200:
            formatted_data = process_attendance_json(response.json())
            return jsonify(formatted_data), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

    return jsonify({"error": "Failed to fetch data"}), 500

# This is the "magic" line for Vercel
# It exports the Flask app as the entry point
app = app