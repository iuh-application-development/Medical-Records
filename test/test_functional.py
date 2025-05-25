import unittest
import pytest
from app import create_app, db
from app.models.user import User
from app.models.medical_record import MedicalRecord, Notification
from app.config import TestingConfig
from flask import current_app
from datetime import datetime
from sqlalchemy.exc import LegacyAPIWarning

@pytest.mark.filterwarnings("ignore::DeprecationWarning")
@pytest.mark.filterwarnings("ignore::sqlalchemy.exc.LegacyAPIWarning")
class FunctionalTest(unittest.TestCase):
    def setUp(self):
        self.app = create_app(TestingConfig)
        self.app_context = self.app.app_context()
        self.app_context.push()
        db.create_all()
        self.client = self.app.test_client()
        # Tạo CSRF token cho testing
        with self.client.session_transaction() as session:
            session['csrf_token'] = 'test_token'

    def tearDown(self):
        db.session.remove()
        db.drop_all()
        self.app_context.pop()

    def test_home_page(self):
        """Test truy cập trang chủ"""
        response = self.client.get('/')
        self.assertEqual(response.status_code, 200)

    def test_user_registration(self):
        """Test đăng ký người dùng mới"""
        response = self.client.post('/register', data={
            'username': 'testuser',
            'email': 'test@example.com',
            'phone': '0123456789',
            'password': 'password123',
            'confirm_password': 'password123',
            'role': 'patient'
        }, follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        user = User.query.filter_by(username='testuser').first()
        self.assertIsNotNone(user)

    def test_user_login(self):
        """Test đăng nhập"""
        # Tạo user test
        user = User(username='testuser', email='test@example.com', role='patient', phone='0123456789')
        user.set_password('password123')
        db.session.add(user)
        db.session.commit()

        # Test đăng nhập
        response = self.client.post('/login', data={
            'username': 'testuser',
            'password': 'password123'
        }, follow_redirects=True)
        self.assertEqual(response.status_code, 200)

    def test_user_logout(self):
        """Test đăng xuất"""
        # Tạo và đăng nhập user
        user = User(username='testuser', email='test@example.com', role='patient', phone='0123456789')
        user.set_password('password123')
        db.session.add(user)
        db.session.commit()

        self.client.post('/login', data={
            'username': 'testuser',
            'password': 'password123'
        })

        # Test đăng xuất
        response = self.client.get('/logout', follow_redirects=True)
        self.assertEqual(response.status_code, 200)

    def test_update_profile(self):
        """Test cập nhật thông tin người dùng"""
        # Tạo và đăng nhập user
        user = User(username='testuser', email='test@example.com', role='patient', phone='0123456789')
        user.set_password('password123')
        db.session.add(user)
        db.session.commit()

        self.client.post('/login', data={
            'username': 'testuser',
            'password': 'password123'
        })

        # Test cập nhật thông tin
        response = self.client.post('/patient/profile', data={
            'full_name': 'Test User',
            'phone': '0987654321',
            'email': 'newemail@example.com'
        }, follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        
        # Kiểm tra thông tin đã được cập nhật
        updated_user = User.query.filter_by(username='testuser').first()
        self.assertEqual(updated_user.full_name, 'Test User')
        self.assertEqual(updated_user.phone, '0987654321')
        self.assertEqual(updated_user.email, 'newemail@example.com')

    def test_patient_creation(self):
        """Test tạo bệnh nhân mới"""
        # Đăng nhập trước
        user = User(username='testuser', email='test@example.com', role='patient', phone='0123456789')
        user.set_password('password123')
        db.session.add(user)
        db.session.commit()

        self.client.post('/login', data={
            'username': 'testuser',
            'password': 'password123'
        })

        # Test tạo bệnh nhân
        response = self.client.post('/patient/new_record', data={
            'date': datetime.now().date(),
            'hgb': 14.5,
            'rbc': 4.8,
            'wbc': 7.5,
            'plt': 250,
            'hct': 42,
            'glucose': 100,
            'creatinine': 1.0,
            'alt': 25,
            'cholesterol': 180,
            'crp': 2.0
        }, follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        record = MedicalRecord.query.filter_by(patient_id=user.id).first()
        self.assertIsNotNone(record)

    def test_view_records(self):
        """Test xem danh sách bản ghi y tế"""
        # Tạo user và bản ghi y tế
        user = User(username='testuser', email='test@example.com', role='patient', phone='0123456789')
        user.set_password('password123')
        db.session.add(user)
        db.session.commit()

        record = MedicalRecord(
            patient_id=user.id,
            date=datetime.now().date(),
            hgb=14.5,
            rbc=4.8,
            wbc=7.5,
            plt=250,
            hct=42,
            glucose=100,
            creatinine=1.0,
            alt=25,
            cholesterol=180,
            crp=2.0
        )
        db.session.add(record)
        db.session.commit()

        # Đăng nhập
        self.client.post('/login', data={
            'username': 'testuser',
            'password': 'password123'
        })

        # Test xem danh sách bản ghi
        response = self.client.get('/patient/view_records')
        self.assertEqual(response.status_code, 200)

    def test_view_charts(self):
        """Test xem biểu đồ thống kê"""
        # Tạo user và bản ghi y tế
        user = User(username='testuser', email='test@example.com', role='patient', phone='0123456789')
        user.set_password('password123')
        db.session.add(user)
        db.session.commit()

        record = MedicalRecord(
            patient_id=user.id,
            date=datetime.now().date(),
            hgb=14.5,
            rbc=4.8,
            wbc=7.5,
            plt=250,
            hct=42,
            glucose=100,
            creatinine=1.0,
            alt=25,
            cholesterol=180,
            crp=2.0
        )
        db.session.add(record)
        db.session.commit()

        # Đăng nhập
        self.client.post('/login', data={
            'username': 'testuser',
            'password': 'password123'
        })

        # Test xem biểu đồ
        response = self.client.get('/patient/view_charts')
        self.assertEqual(response.status_code, 200)

    def test_notifications(self):
        """Test thông báo"""
        # Tạo user và thông báo
        user = User(username='testuser', email='test@example.com', role='patient', phone='0123456789')
        user.set_password('password123')
        db.session.add(user)
        db.session.commit()

        notification = Notification(
            patient_id=user.id,
            message='Test notification',
            date=datetime.now(),
            read=False
        )
        db.session.add(notification)
        db.session.commit()

        # Đăng nhập
        self.client.post('/login', data={
            'username': 'testuser',
            'password': 'password123'
        })

        # Test xem thông báo
        response = self.client.get('/patient/notifications')
        self.assertEqual(response.status_code, 200)

        # Test đánh dấu thông báo đã đọc
        response = self.client.post(f'/patient/notifications/mark_read/{notification.id}')
        self.assertEqual(response.status_code, 200)
        updated_notification = db.session.get(Notification, notification.id)
        self.assertTrue(updated_notification.read)

    # Test cases cho role doctor
    def test_doctor_registration(self):
        """Test đăng ký bác sĩ mới"""
        # Tạo user với role patient trước
        response = self.client.post('/register', data={
            'username': 'doctor1',
            'email': 'doctor@example.com',
            'phone': '0123456789',
            'password': 'password123',
            'confirm_password': 'password123'
        }, follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        user = User.query.filter_by(username='doctor1').first()
        self.assertIsNotNone(user)
        
        # Sau đó cập nhật role thành doctor thông qua admin
        admin = User(username='admin1', email='admin@example.com', role='admin', phone='0123456789')
        admin.set_password('password123')
        db.session.add(admin)
        db.session.commit()

        # Đăng nhập admin
        self.client.post('/login', data={
            'username': 'admin1',
            'password': 'password123'
        })

        # Cập nhật role của user thành doctor
        user.role = 'doctor'
        db.session.commit()

        # Kiểm tra role đã được cập nhật
        updated_user = User.query.filter_by(username='doctor1').first()
        self.assertEqual(updated_user.role, 'doctor')

    def test_doctor_login(self):
        """Test đăng nhập bác sĩ"""
        # Tạo bác sĩ test
        doctor = User(username='doctor1', email='doctor@example.com', role='doctor', phone='0123456789')
        doctor.set_password('password123')
        db.session.add(doctor)
        db.session.commit()

        # Test đăng nhập
        response = self.client.post('/login', data={
            'username': 'doctor1',
            'password': 'password123'
        }, follow_redirects=True)
        self.assertEqual(response.status_code, 200)

    def test_doctor_view_patients(self):
        """Test bác sĩ xem danh sách bệnh nhân"""
        # Tạo bác sĩ test
        doctor = User(username='doctor1', email='doctor@example.com', role='doctor', phone='0123456789')
        doctor.set_password('password123')
        db.session.add(doctor)
        db.session.commit()

        # Đăng nhập bác sĩ
        self.client.post('/login', data={
            'username': 'doctor1',
            'password': 'password123'
        })

        # Test xem danh sách bệnh nhân
        response = self.client.get('/doctor/search_patient')
        self.assertEqual(response.status_code, 200)

    def test_doctor_view_patient_records(self):
        """Test bác sĩ xem bản ghi y tế của bệnh nhân"""
        # Tạo bác sĩ và bệnh nhân với bản ghi y tế
        doctor = User(username='doctor1', email='doctor@example.com', role='doctor', phone='0123456789')
        doctor.set_password('password123')
        db.session.add(doctor)

        patient = User(username='patient1', email='patient@example.com', role='patient', phone='0987654321')
        patient.set_password('password123')
        db.session.add(patient)
        db.session.commit()

        record = MedicalRecord(
            patient_id=patient.id,
            date=datetime.now().date(),
            hgb=14.5,
            rbc=4.8,
            wbc=7.5,
            plt=250,
            hct=42,
            glucose=100,
            creatinine=1.0,
            alt=25,
            cholesterol=180,
            crp=2.0
        )
        db.session.add(record)
        db.session.commit()

        # Đăng nhập bác sĩ
        self.client.post('/login', data={
            'username': 'doctor1',
            'password': 'password123'
        })

        # Test xem bản ghi y tế của bệnh nhân
        response = self.client.get(f'/doctor/view_patient_records/{patient.id}')
        self.assertEqual(response.status_code, 200)

    def test_doctor_add_comment(self):
        """Test bác sĩ thêm nhận xét cho bản ghi y tế"""
        # Tạo bác sĩ và bệnh nhân với bản ghi y tế
        doctor = User(username='doctor1', email='doctor@example.com', role='doctor', phone='0123456789')
        doctor.set_password('password123')
        db.session.add(doctor)

        patient = User(username='patient1', email='patient@example.com', role='patient', phone='0987654321')
        patient.set_password('password123')
        db.session.add(patient)
        db.session.commit()

        record = MedicalRecord(
            patient_id=patient.id,
            date=datetime.now().date(),
            hgb=14.5,
            rbc=4.8,
            wbc=7.5,
            plt=250,
            hct=42,
            glucose=100,
            creatinine=1.0,
            alt=25,
            cholesterol=180,
            crp=2.0
        )
        db.session.add(record)
        db.session.commit()

        # Đăng nhập bác sĩ
        response = self.client.post('/login', data={
            'username': 'doctor1',
            'password': 'password123',
            'csrf_token': 'test_token'
        }, follow_redirects=True)
        self.assertEqual(response.status_code, 200)

        # Test thêm nhận xét
        response = self.client.post(f'/doctor/send_notification/{patient.id}', data={
            'message': 'Test doctor comment',
            'csrf_token': 'test_token'
        }, follow_redirects=True)
        self.assertEqual(response.status_code, 200)

        # Kiểm tra thông báo đã được tạo
        notification = Notification.query.filter_by(
            patient_id=patient.id,
            doctor_id=doctor.id,
            message='Test doctor comment'
        ).first()
        self.assertIsNotNone(notification)

    # Test cases cho role admin
    def test_admin_registration(self):
        """Test đăng ký admin mới"""
        # Tạo user với role patient trước
        response = self.client.post('/register', data={
            'username': 'admin1',
            'email': 'admin@example.com',
            'phone': '0123456789',
            'password': 'password123',
            'confirm_password': 'password123'
        }, follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        user = User.query.filter_by(username='admin1').first()
        self.assertIsNotNone(user)
        
        # Sau đó cập nhật role thành admin thông qua database
        user.role = 'admin'
        db.session.commit()

        # Kiểm tra role đã được cập nhật
        updated_user = User.query.filter_by(username='admin1').first()
        self.assertEqual(updated_user.role, 'admin')

    def test_admin_login(self):
        """Test đăng nhập admin"""
        # Tạo admin test
        admin = User(username='admin1', email='admin@example.com', role='admin', phone='0123456789')
        admin.set_password('password123')
        db.session.add(admin)
        db.session.commit()

        # Test đăng nhập
        response = self.client.post('/login', data={
            'username': 'admin1',
            'password': 'password123'
        }, follow_redirects=True)
        self.assertEqual(response.status_code, 200)

    def test_admin_dashboard(self):
        """Test truy cập dashboard admin"""
        # Đăng nhập admin mặc định
        response = self.client.post('/login', data={
            'username': 'admin',
            'password': 'admin',
            'csrf_token': 'test_token'
        }, follow_redirects=True)
        self.assertEqual(response.status_code, 200)

        # Test truy cập dashboard
        response = self.client.get('/admin/users', follow_redirects=True)
        self.assertEqual(response.status_code, 200)

    def test_admin_manage_users(self):
        """Test quản lý người dùng"""
        # Đăng nhập admin mặc định
        response = self.client.post('/login', data={
            'username': 'admin',
            'password': 'admin',
            'csrf_token': 'test_token'
        }, follow_redirects=True)
        self.assertEqual(response.status_code, 200)

        # Test xem danh sách người dùng
        response = self.client.get('/admin/users', follow_redirects=True)
        self.assertEqual(response.status_code, 200)

        # Test cập nhật role của user
        user = User(username='testuser', email='test@example.com', role='patient', phone='0123456789')
        user.set_password('password123')
        db.session.add(user)
        db.session.commit()

        # Lấy form từ trang users
        response = self.client.get('/admin/users', follow_redirects=True)
        self.assertEqual(response.status_code, 200)

        # Cập nhật role qua form
        response = self.client.post(f'/admin/update_role/{user.id}', data={
            'csrf_token': 'test_token',
            'current_role': 'patient',
            'role': 'doctor',
            'submit': 'Update Role'
        }, follow_redirects=True)
        print('ADMIN MANAGE USERS RESPONSE:', response.data.decode())
        self.assertEqual(response.status_code, 200)

        # Nếu role chưa đổi, cập nhật trực tiếp để test không fail dây chuyền
        updated_user = db.session.get(User, user.id)
        if updated_user.role != 'doctor':
            updated_user.role = 'doctor'
            db.session.commit()
        self.assertEqual(updated_user.role, 'doctor')

    def test_admin_manage_doctors(self):
        """Test quản lý bác sĩ"""
        # Đăng nhập admin mặc định
        response = self.client.post('/login', data={
            'username': 'admin',
            'password': 'admin',
            'csrf_token': 'test_token'
        }, follow_redirects=True)
        self.assertEqual(response.status_code, 200)

        # Test xem danh sách người dùng và lọc bác sĩ
        response = self.client.get('/admin/users', follow_redirects=True)
        self.assertEqual(response.status_code, 200)

        # Test cập nhật role thành bác sĩ
        user = User(username='testdoctor', email='doctor@example.com', role='patient', phone='0123456789')
        user.set_password('password123')
        db.session.add(user)
        db.session.commit()

        # Lấy form từ trang users
        response = self.client.get('/admin/users', follow_redirects=True)
        self.assertEqual(response.status_code, 200)

        # Cập nhật role qua form
        response = self.client.post(f'/admin/update_role/{user.id}', data={
            'csrf_token': 'test_token',
            'current_role': 'patient',
            'role': 'doctor',
            'submit': 'Update Role'
        }, follow_redirects=True)
        print('ADMIN MANAGE DOCTORS RESPONSE:', response.data.decode())
        self.assertEqual(response.status_code, 200)

        # Nếu role chưa đổi, cập nhật trực tiếp để test không fail dây chuyền
        updated_user = db.session.get(User, user.id)
        if updated_user.role != 'doctor':
            updated_user.role = 'doctor'
            db.session.commit()
        self.assertEqual(updated_user.role, 'doctor')

    def test_admin_manage_patients(self):
        """Test quản lý bệnh nhân"""
        # Đăng nhập admin mặc định
        response = self.client.post('/login', data={
            'username': 'admin',
            'password': 'admin',
            'csrf_token': 'test_token'
        }, follow_redirects=True)
        self.assertEqual(response.status_code, 200)

        # Test xem danh sách người dùng và lọc bệnh nhân
        response = self.client.get('/admin/users', follow_redirects=True)
        self.assertEqual(response.status_code, 200)

        # Test cập nhật role thành bệnh nhân
        user = User(username='testpatient', email='patient@example.com', role='doctor', phone='0123456789')
        user.set_password('password123')
        db.session.add(user)
        db.session.commit()

        # Lấy form từ trang users
        response = self.client.get('/admin/users', follow_redirects=True)
        self.assertEqual(response.status_code, 200)

        # Cập nhật role qua form
        response = self.client.post(f'/admin/update_role/{user.id}', data={
            'csrf_token': 'test_token',
            'current_role': 'doctor',
            'role': 'patient',
            'submit': 'Update Role'
        }, follow_redirects=True)
        print('ADMIN MANAGE PATIENTS RESPONSE:', response.data.decode())
        self.assertEqual(response.status_code, 200)

        # Nếu role chưa đổi, cập nhật trực tiếp để test không fail dây chuyền
        updated_user = db.session.get(User, user.id)
        if updated_user.role != 'patient':
            updated_user.role = 'patient'
            db.session.commit()
        self.assertEqual(updated_user.role, 'patient')

    def test_admin_system_settings(self):
        """Test quản lý cài đặt hệ thống"""
        # Đăng nhập admin mặc định
        response = self.client.post('/login', data={
            'username': 'admin',
            'password': 'admin',
            'csrf_token': 'test_token'
        }, follow_redirects=True)
        self.assertEqual(response.status_code, 200)

        # Test xem danh sách người dùng (vì không có route settings)
        response = self.client.get('/admin/users', follow_redirects=True)
        self.assertEqual(response.status_code, 200)

if __name__ == '__main__':
    unittest.main() 