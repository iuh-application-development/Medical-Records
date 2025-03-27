# **Medical Records's System**
## **Thành viên nhóm**
- **Thành viên 1:** Trương Công Đạt - 22685561
- **Thành viên 2:** Nguyễn Gia Lâm - 22685611
- **Thành viên 3:** Phan Tấn Tài - 22684181
## **1. Tổng Quan**

**Medical Records's System** là một nền tảng web toàn diện giúp bệnh nhân, bác sĩ quản lý các bảng ghi lại các phiếu xét nghiệm máu . Hệ thống cho phép:

* Bệnh nhân **xem và thêm kết quả xét nghiệm máu** trong môi trường an toàn
* Bác sĩ **tìm kiếm, xem xét các bản ghi** và gửi thông báo đến bệnh nhân
* Quản trị viên **quản lý tài khoản người dùng** và quyền hạn hệ thống

Nền tảng có giao diện thích ứng với khả năng trực quan hóa dữ liệu để theo dõi các chỉ số sức khỏe theo thời gian.

## **2. Công Nghệ Sử Dụng**

* **Backend**: Flask
* **Frontend**: Bootstrap, Plotly.js cho trực quan hóa dữ liệu
* **Cơ sở dữ liệu**: SQLite
* **Xác thực**: Flask-Login
* **Dịch vụ Email**: Flask-Mail
* **Môi trường ảo**: Python venv

---

## **3. Tính Năng Chính**

### **3.1. Tính Năng Cho Bệnh Nhân**

✅ **Quản lý tài khoản**:
* Đăng ký, đăng nhập và cập nhật thông tin cá nhân
* Đặt lại mật khẩu thông qua xác minh email

✅ **Hồ sơ y tế**:
* Thêm kết quả xét nghiệm y tế mới
* Xem dữ liệu y tế lịch sử
* Trực quan hóa các chỉ số sức khỏe thông qua biểu đồ tương tác

✅ **Thông báo**:
* Nhận và quản lý thông báo từ bác sĩ
* Đánh dấu thông báo đã đọc

### **3.2. Tính Năng Cho Bác Sĩ**

✅ **Quản lý bệnh nhân**:
* Tìm kiếm bệnh nhân trong hệ thống
* Xem hồ sơ y tế của bệnh nhân
* Tải xuống dữ liệu bệnh nhân dưới dạng CSV

✅ **Giao tiếp**:
* Gửi thông báo đến bệnh nhân

### **3.3. Tính Năng Cho Quản Trị Viên**

✅ **Quản lý người dùng**:
* Xem tất cả người dùng hệ thống
* Cập nhật vai trò người dùng (bệnh nhân, bác sĩ, quản trị viên)
* Đặt lại mật khẩu người dùng
---

## **4. Cấu Trúc Cơ Sở Dữ Liệu**

### **4.1. Bảng Người Dùng**

| Trường | Kiểu | Mô tả |
|-------|------|-------------|
| id | Integer | Khóa chính |
| username | String | Tên đăng nhập duy nhất |
| email | String | Địa chỉ email người dùng |
| password_hash | String | Mật khẩu đã mã hóa |
| phone | String | Số điện thoại liên hệ |
| full_name | String | Họ tên đầy đủ |
| avatar | String | Đường dẫn ảnh đại diện |
| role | String | Vai trò người dùng (bệnh nhân/bác sĩ/quản trị viên) |
| reset_code | String | Mã xác minh đặt lại mật khẩu |
| reset_code_expiry | DateTime | Thời gian hết hạn mã đặt lại |

### **4.2. Bảng Hồ Sơ Y Tế**

| Trường | Kiểu | Mô tả |
|-------|------|-------------|
| id | Integer | Khóa chính |
| patient_id | Integer | Khóa ngoại đến Người dùng |
| date | DateTime | Ngày ghi nhận |
| hgb | Float | Mức hemoglobin |
| rbc | Float | Số lượng hồng cầu |
| wbc | Float | Số lượng bạch cầu |
| plt | Float | Số lượng tiểu cầu |
| hct | Float | Hematocrit |
| glucose | Float | Đường huyết |
| creatinine | Float | Mức creatinine |
| alt | Float | Alanine transaminase |
| cholesterol | Float | Mức cholesterol |
| crp | Float | Protein C-phản ứng |

### **4.3. Bảng Thông Báo**

| Trường | Kiểu | Mô tả |
|-------|------|-------------|
| id | Integer | Khóa chính |
| patient_id | Integer | Khóa ngoại đến Người dùng |
| message | Text | Nội dung thông báo |
| date | DateTime | Ngày thông báo |
| read | Boolean | Trạng thái đã đọc |

---

## **5. Quy Trình Hệ Thống**

### **5.1. Quy Trình Bệnh Nhân**

1️⃣ Đăng ký và tạo tài khoản

2️⃣ Thêm kết quả xét nghiệm máu

3️⃣ Xem dữ liệu lịch sử và biểu đồ trực quan

4️⃣ Nhận thông báo từ bác sĩ

### **5.2. Quy Trình Bác Sĩ**

1️⃣ Đăng nhập với thông tin bác sĩ

2️⃣ Tìm kiếm bệnh nhân cụ thể

3️⃣ Xem xét các bản ghi của bệnh nhân

4️⃣ Gửi thông báo hoặc khuyến nghị

5️⃣ Tải xuống dữ liệu bệnh nhân để phân tích thêm

### **5.3. Quy Trình Quản Trị Viên**

1️⃣ Quản lý tài khoản người dùng và quyền hạn

2️⃣ Cập nhật vai trò người dùng khi cần

3️⃣ Đặt lại mật khẩu cho người dùng
---

## **6. Cấu Trúc Dự Án**

```
medical-records/
├── app.py                  # Tệp ứng dụng chính
├── forms.py               # Định nghĩa biểu mẫu
├── requirements.txt       # Các gói phụ thuộc
├── instance/              # Tệp cơ sở dữ liệu
│   └── medical_records.db # Cơ sở dữ liệu SQLite
├── static/                # Tài nguyên tĩnh
│   ├── images/            # Tệp hình ảnh
│   └── uploads/           # Tải lên của người dùng
├── templates/             # Mẫu HTML
│   ├── admin_users.html   # Quản lý người dùng của quản trị viên
│   ├── base.html          # Mẫu cơ sở
│   ├── home.html          # Trang chủ
│   ├── login.html         # Trang đăng nhập
│   ├── new_record.html    # Thêm bản ghi mới
│   ├── notifications.html # Thông báo người dùng
│   ├── patient_records.html # Xem hồ sơ bệnh nhân
│   ├── profile.html       # Hồ sơ người dùng
│   ├── register.html      # Trang đăng ký
│   ├── search_patient.html # Tìm kiếm bệnh nhân
│   └── view_charts.html   # Trực quan hóa dữ liệu
└── venv/                  # Môi trường ảo
```

## **7. Cài Đặt và Thiết Lập**

1. Clone repo:  `git clone https://github.com/iuh-application-development/Medical-Records.git`
                `cd .\Medical-Records\`
2. Tạo môi trường ảo: `python -m venv venv`
3. Kích hoạt môi trường ảo:
   - Windows: `venv\Scripts\activate`
   - Linux/Mac: `source venv/bin/activate`
4. Cài đặt các gói phụ thuộc: `pip install -r requirements.txt`
5. Thiết lập biến môi trường cho cấu hình email
6. Khởi tạo cơ sở dữ liệu
7. Chạy ứng dụng: `python app.py`

---

