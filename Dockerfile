FROM python:3.11-alpine
RUN apk --no-cache add curl tzdata libpq
WORKDIR /app

RUN pip install --upgrade pip setuptools wheel && pip install Flask python-dotenv "psycopg[binary,pool]" Flask-APScheduler geoip2 gunicorn

COPY /BeatLog/ ./beatlog

ENTRYPOINT gunicorn -w 3 -t 60 -b 0.0.0.0:8000 --preload 'beatlog:create_app()'