FROM python:3.11

WORKDIR /app

# Requirements
COPY requirements.txt ./
RUN pip install -r requirements.txt

# Ports
EXPOSE 5000

COPY *.py .

CMD [ "python", "main.py" ]