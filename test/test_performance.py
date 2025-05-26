from locust import HttpUser, task, between
from app import create_app, db
from app.models.user import User
from app.models.medical_record import MedicalRecord
from app.config import TestingConfig
from bs4 import BeautifulSoup
import random
import time

user_counter = 0

class BaseUser(HttpUser):
    abstract = True
    wait_time = between(1, 2.5)
    csrf_token = None

    def on_start(self):
        self.get_csrf_token()
        if self.csrf_token:
            self.login()

    def get_csrf_token(self):
        try:
            response = self.client.get("/login", catch_response=True)
            if response.status_code == 200:
                soup = BeautifulSoup(response.content, 'html.parser')
                csrf_input = soup.find('input', {'name': 'csrf_token'})
                if csrf_input:
                    self.csrf_token = csrf_input['value']
                else:
                    response.failure("CSRF token not found on login page")
            else:
                response.failure(f"Failed to get login page: {response.status_code}")
        except Exception as e:
            self.environment.runner.quit()
            print(f"Error getting CSRF token: {e}")
            self.csrf_token = None

    def login(self):
        login_data = {
            "username": self.username,
            "password": self.password,
            "csrf_token": self.csrf_token
        }
        response = self.client.post("/login", login_data, catch_response=True)
        if response.status_code != 200:
            response.failure(f"Failed to login as {self.username}: {response.status_code}")
            # Dừng nếu đăng nhập thất bại
            # self.environment.runner.quit() # Tạm comment để test các user khác

class WebsiteUser(BaseUser):
    username = "testuser"
    password = "password123"
    wait_time = between(1, 2.5)  # Thời gian chờ giữa các request (1-2.5 giây)

    @task(3)  # Tần suất thực hiện task (3 lần)
    def view_medical_records(self):
        """Xem danh sách bản ghi y tế"""
        with self.client.get("/patient/view_records", catch_response=True) as response:
            if response.status_code != 200:
                response.failure(f"Failed to view records: {response.status_code}")

    @task(2)  # Tần suất thực hiện task (2 lần)
    def create_medical_record(self):
        """Tạo bản ghi y tế mới"""
        if not self.csrf_token:
             return # Bỏ qua nếu không có token
        # Tạo dữ liệu ngẫu nhiên hơn cho bản ghi y tế
        record_data = {
            "date": "2024-01-01", # Có thể làm động ngày này
            "hgb": round(random.uniform(12, 16), 1),
            "rbc": round(random.uniform(4, 5.5), 1),
            "wbc": round(random.uniform(4, 11), 1),
            "plt": random.randint(150, 400),
            "hct": round(random.uniform(35, 50), 1),
            "glucose": random.randint(70, 140),
            "creatinine": round(random.uniform(0.5, 1.5), 1),
            "alt": random.randint(10, 50),
            "cholesterol": random.randint(150, 250),
            "crp": round(random.uniform(0.1, 10), 1),
            "csrf_token": self.csrf_token
        }
        with self.client.post("/patient/new_record", record_data, catch_response=True) as response:
            if response.status_code != 200:
                response.failure(f"Failed to create record: {response.status_code}")

    # @task(1) # Tạm bỏ task search vì nó không tồn tại cho patient
    # def search_records(self):
    #     """Tìm kiếm bản ghi y tế"""
    #     with self.client.get("/patient/search?query=test", catch_response=True) as response:
    #         if response.status_code != 200:
    #             response.failure(f"Failed to search records: {response.status_code}")

    @task(1) # Thêm task xem thông báo
    def view_notifications(self):
        """Xem thông báo"""
        with self.client.get("/patient/notifications", catch_response=True) as response:
            if response.status_code != 200:
                response.failure(f"Failed to view notifications: {response.status_code}")

class DoctorUser(BaseUser):
    username = "testdoctor"
    password = "password123"
    wait_time = between(1, 3)
    
    @task(3)
    def view_patient_records(self):
        """Xem bản ghi của bệnh nhân (cần patient_id)"""
        # Giả sử patient có ID 1 tồn tại. Cần cải tiến để lấy ID động.
        patient_id = 1 
        with self.client.get(f"/doctor/view_patient_records/{patient_id}", catch_response=True) as response:
            if response.status_code != 200:
                response.failure(f"Failed to view patient records for ID {patient_id}: {response.status_code}")

    @task(2)
    def add_comment(self):
        """Thêm nhận xét cho bệnh nhân (cần patient_id)"""
        if not self.csrf_token:
            return # Bỏ qua nếu không có token
        # Giả sử patient có ID 1 tồn tại. Cần cải tiến để lấy ID động.
        patient_id = 1
        comment_data = {
            "message": f"Test comment from doctor {self.username} at {int(time.time())}",
            "csrf_token": self.csrf_token
        }
        with self.client.post(f"/doctor/send_notification/{patient_id}", comment_data, catch_response=True) as response:
            if response.status_code != 200:
                response.failure(f"Failed to add comment for ID {patient_id}: {response.status_code}")

    @task(1)
    def search_patients(self):
        """Tìm kiếm bệnh nhân"""
        # Tìm kiếm với query ngẫu nhiên hoặc cố định
        search_query = random.choice(["testuser", "patient", "admin", "", "xyz"]) # Thêm các query có thể có hoặc không có kết quả
        with self.client.get(f"/doctor/search_patient?query={search_query}", catch_response=True) as response:
             if response.status_code != 200:
                 response.failure(f"Failed to search patients with query '{search_query}': {response.status_code}")

