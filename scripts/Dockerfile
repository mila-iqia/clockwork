FROM python:3.9-slim-buster

RUN mkdir /clockwork

ENV CLOCKWORK_ROOT=/clockwork
ENV PYTHONPATH=${PYTHONPATH}:${CLOCKWORK_ROOT}

WORKDIR ${CLOCKWORK_ROOT}

ENV MONGODB_DATABASE_NAME="clockwork"

RUN pip install --upgrade pip

# Copy the required folders and install their requirements
COPY scripts /clockwork/scripts
COPY slurm_state /clockwork/slurm_state
RUN pip install -r /clockwork/slurm_state/requirements.txt && rm -rf /root/.cache

ENTRYPOINT cd /clockwork/scripts ; bash produce_fake_data.sh
