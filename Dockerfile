# Sử dụng image Python chính thức
FROM python:3.12-slim

# Cài đặt các gói hệ thống cần thiết
RUN apt-get update && apt-get install -y \
    tesseract-ocr \
    libtesseract-dev \
    libleptonica-dev \
    libgl1 \
    poppler-utils \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Tạo thư mục ứng dụng
WORKDIR /app

# Copy mã nguồn
COPY . /app

# Cài đặt các thư viện Python
RUN pip install --no-cache-dir --upgrade pip
RUN pip install --no-cache-dir -r requirements.txt

# Khởi chạy ứng dụng
CMD ["python", "main.py"]