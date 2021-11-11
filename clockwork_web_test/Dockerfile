FROM clockwork_web

COPY requirements.txt /requirements_web.txt
RUN pip install -r /requirements_web.txt && rm -rf /root/.cache

CMD ["pytest"]