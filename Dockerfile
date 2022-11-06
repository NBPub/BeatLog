FROM python:alpine
RUN apk --no-cache add curl tzdata libpq
WORKDIR /app

COPY requirements.txt .
RUN pip install --upgrade pip setuptools wheel && pip install -r requirements.txt && pip install gunicorn

COPY /BeatLog/ ./beatlog

ENTRYPOINT gunicorn -w 3 -t 60 -b 0.0.0.0:8000 --preload 'beatlog:create_app()'