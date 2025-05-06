FROM python:3.12

RUN apt-get update && apt-get install -y libglib2.0-0 libgl1-mesa-glx

COPY requirements.txt requirements.txt
RUN pip install -r requirements.txt

COPY . .

CMD ["python", "main.py"]
