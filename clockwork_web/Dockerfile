FROM python:3.9-slim-buster

RUN mkdir /clockwork

ENV CLOCKWORK_ROOT=/clockwork
ENV PYTHONPATH=${PYTHONPATH}:${CLOCKWORK_ROOT}

WORKDIR ${CLOCKWORK_ROOT}

ENV FLASK_APP=clockwork_web.main:app
ENV MONGODB_DATABASE_NAME="clockwork"

RUN pip install --upgrade pip

RUN apt-get update && apt-get install -y --no-install-recommends git
RUN pip install -e git+https://github.com/maxcountryman/flask-login.git#egg=flask-login
# python3 -m pip install -e git+https://github.com/maxcountryman/flask-login.git#egg=flask-login
COPY requirements.txt /requirements_web.txt
RUN pip install -r /requirements_web.txt && rm -rf /root/.cache

COPY entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

ENTRYPOINT ["/entrypoint.sh"]
