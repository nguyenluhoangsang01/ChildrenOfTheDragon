# Sử dụng image Python chính thức
FROM python:3.12-slim

# Cập nhật và cài đặt các dependencies cần thiết
RUN apt-get update && apt-get install -y \
    tesseract-ocr \
    libtesseract-dev \
    libleptonica-dev \
    poppler-utils \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Tạo thư mục ứng dụng
WORKDIR /app

# Copy tất cả file vào thư mục làm việc
COPY . /app

# Cài đặt các gói Python
RUN pip install --no-cache-dir --upgrade pip
RUN pip install --no-cache-dir -r requirements.txt

# Chạy ứng dụng (sửa lại 'main.py' nếu file của bạn tên khác)
CMD ["python", "main.py"]