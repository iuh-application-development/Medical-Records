# Mô tả đề tài

Medical Records là một nền tảng web toàn diện giúp bệnh nhân, bác sĩ quản lý các bảng ghi lại một số chỉ sô quan trọng có trong các phiếu xét nghiệm máu để tiện theo dõi. Hệ thống cho phép:

* Bệnh nhân **xem và thêm một số chỉ số quan trọng trong kết quả xét nghiệm máu** 
* Bác sĩ **tìm kiếm, xem xét các bản ghi** và **gửi thông báo đến bệnh nhân**
* Quản trị viên **quản lý tài khoản người dùng** 

Ngoài ra, người dùng còn có thể giao tiếp với AI của Gemini về các vấn đề liên quan đến lĩnh vực y tế.

# Thông tin nhóm
| Họ và tên       | MSSV     | Email                 |
| --------------- | -------- | --------------------- |
| Trương Công Đạt | 22685561 | tdat4926@gmail.com    |
| Nguyễn Gia Lâm  | 22685611 | lam2004ha@gmail.com   |
| han Tấn Tài     | 22684181 | tide.tantai@gmail.com |


# Hướng dẫn cài đặt hoặc sử dụng
## Yêu cầu : Phải cài đặt miniconda trước khi chạy các bước tiếp theo bên dưới.
```bash 
winget install -e --id Anaconda.Miniconda3
```
1.  Clone repo:
    ```bash
    git clone https://github.com/iuh-application-development/Medical-Records.git
    ```
    ```bash
    cd .\Medical-Records\
    ```
## Chạy cơ bản  
2.  Tạo môi trường ảo:
    ```bash
    python -m venv venv
    ```
3.  Kích hoạt môi trường ảo:
    - Đối với Windows:
    ```bash
    venv\Scripts\activate
    ```
    - Đối với Linux/Mac:
    ```bash
    source venv/bin/activate
    ```
4.  Cài đặt các gói phụ thuộc:
    ```bash
    pip install -r requirements.txt
    ```
5.  Chạy ứng dụng:
    ```bash
    python run.py
    ```
## Chạy tự động
```bash
    .\setup-and-run.ps1
```
# Link video

[Link Video Demo] 

# Screenshots
- **Giao diện trò chuyện với AI**
![Screenshot user](./static/images/Screenshots/chat_AI.jpg) 
## Role Patient
- **Tạo bản ghi mới**
![Screenshot user](./static/images/Screenshots/new_record.jpg) 
- **Xem danh sách các bản ghi**
![Screenshot user](./static/images/Screenshots/view_records.jpg) 
- **Xem các biểu đồ đường của các bản ghi đã nhập**
![Screenshot user](./static/images/Screenshots/show_charts.jpg)
- **Xem thông báo**
![Screenshot user](./static/images/Screenshots/patient_notification.jpg)
- **Xem thông tin liên lạc của bác sĩ**
![Screenshot user](./static/images/Screenshots/search_doctors.jpg) 

## Role Doctor
- **Xem danh sách các bệnh nhân**
![Screenshot user](./static/images/Screenshots/search_patients.jpg) 
- **Xem các bản ghi của bệnh nhân đã tạo**
![Screenshot user](./static/images/Screenshots/view_patient_records.jpg) 
- **Xem biểu đồ của các bản ghi**
![Screenshot user](./static/images/Screenshots/show_patient_chart.jpg) 
- **Gửi thông báo cho bệnh nhân**
![Screenshot user](./static/images/Screenshots/send_notification.jpg)

## Role Admin 
- **Giao diện quản lý người dùng**
![Screenshot user](./static/images/Screenshots/Admin_manage_user.jpg) 

# Link web đã triển khai: [Medical Record](https://medical-records-pzlf.onrender.com/)