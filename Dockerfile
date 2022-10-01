FROM python:alpine
RUN apk --no-cache add curl tzdata libpq
WORKDIR /app

COPY requirements.txt .
RUN pip install --upgrade pip && pip install -r requirements.txt && pip install gunicorn

COPY /BeatLog/ ./beatlog

ENTRYPOINT gunicorn -w 3 -b 0.0.0.0:8000 --preload 'beatlog:create_app()'