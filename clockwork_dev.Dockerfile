FROM python:3.9-slim-buster

RUN mkdir /clockwork

ENV CLOCKWORK_ROOT=/clockwork
ENV PYTHONPATH=${PYTHONPATH}:${CLOCKWORK_ROOT}:${CLOCKWORK_ROOT}/clockwork_tools

WORKDIR ${CLOCKWORK_ROOT}

ENV FLASK_APP=clockwork_web.main:app
ENV CLOCKWORK_ENABLE_TESTING_LOGIN=True
ENV MONGODB_DATABASE_NAME="clockwork"

RUN pip install --upgrade pip poetry

COPY clockwork_web/requirements.txt /requirements_web.txt
RUN pip install -r /requirements_web.txt && rm -rf /root/.cache

COPY clockwork_web_test/requirements.txt /requirements_web_test.txt
RUN pip install -r /requirements_web_test.txt && rm -rf /root/.cache

COPY clockwork_tools/poetry.lock /poetry.lock
COPY clockwork_tools/pyproject.toml /pyproject.toml
RUN cd / && poetry env use system && poetry install --no-root && rm -rf /root/.cache

COPY clockwork_tools_test/requirements.txt /requirements_tools_test.txt
RUN pip install -r /requirements_tools_test.txt && rm -rf /root/.cache

COPY slurm_state/requirements.txt /requirements_state.txt
RUN pip install -r /requirements_state.txt && rm -rf /root/.cache

COPY slurm_state_test/requirements.txt /requirements_state_test.txt
RUN pip install -r /requirements_state_test.txt && rm -rf /root/.cache

COPY entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

ENTRYPOINT ["/entrypoint.sh"]
