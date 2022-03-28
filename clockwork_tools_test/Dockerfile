FROM python:3.9-slim-buster

RUN mkdir /clockwork

ENV CLOCKWORK_ROOT=/clockwork
ENV PYTHONPATH=${PYTHONPATH}:${CLOCKWORK_ROOT}

WORKDIR ${CLOCKWORK_ROOT}

ENV MONGODB_DATABASE_NAME="clockwork"

RUN pip install --upgrade pip
COPY clockwork_tools clockwork_tools
RUN pip install -e ./clockwork_tools && rm -rf /root/.cache

COPY clockwork_tools_test/requirements.txt /requirements_tools_test.txt
RUN pip install -r /requirements_tools_test.txt && rm -rf /root/.cache

CMD ["coverage", "run", "--source=clockwork_tools/clockwork_tools", "--rcfile=clockwork_tools_test/.coveragerc", "-m", "pytest", "clockwork_tools_test"]
