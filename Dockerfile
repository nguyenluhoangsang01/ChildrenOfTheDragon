# Sử dụng image Python nhẹ nhất có thể
FROM python:3.12-slim

# Cài libGL (chỉ cần nếu bạn xài opencv-python, không cần cho opencv-python-headless)
RUN apt-get update && apt-get install -y libgl1

# Tạo thư mục làm việc
WORKDIR /app

# Copy toàn bộ mã nguồn vào container
COPY . /app

# Cài các gói Python cần thiết
RUN pip install --no-cache-dir -r requirements.txt

# Command mặc định khi container chạy
CMD ["python", "main.py"]