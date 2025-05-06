FROM python:3.12-slim

# Cài libGL để OpenCV hoạt động
RUN apt-get update && apt-get install -y libgl1

# Copy code vào container
WORKDIR /app
COPY . /app

# Cài Python dependencies
RUN pip install -r requirements.txt

CMD ["python", "main.py"]