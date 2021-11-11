FROM python:3.9-slim-buster

RUN mkdir /clockwork

ENV CLOCKWORK_ROOT=/clockwork
ENV PYTHONPATH=${PYTHONPATH}:${CLOCKWORK_ROOT}

WORKDIR ${CLOCKWORK_ROOT}

ENV MONGODB_DATABASE_NAME="clockwork"

RUN pip install --upgrade pip

COPY clockwork_tools/requirements.txt /requirements_tools.txt
RUN pip install -r /requirements_tools.txt && rm -rf /root/.cache

COPY clockwork_tools_test/requirements.txt /requirements_tools_test.txt
RUN pip install -r /requirements_tools_test.txt && rm -rf /root/.cache

CMD ["pytest"]
