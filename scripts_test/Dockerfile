FROM python:3.9-slim-buster

RUN mkdir /clockwork

ENV CLOCKWORK_ROOT=/clockwork
ENV PYTHONPATH=${PYTHONPATH}:${CLOCKWORK_ROOT}

WORKDIR ${CLOCKWORK_ROOT}

RUN pip install --upgrade pip

COPY scripts/requirements.txt /requirements_scripts.txt
RUN pip install -r /requirements_scripts.txt && rm -rf /root/.cache

COPY scripts_test/requirements.txt /requirements_scripts_test.txt
RUN pip install -r /requirements_scripts_test.txt && rm -rf /root/.cache

# Add folder `slurm_state` so that `slurm_state` symbols are available during tests.
# `slurm_state` symbols get_mongo_client() and get_config() are used in script `cleanup_jobs`.
ADD slurm_state slurm_state

CMD ["coverage", "run", "--source=scripts", "--rcfile=scripts_test/.coveragerc", "-m", "pytest", "scripts_test"]
