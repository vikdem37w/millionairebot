FROM python:3.13.5-alpine
WORKDIR /app/
# RUN apk add --no-cache gcc musl-dev linux-headers
COPY requirements.txt requirements.txt
RUN pip install -r requirements.txt
COPY . .
# EXPOSE 8000
# CMD ["python", "simplifiedsdcambot.py"]