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

def get_user_medical_records(user_id):
    """Lấy tất cả thông tin bệnh án của người dùng"""
    try:
        from app.models.user import User
        user = User.query.get(user_id)
        if not user or user.role != 'patient':
            return None
            
        all_records = MedicalRecord.query.filter_by(patient_id=user_id)\
            .order_by(MedicalRecord.date.desc())\
            .all()
            
        if not all_records:
            return None
            
        records_data = []
        for record in all_records:
            record_info = {
                "date": record.date.strftime("%Y-%m-%d"),
                "hgb": record.hgb,
                "rbc": record.rbc,
                "wbc": record.wbc,
                "plt": record.plt,
                "hct": record.hct,
                "glucose": record.glucose,
                "creatinine": record.creatinine,
                "alt": record.alt,
                "cholesterol": record.cholesterol,
                "crp": record.crp
            }
            records_data.append(record_info)
            
        return records_data
    except Exception as e:
        print(f"Lỗi khi lấy thông tin bệnh án: {e}")
        return None

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

@bp.route('/ask', methods=['POST'])
@csrf.exempt
def ask_ai():
    try:
        if not request.is_json:
            return jsonify({'error': 'Yêu cầu phải ở định dạng JSON'}), 400
            
        data = request.get_json()
        if not data or 'message' not in data:
            return jsonify({'error': 'Vui lòng cung cấp tin nhắn'}), 400
        
        user_message = data['message']
        if not isinstance(user_message, str) or not user_message.strip():
            return jsonify({'error': 'Tin nhắn không hợp lệ'}), 400
        
        user_id = None
        user_name = None
        if hasattr(current_user, 'is_authenticated') and current_user.is_authenticated:
            user_id = current_user.id
            user_name = current_user.username
            
        ai_response = chat_with_gemini(user_message, user_id, user_name)
        
        if user_id:
            try:
                chat_history = ChatHistory(
                    user_id=user_id,
                    message=user_message,
                    response=ai_response,
                    timestamp=datetime.utcnow()
                )
                db.session.add(chat_history)
                db.session.commit()
            except Exception as e:
                print(f"Lỗi khi lưu lịch sử chat: {e}")
                db.session.rollback()
        
        return jsonify({
            'response': ai_response
        })
    except Exception as e:
        return jsonify({'error': f'Lỗi server: {str(e)}'}), 500

@bp.route('/history', methods=['GET'])
@login_required
def get_user_chat_history():
    try:
        history = ChatHistory.query.filter_by(user_id=current_user.id)\
            .order_by(ChatHistory.timestamp.desc())\
            .all()
            
        return jsonify({
            'history': [chat.to_dict() for chat in history]
        })
    except Exception as e:
        return jsonify({'error': f'Lỗi khi lấy lịch sử chat: {str(e)}'}), 500

@bp.route('/test', methods=['GET'])
def test_api():
    return jsonify({
        'status': 'success',
        'message': 'Chat AI API đang hoạt động bình thường'
    }) 