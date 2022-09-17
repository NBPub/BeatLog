FROM python:alpine
RUN apk --no-cache add curl tzdata libpq
WORKDIR /app

COPY requirements.txt .
RUN pip install --upgrade pip 
RUN pip install -r requirements.txt

COPY /BeatLog/ ./beatlog

ENTRYPOINT flask run

EXPOSE 5000