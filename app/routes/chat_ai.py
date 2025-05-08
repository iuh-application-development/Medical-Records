from flask import Blueprint, jsonify, request
import requests
import json
from flask_login import login_required, current_user
from app import csrf, db
from app.models.chat_history import ChatHistory
from app.models.medical_record import MedicalRecord
from datetime import datetime

bp = Blueprint('chat_ai', __name__)

API_KEY = "AIzaSyAOBTEy3kA3ZITeOkEZHAUQgL_ab91pMrA"
URL = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key={API_KEY}"


def chat_with_gemini(user_input, user_id=None, user_name=None):
    headers = {
        "Content-Type": "application/json"
    }
    
    prompt = user_input
    
    if user_id and user_name:
        user_context = f"Người dùng hiện tại: {user_name}\n\n"
        
        medical_records = get_user_medical_records(user_id)
        if medical_records:
            user_context += f"Thông tin bệnh án (tổng số {len(medical_records)} bản ghi):\n"
            
            if len(medical_records) > 1:
                user_context += "\nXu hướng các chỉ số theo thời gian:\n"
                
                first_record = medical_records[-1]  
                latest_record = medical_records[0]  
                
                key_metrics = ['hgb', 'rbc', 'wbc', 'plt', 'glucose', 'cholesterol']
                for metric in key_metrics:
                    if first_record.get(metric) is not None and latest_record.get(metric) is not None:
                        old_value = float(first_record[metric])
                        new_value = float(latest_record[metric])
                        change = new_value - old_value
                        change_percent = (change / old_value) * 100 if old_value != 0 else 0
                        
                        if abs(change_percent) > 5:  
                            direction = "tăng" if change > 0 else "giảm"
                            user_context += f"- {metric}: {direction} {abs(change_percent):.1f}% từ {old_value} đến {new_value} (từ {first_record['date']} đến {latest_record['date']})\n"
            
            for i, record in enumerate(medical_records[:3]):
                user_context += f"\nBản ghi {i+1} (Ngày {record['date']}):\n"
                for key, value in record.items():
                    if key != 'date' and value is not None:
                        user_context += f"- {key}: {value}\n"
            
            if len(medical_records) > 3:
                user_context += f"\n(Còn {len(medical_records) - 3} bản ghi khác không hiển thị chi tiết)\n"
        
        system_prompt = (
            "Bạn là trợ lý AI y tế của hệ thống Medical Records Management. "
            "Dưới đây là thông tin đầy đủ về người dùng và toàn bộ lịch sử bệnh án (nếu có). "
            "Sử dụng thông tin này để phân tích và đưa ra câu trả lời chuyên sâu, nhưng KHÔNG được nhắc lại các giá trị cụ thể. "
            "Nếu người dùng hỏi về xu hướng sức khỏe hoặc thay đổi trong các chỉ số, hãy sử dụng dữ liệu xu hướng đã cung cấp. "
            f"{user_context}\n\n"
            "Dựa trên thông tin đầy đủ trên, hãy trả lời câu hỏi sau đây: "
        )
        prompt = system_prompt + user_input
    
    data = {
        "contents": [
            {
                "parts": [
                    {"text": prompt}
                ]
            }
        ]
    }

    try:
        response = requests.post(URL, headers=headers, data=json.dumps(data))
        response.raise_for_status()
        
        if response.status_code == 200:
            res_json = response.json()
            try:
                return res_json['candidates'][0]['content']['parts'][0]['text']
            except (KeyError, IndexError):
                return "Không thể trích xuất nội dung từ phản hồi."
        else:
            return f"Lỗi {response.status_code}: {response.text}"
    except Exception as e:
        return f"Lỗi: {str(e)}"

