FROM clockwork_web

COPY requirements.txt /requirements_web_test.txt
RUN pip install -r /requirements_web_test.txt && rm -rf /root/.cache

ENV CLOCKWORK_ENABLE_TESTING_LOGIN="True"

CMD ["coverage", "run", "--source=clockwork_web", "--rcfile=clockwork_web_test/.coveragerc", "-m", "pytest", "clockwork_web_test"]
