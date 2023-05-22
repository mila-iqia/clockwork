FROM python:3.9-slim-buster

RUN mkdir /clockwork
# Create folder required by Playwright to install browsers,
# and set permissions so that Playwright can install browsers in these folders.
RUN mkdir /.cache
RUN chmod -R 777 /.cache
RUN chmod -R 777 /clockwork

# Add a variable available only inside container.
ENV WE_ARE_IN_DOCKER=1

ENV CLOCKWORK_ROOT=/clockwork
ENV PYTHONPATH=${PYTHONPATH}:${CLOCKWORK_ROOT}:${CLOCKWORK_ROOT}/clockwork_tools

WORKDIR ${CLOCKWORK_ROOT}

ENV FLASK_APP=clockwork_web.main:app
ENV CLOCKWORK_ENABLE_TESTING_LOGIN=True
ENV MONGODB_DATABASE_NAME="clockwork"

# to have gcc to build `dulwich` used by poetry
RUN apt update && apt install -y build-essential

# Install OS packages required for Playwright browsers
# https://github.com/microsoft/playwright-python/issues/498#issuecomment-856349356
RUN apt install -y gstreamer1.0-libav libnss3-tools libatk-bridge2.0-0 libcups2-dev libxkbcommon-x11-0 libxcomposite-dev libxrandr2 libgbm-dev libgtk-3-0

RUN pip install --upgrade pip poetry

COPY clockwork_web/requirements.txt /requirements_web.txt
RUN pip install -r /requirements_web.txt && rm -rf /root/.cache

COPY clockwork_web_test/requirements.txt /requirements_web_test.txt
RUN pip install -r /requirements_web_test.txt && rm -rf /root/.cache

# Install Python requirements for clockwork frontend/javascript tests.
# This include package `pytest-playwright`.
COPY clockwork_frontend_test/requirements.txt /requirements_frontend_test.txt
RUN pip install -r /requirements_frontend_test.txt && rm -rf /root/.cache

COPY clockwork_tools/poetry.lock /poetry.lock
COPY clockwork_tools/pyproject.toml /pyproject.toml
RUN cd / && poetry env use system && poetry install --no-root && rm -rf /root/.cache

COPY clockwork_tools_test/requirements.txt /requirements_tools_test.txt
RUN pip install -r /requirements_tools_test.txt && rm -rf /root/.cache

COPY slurm_state/requirements.txt /requirements_state.txt
RUN pip install -r /requirements_state.txt && rm -rf /root/.cache

COPY slurm_state_test/requirements.txt /requirements_state_test.txt
RUN pip install -r /requirements_state_test.txt && rm -rf /root/.cache

COPY scripts/requirements.txt /requirements_scripts.txt
RUN pip install -r /requirements_scripts.txt && rm -rf /root/.cache

COPY entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

ENTRYPOINT ["/entrypoint.sh"]
