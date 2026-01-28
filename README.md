<h2 align="center">
    <a href="https://dainam.edu.vn/vi/khoa-cong-nghe-thong-tin">
    🎓 Faculty of Information Technology (DaiNam University)
    </a>
</h2>
<h2 align="center">
   Hệ thống quản lý khách hàng và công việc trên nền tảng Odoo 15
</h2>
<div align="center">
    <p align="center">
        <img src="images/aiotlab_logo.png" alt="AIoTLab Logo" width="170"/>
        <img src="images/fitdnu_logo.png" alt="AIoTLab Logo" width="180"/>
        <img src="images/dnu_logo.png" alt="DaiNam University Logo" width="200"/>
    </p>

[![AIoTLab](https://img.shields.io/badge/AIoTLab-green?style=for-the-badge)](https://www.facebook.com/DNUAIoTLab)
[![Faculty of Information Technology](https://img.shields.io/badge/Faculty%20of%20Information%20Technology-blue?style=for-the-badge)](https://dainam.edu.vn/vi/khoa-cong-nghe-thong-tin)
[![DaiNam University](https://img.shields.io/badge/DaiNam%20University-orange?style=for-the-badge)](https://dainam.edu.vn)
</div>

## 1. Tổng quan về hệ thống

Hệ thống được xây dựng trên nền tảng Odoo 15 nhằm hỗ trợ doanh nghiệp quản lý tập trung các nghiệp vụ cốt lõi, bao gồm quản lý nhân sự, quản lý khách hàng và quản lý công việc. Hệ thống được thiết kế theo mô hình ERP module hóa, cho phép các chức năng liên kết chặt chẽ với nhau, đồng thời đảm bảo tính linh hoạt, dễ mở rộng và phù hợp với nhu cầu quản lý thực tế của doanh nghiệp.

Trong hệ thống, mỗi nghiệp vụ được triển khai dưới dạng một module độc lập nhưng có khả năng tích hợp và chia sẻ dữ liệu. Nhờ đó, thông tin về nhân sự, khách hàng, công việc và phản hồi được quản lý đồng bộ, giúp nâng cao hiệu quả vận hành, giảm thao tác thủ công và hỗ trợ nhà quản lý trong quá trình theo dõi, đánh giá và ra quyết định.

Bên cạnh các chức năng quản lý cơ bản, hệ thống còn tích hợp một số tính năng mở rộng như tự động hóa quy trình chăm sóc khách hàng, xử lý khiếu nại, đồng bộ lịch công việc với Google Calendar và chatbot nội quy hỗ trợ tra cứu quy định công ty. Các tính năng này góp phần nâng cao trải nghiệm người dùng và tiệm cận hơn với nhu cầu thực tế của doanh nghiệp hiện nay.

![Ubuntu](https://img.shields.io/badge/Ubuntu-E95420?style=for-the-badge&logo=ubuntu&logoColor=white)
![GitLab](https://img.shields.io/badge/gitlab-%23181717.svg?style=for-the-badge&logo=gitlab&logoColor=white)
![Postgres](https://img.shields.io/badge/postgres-%23316192.svg?style=for-the-badge&logo=postgresql&logoColor=white)

![Python](https://img.shields.io/badge/python-v3.8+-blue.svg)
[![security: bandit](https://img.shields.io/badge/security-bandit-yellow.svg)](https://github.com/PyCQA/bandit)




# 1. Cài đặt công cụ, môi trường và các thư viện cần thiết

## 1.1. Clone project.
git clone https://gitlab.com/anhlta/odoo-fitdnu.git
git checkout 

## 1.2. cài đặt các thư viện cần thiết

Người sử dụng thực thi các lệnh sau đề cài đặt các thư viện cần thiết

```
sudo apt-get install libxml2-dev libxslt-dev libldap2-dev libsasl2-dev libssl-dev python3.10-distutils python3.10-dev build-essential libssl-dev libffi-dev zlib1g-dev python3.10-venv libpq-dev
```
## 1.3. khởi tạo môi trường ảo.

`python3.10 -m venv ./venv`
Thay đổi trình thông dịch sang môi trường ảo và chạy requirements.txt để cài đặt tiếp các thư viện được yêu cầu

```
source venv/bin/activate
pip3 install -r requirements.txt
```

# 2. Setup database

Khởi tạo database trên docker bằng việc thực thi file dockercompose.yml.

`docker-compose up -d`

# 3. Setup tham số chạy cho hệ thống

## 3.1. Khởi tạo odoo.conf

Tạo tệp **odoo.conf** có nội dung như sau:

```
[options]
addons_path = addons
db_host = localhost
db_password = odoo
db_user = odoo
db_port = 5432
xmlrpc_port = 8069
```
Có thể kế thừa từ **odoo.conf.template**

Ngoài ra có thể thêm mổ số parameters như:

```
-c _<đường dẫn đến tệp odoo.conf>_
-u _<tên addons>_ giúp cập nhật addons đó trước khi khởi chạy
-d _<tên database>_ giúp chỉ rõ tên database được sử dụng
--dev=all giúp bật chế độ nhà phát triển 
```

# 4. Chạy hệ thống và cài đặt các ứng dụng cần thiết

Người sử dụng truy cập theo đường dẫn _http://localhost:8069/_ để đăng nhập vào hệ thống.

Hoàn tất
# 5. Modul Nhân sự, Quản lý công việc, Quản lý khách hàng
# Các Module Tùy Chỉnh cho Odoo

Dự án này bao gồm 3 module tùy chỉnh được phát triển cho công ty FITDNU, giúp quản lý nhân sự, khách hàng và công việc một cách hiệu quả.

## 1. Module Nhân Sự (nhan_su)

### Giới thiệu
Module này là nền tảng để quản lý thông tin nhân viên và chức vụ. Các module khác như quản lý công việc và khách hàng sẽ sử dụng dữ liệu từ đây.
![Quản lý nhân sự](image/qlns.png)
### Tính năng chính
- **Quản lý nhân viên**: Lưu thông tin cá nhân, liên hệ, chức vụ.
- **Quản lý chức vụ**: Danh sách các vị trí trong công ty.
- **Lịch sử công tác**: Theo dõi quá trình làm việc của nhân viên.
- **Chứng chỉ và bằng cấp**: Quản lý các chứng chỉ của nhân viên.

### Cách cài đặt
Cài module này trước khi cài các module khác như `quan_ly_cong_viec` và `quan_ly_khach_hang`.

### Lưu ý
- Chuẩn hóa danh sách chức vụ để gợi ý nhân viên chính xác.
- Thông tin nhân viên sẽ được sử dụng trong các module khác.

## 2. Module Quản Lý Khách Hàng (quan_ly_khach_hang)

### Giới thiệu
Module này giúp quản lý thông tin khách hàng, theo dõi giao dịch, hợp đồng, và tương tác với khách hàng. Phù hợp cho doanh nghiệp muốn theo dõi khách hàng tiềm năng và chăm sóc khách hàng tốt hơn.\
![Quản lý Khách hàng](image/qlkh.png)

### Tính năng chính
- **Quản lý khách hàng**: Lưu thông tin cá nhân, công ty, thu nhập, trạng thái.
- **Giao dịch và hợp đồng**: Theo dõi đơn hàng, hợp đồng, cơ hội bán hàng.
- **Tương tác**: Ghi lại các lần liên hệ với khách hàng.
- **Phản hồi và ghi chú**: Thu thập feedback và ghi chú về khách hàng.
- **Chiến dịch marketing**: Quản lý các chiến dịch để thu hút khách hàng.

### Cách cài đặt
1. Cài module `nhan_su` trước.
2. Cài module này.
3. Có thể cài thêm `quan_ly_cong_viec` để liên kết với dự án.

### Lưu ý
- Email và số điện thoại phải đúng định dạng.
- Ngày sinh không được là ngày tương lai.
- Nếu là khách hàng doanh nghiệp, cần nhập tên công ty và mã số thuế.

## 3. Module Quản Lý Công Việc (quan_ly_cong_viec)

### Giới thiệu
Module này giúp quản lý dự án và công việc trong công ty. Bạn có thể tạo dự án, phân chia công việc, theo dõi tiến độ và giao tiếp qua chatbot.
![Quản lý công việc](image/qlcv1.png)

### Tính năng chính
- **Quản lý dự án**: Tạo dự án, chọn khách hàng, người phụ trách, nhân viên tham gia. Theo dõi tiến độ và deadline.
- **Công việc**: Chia công việc thành giai đoạn, gán cho nhân viên, ghi nhật ký làm việc.
- **Đánh giá nhân viên**: Đánh giá hiệu suất của nhân viên trong dự án.
- **Dashboard**: Xem tổng quan số dự án, công việc, tiến độ.
- **Chatbot**: Hỏi nhanh về dự án, công việc qua chatbot tích hợp Gemini.

### Cách cài đặt
1. Cài module `nhan_su` trước.
2. Cài module `quan_ly_khach_hang`.
3. Cài module này.
4. Cấu hình chatbot nếu muốn dùng.

### Lưu ý
- Tiến độ phải từ 0% đến 100%.
- Khi dự án hoàn thành, công việc sẽ tự động chuyển sang giai đoạn hoàn thành.

## Thứ Tự Cài Đặt Các Module
Để tránh lỗi phụ thuộc, hãy cài theo thứ tự sau:
1. `nhan_su`
2. `quan_ly_khach_hang`
3. `quan_ly_cong_viec`

## Tác Giả
# Nhóm 7: CNTT16-01
Các module được phát triển cho công ty FITDNU.
    
