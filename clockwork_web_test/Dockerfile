FROM clockwork_web

COPY requirements.txt /requirements_web_test.txt
RUN pip install -r /requirements_web_test.txt && rm -rf /root/.cache

CMD ["pytest"]