class AdminUser(BaseUser):
    username = "admin"
    password = "admin"
    wait_time = between(1, 4)
    
    @task(5) # Tăng tần suất xem danh sách user vì là task nhẹ
    def manage_users(self):
        """Xem danh sách người dùng"""
        with self.client.get("/admin/users", catch_response=True) as response:
            if response.status_code != 200:
                response.failure(f"Failed to view users page: {response.status_code}")

    @task(1) # Tần suất thấp cho các tác vụ thay đổi dữ liệu
    def admin_update_user_role(self):
        """Admin đổi vai trò của người dùng"""
        if not self.csrf_token:
            return # Bỏ qua nếu không có token
        # Cần ID của một user test (không phải admin) và vai trò mới
        # Thay thế 2 bằng ID của user test (ví dụ testuser có thể có ID 2 hoặc khác)
        user_id_to_update = 2 # <--- CẦN CẬP NHẬT ID NÀY
        new_role = random.choice(['patient', 'doctor'])
        update_data = {
            'role': new_role,
            'current_role': 'patient', # Giả định user hiện tại là patient, cần lấy động
            'submit': 'Update Role',
            'csrf_token': self.csrf_token
        }
        with self.client.post(f"/admin/update_role/{user_id_to_update}", update_data, catch_response=True) as response:
            if response.status_code not in [200, 302]: # Chấp nhận 200 OK hoặc 302 Redirect
                response.failure(f"Failed to update role for user {user_id_to_update}: {response.status_code}")

    @task(1) # Tần suất thấp cho các tác vụ thay đổi dữ liệu
    def admin_reset_user_password(self):
        """Admin đặt lại mật khẩu người dùng"""
        if not self.csrf_token:
            return # Bỏ qua nếu không có token
        # Cần ID của một user test (không phải admin)
        # Thay thế 2 bằng ID của user test
        user_id_to_reset_password = 2 # <--- CẦN CẬP NHẬT ID NÀY
        new_password = f"newpass{int(time.time())}"
        reset_data = {
            'new_password': new_password,
            'confirm_password': new_password,
            'submit': 'Reset Password',
            'csrf_token': self.csrf_token
        }
        with self.client.post(f"/admin/reset_password/{user_id_to_reset_password}", reset_data, catch_response=True) as response:
             if response.status_code not in [200, 302]: # Chấp nhận 200 OK hoặc 302 Redirect
                 response.failure(f"Failed to reset password for user {user_id_to_reset_password}: {response.status_code}")

class GuestUser(HttpUser):
    wait_time = between(1, 5)
    
    def on_start(self):
        self.get_csrf_token_register()

    def get_csrf_token_register(self):
         try:
            response = self.client.get("/register", catch_response=True)
            if response.status_code == 200:
                soup = BeautifulSoup(response.content, 'html.parser')
                csrf_input = soup.find('input', {'name': 'csrf_token'})
                if csrf_input:
                    self.csrf_token = csrf_input['value']
                else:
                    response.failure("CSRF token not found on register page")
            else:
                response.failure(f"Failed to get register page: {response.status_code}")
         except Exception as e:
            self.environment.runner.quit()
            print(f"Error getting CSRF token for register: {e}")
            self.csrf_token = None

    @task(1)
    def register_user(self):
        """Đăng ký người dùng mới"""
        if not self.csrf_token:
            self.get_csrf_token_register() # Thử lấy lại token nếu chưa có
            if not self.csrf_token: # Nếu vẫn không có, bỏ qua
                return
                
        global user_counter
        user_counter += 1
        new_username = f"newuser{user_counter}_{int(time.time())}"
        new_email = f"newuser{user_counter}_{int(time.time())}@example.com"
        password = "newpassword123"
        
        register_data = {
            'username': new_username,
            'email': new_email,
            'phone': f'012345{user_counter}',
            'password': password,
            'confirm_password': password,
            'role': random.choice(['patient', 'doctor']),
            'submit': 'Register',
            'csrf_token': self.csrf_token
        }
        with self.client.post("/register", register_data, catch_response=True) as response:
            if response.status_code not in [200, 302]: # Chấp nhận 200 OK hoặc 302 Redirect
                 response.failure(f"Failed to register user {new_username}: {response.status_code}, Response: {response.text}")
            else:
                 response.success()

    @task(2)
    def view_login_page(self):
        """Xem trang đăng nhập"""
        self.client.get("/login")