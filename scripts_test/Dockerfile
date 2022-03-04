FROM python:3.9-slim-buster

RUN mkdir /clockwork

ENV CLOCKWORK_ROOT=/clockwork
ENV PYTHONPATH=${PYTHONPATH}:${CLOCKWORK_ROOT}

WORKDIR ${CLOCKWORK_ROOT}

ENV MONGODB_DATABASE_NAME="clockwork"

RUN pip install --upgrade pip

COPY scripts/requirements.txt /requirements_scrips.txt
RUN pip install -r /requirements_scrips.txt && rm -rf /root/.cache

COPY scripts_test/requirements.txt /requirements_scripts_test.txt
RUN pip install -r /requirements_scripts_test.txt && rm -rf /root/.cache

CMD ["coverage", "run", "--source=scripts", "--rcfile=scripts_test/.coveragerc", "-m", "pytest", "scripts_test"]
