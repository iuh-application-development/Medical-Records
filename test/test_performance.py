import unittest
import time
from app import create_app, db
from app.models.user import User
from app.models.medical_record import MedicalRecord
from app.config import TestingConfig

class PerformanceTest(unittest.TestCase):
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

    def test_user_registration_performance(self):
        """Test hiệu suất đăng ký người dùng"""
        start_time = time.time()
        
        # Test đăng ký 10 user
        for i in range(10):
            response = self.client.post('/register', data={
                'username': f'testuser{i}',
                'email': f'test{i}@example.com',
                'phone': f'012345678{i}',
                'password': 'password123',
                'confirm_password': 'password123',
                'role': 'patient',
                'csrf_token': 'test_token'
            }, follow_redirects=True)
            self.assertEqual(response.status_code, 200)
        
        end_time = time.time()
        execution_time = end_time - start_time
        
        # Kiểm tra thời gian thực thi
        self.assertLess(execution_time, 5.0)  # Phải hoàn thành trong 5 giây

    def test_medical_record_creation_performance(self):
        """Test hiệu suất tạo bản ghi y tế"""
        # Tạo user test
        user = User(username='testuser', email='test@example.com', role='patient', phone='0123456789')
        user.set_password('password123')
        db.session.add(user)
        db.session.commit()

        # Đăng nhập
        self.client.post('/login', data={
            'username': 'testuser',
            'password': 'password123',
            'csrf_token': 'test_token'
        })

        start_time = time.time()
        
        # Test tạo 10 bản ghi y tế
        for i in range(10):
            response = self.client.post('/patient/new_record', data={
                'date': '2024-01-01',
                'hgb': 14.5,
                'rbc': 4.8,
                'wbc': 7.5,
                'plt': 250,
                'hct': 42,
                'glucose': 100,
                'creatinine': 1.0,
                'alt': 25,
                'cholesterol': 180,
                'crp': 2.0,
                'csrf_token': 'test_token',
                'submit': 'Save Record'
            }, follow_redirects=True)
            self.assertEqual(response.status_code, 200)
        
        end_time = time.time()
        execution_time = end_time - start_time
        
        # Kiểm tra thời gian thực thi
        self.assertLess(execution_time, 5.0)  # Phải hoàn thành trong 5 giây

    def test_search_performance(self):
        """Test hiệu suất tìm kiếm"""
        # Tạo 10 user test
        for i in range(10):
            user = User(username=f'testuser{i}', email=f'test{i}@example.com', role='patient', phone=f'012345678{i}')
            user.set_password('password123')
            db.session.add(user)
        db.session.commit()

        # Đăng nhập admin
        self.client.post('/login', data={
            'username': 'admin',
            'password': 'admin',
            'csrf_token': 'test_token'
        })

        start_time = time.time()
        
        # Test tìm kiếm
        response = self.client.get('/admin/users?search=test', follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        
        end_time = time.time()
        execution_time = end_time - start_time
        
        # Kiểm tra thời gian thực thi
        self.assertLess(execution_time, 1.0)  # Phải hoàn thành trong 1 giây

    def test_bulk_medical_record_creation(self):
        """Test hiệu suất tạo nhiều bản ghi y tế cùng lúc"""
        # Tạo user test
        user = User(username='testuser', email='test@example.com', role='patient', phone='0123456789')
        user.set_password('password123')
        db.session.add(user)
        db.session.commit()

        # Đăng nhập
        self.client.post('/login', data={
            'username': 'testuser',
            'password': 'password123',
            'csrf_token': 'test_token'
        })

        start_time = time.time()
        
        # Test tạo 50 bản ghi y tế
        for i in range(50):
            response = self.client.post('/patient/new_record', data={
                'date': '2024-01-01',
                'hgb': 14.5,
                'rbc': 4.8,
                'wbc': 7.5,
                'plt': 250,
                'hct': 42,
                'glucose': 100,
                'creatinine': 1.0,
                'alt': 25,
                'cholesterol': 180,
                'crp': 2.0,
                'csrf_token': 'test_token',
                'submit': 'Save Record'
            }, follow_redirects=True)
            self.assertEqual(response.status_code, 200)
        
        end_time = time.time()
        execution_time = end_time - start_time
        
        # Kiểm tra thời gian thực thi
        self.assertLess(execution_time, 15.0)  # Phải hoàn thành trong 15 giây

    def test_concurrent_user_operations(self):
        """Test hiệu suất khi nhiều user thao tác cùng lúc"""
        # Tạo 5 user test
        users = []
        for i in range(5):
            user = User(username=f'testuser{i}', email=f'test{i}@example.com', role='patient', phone=f'012345678{i}')
            user.set_password('password123')
            db.session.add(user)
            users.append(user)
        db.session.commit()

        start_time = time.time()
        
        # Mỗi user tạo 5 bản ghi y tế
        for user in users:
            # Đăng nhập
            self.client.post('/login', data={
                'username': user.username,
                'password': 'password123',
                'csrf_token': 'test_token'
            })
            
            # Tạo bản ghi
            for i in range(5):
                response = self.client.post('/patient/new_record', data={
                    'date': '2024-01-01',
                    'hgb': 14.5,
                    'rbc': 4.8,
                    'wbc': 7.5,
                    'plt': 250,
                    'hct': 42,
                    'glucose': 100,
                    'creatinine': 1.0,
                    'alt': 25,
                    'cholesterol': 180,
                    'crp': 2.0,
                    'csrf_token': 'test_token',
                    'submit': 'Save Record'
                }, follow_redirects=True)
                self.assertEqual(response.status_code, 200)
        
        end_time = time.time()
        execution_time = end_time - start_time
        
        # Kiểm tra thời gian thực thi
        self.assertLess(execution_time, 20.0)  # Phải hoàn thành trong 20 giây

    def test_database_query_performance(self):
        """Test hiệu suất truy vấn database"""
        # Tạo 100 user test
        for i in range(100):
            user = User(username=f'testuser{i}', email=f'test{i}@example.com', role='patient', phone=f'012345678{i}')
            user.set_password('password123')
            db.session.add(user)
        db.session.commit()

        start_time = time.time()
        
        # Test các truy vấn phức tạp
        # 1. Tìm kiếm user theo nhiều điều kiện
        users = User.query.filter(User.username.like('%test%')).filter(User.role == 'patient').all()
        self.assertEqual(len(users), 100)
        
        # 2. Phân trang
        page1 = User.query.paginate(page=1, per_page=20)
        self.assertEqual(len(page1.items), 20)
        
        # 3. Sắp xếp
        sorted_users = User.query.order_by(User.username).all()
        self.assertEqual(len(sorted_users), 100)
        
        end_time = time.time()
        execution_time = end_time - start_time
        
        # Kiểm tra thời gian thực thi
        self.assertLess(execution_time, 2.0)  # Phải hoàn thành trong 2 giây

    def test_doctor_operations_performance(self):
        """Test hiệu suất các thao tác của bác sĩ"""
        # Tạo bác sĩ test
        doctor = User(username='testdoctor', email='doctor@example.com', role='doctor', phone='0123456789')
        doctor.set_password('password123')
        db.session.add(doctor)
        db.session.commit()

        # Đăng nhập
        self.client.post('/login', data={
            'username': 'testdoctor',
            'password': 'password123',
            'csrf_token': 'test_token'
        })

        start_time = time.time()

        # 1. Test tìm kiếm bệnh nhân
        response = self.client.get('/doctor/search_patient', follow_redirects=True)
        self.assertEqual(response.status_code, 200)

        # 2. Test xem bản ghi y tế của bệnh nhân
        response = self.client.get('/doctor/view_patient_records/1', follow_redirects=True)
        self.assertEqual(response.status_code, 200)

        # 3. Test thêm nhận xét
        response = self.client.post('/doctor/send_notification/1', data={
            'message': 'Test comment',
            'csrf_token': 'test_token'
        }, follow_redirects=True)
        self.assertEqual(response.status_code, 200)

        end_time = time.time()
        execution_time = end_time - start_time
        
        # Kiểm tra thời gian thực thi
        self.assertLess(execution_time, 3.0)  # Phải hoàn thành trong 3 giây

    def test_patient_operations_performance(self):
        """Test hiệu suất các thao tác của bệnh nhân"""
        # Tạo bệnh nhân test
        patient = User(username='testpatient', email='patient@example.com', role='patient', phone='0123456789')
        patient.set_password('password123')
        db.session.add(patient)
        db.session.commit()

        # Đăng nhập
        self.client.post('/login', data={
            'username': 'testpatient',
            'password': 'password123',
            'csrf_token': 'test_token'
        })

        start_time = time.time()

        # 1. Test xem thông tin cá nhân
        response = self.client.get('/patient/profile', follow_redirects=True)
        self.assertEqual(response.status_code, 200)

        # 2. Test xem lịch sử bản ghi y tế
        response = self.client.get('/patient/view_records', follow_redirects=True)
        self.assertEqual(response.status_code, 200)

        # 3. Test cập nhật thông tin cá nhân
        response = self.client.post('/patient/profile', data={
            'full_name': 'Test User',
            'phone': '0987654321',
            'email': 'newemail@example.com',
            'csrf_token': 'test_token'
        }, follow_redirects=True)
        self.assertEqual(response.status_code, 200)

        end_time = time.time()
        execution_time = end_time - start_time
        
        # Kiểm tra thời gian thực thi
        self.assertLess(execution_time, 3.0)  # Phải hoàn thành trong 3 giây

    def test_admin_operations_performance(self):
        """Test hiệu suất các thao tác của admin"""
        # Đăng nhập admin
        self.client.post('/login', data={
            'username': 'admin',
            'password': 'admin',
            'csrf_token': 'test_token'
        })

        start_time = time.time()

        # 1. Test quản lý người dùng
        response = self.client.get('/admin/users', follow_redirects=True)
        self.assertEqual(response.status_code, 200)

        # 2. Test cập nhật vai trò người dùng
        response = self.client.post('/admin/update_role/1', data={
            'role': 'doctor',
            'csrf_token': 'test_token'
        }, follow_redirects=True)
        self.assertEqual(response.status_code, 200)

        # 3. Test reset mật khẩu
        response = self.client.post('/admin/reset_password/1', data={
            'new_password': 'newpassword123',
            'confirm_password': 'newpassword123',
            'csrf_token': 'test_token'
        }, follow_redirects=True)
        self.assertEqual(response.status_code, 200)

        end_time = time.time()
        execution_time = end_time - start_time
        
        # Kiểm tra thời gian thực thi
        self.assertLess(execution_time, 4.0)  # Phải hoàn thành trong 4 giây

    def test_export_performance(self):
        """Test hiệu suất xuất dữ liệu"""
        # Tạo dữ liệu test
        for i in range(50):
            user = User(username=f'testuser{i}', email=f'test{i}@example.com', role='patient', phone=f'012345678{i}')
            user.set_password('password123')
            db.session.add(user)
        db.session.commit()

        # Đăng nhập admin
        with self.client.session_transaction() as session:
            session['csrf_token'] = 'test_token'
        
        self.client.post('/login', data={
            'username': 'admin',
            'password': 'admin',
            'csrf_token': 'test_token'
        })

        start_time = time.time()

        # 1. Test xuất danh sách người dùng
        response = self.client.get('/admin/users/export', headers={
            'X-CSRFToken': 'test_token'
        }, follow_redirects=True)
        self.assertEqual(response.status_code, 200)

        # 2. Test xuất bản ghi y tế
        response = self.client.get('/admin/records/export', headers={
            'X-CSRFToken': 'test_token'
        }, follow_redirects=True)
        self.assertEqual(response.status_code, 200)

        end_time = time.time()
        execution_time = end_time - start_time
        
        # Kiểm tra thời gian thực thi
        self.assertLess(execution_time, 5.0)  # Phải hoàn thành trong 5 giây

if __name__ == '__main__':
    unittest.main() 