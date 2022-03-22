FROM python:3.9-slim-buster

RUN mkdir /clockwork

ENV CLOCKWORK_ROOT=/clockwork
ENV PYTHONPATH=${PYTHONPATH}:${CLOCKWORK_ROOT}

WORKDIR ${CLOCKWORK_ROOT}

RUN pip install --upgrade pip

COPY slurm_state/requirements.txt /requirements_state.txt
RUN pip install -r /requirements_state.txt && rm -rf /root/.cache

COPY slurm_state_test/requirements.txt /requirements_state_test.txt
RUN pip install -r /requirements_state_test.txt && rm -rf /root/.cache

CMD ["coverage", "run", "--source=slurm_state", "--rcfile=slurm_state_test/.coveragerc", "-m", "pytest", "slurm_state_test"]