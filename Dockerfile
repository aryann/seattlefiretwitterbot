FROM python:3.7-slim

ENV APP_HOME /app
WORKDIR $APP_HOME
COPY . ./

RUN pip install \
  Flask \
  gunicorn \
  python-twitter \
  requests

CMD exec gunicorn \
  --bind=":$PORT" \
  --workers=1 \
  --threads=4 \
  --timeout=0 \
  --log-file=- \
  reconciler:app
  