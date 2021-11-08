# The tests should not require that the server is in the same container, but they do.
FROM clockwork_web_test

COPY clockwork_tools/requirements.txt /requirements_tools.txt
RUN pip install -r /requirements_tools.txt && rm -rf /root/.cache

COPY clockwork_tools_test/requirements.txt /requirements_tools_test.txt
RUN pip install -r /requirements_tools_test.txt && rm -rf /root/.cache

COPY clockwork_tools_test/run.sh /clockwork/run.sh
CMD ["bash", "run.sh"]