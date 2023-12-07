FROM clockwork_web

# Create folder required by Playwright to install browsers
# and set permissions so that Playwright can install browsers in this folder
RUN mkdir /.cache
RUN chmod -R 776 /.cache

RUN apt update && apt install -y build-essential

# Install OS packages required for Playwright browsers
# https://github.com/microsoft/playwright-python/issues/498#issuecomment-856349356
RUN apt install -y gstreamer1.0-libav libnss3-tools libatk-bridge2.0-0 libcups2-dev libxkbcommon-x11-0 libxcomposite-dev libxrandr2 libgbm-dev libgtk-3-0

# Install Python requirements for clockwork frontend/javascript tests.
# This include package `pytest-playwright`.
COPY clockwork_frontend_test/requirements.txt /requirements_frontend_test.txt
RUN pip install -r /requirements_frontend_test.txt && rm -rf /root/.cache

# Add a variable available only inside container.
ENV WE_ARE_IN_DOCKER=1
ENV CLOCKWORK_ENABLE_TESTING_LOGIN="True"

CMD ["bash", "clockwork_frontend_test/launch_frontend_tests_in_clockwork_dev.sh"]

