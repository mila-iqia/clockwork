set -eu

echo Install playwright browser Chromium
playwright install chromium

echo Store fake data
python3 scripts/store_fake_data_in_db.py

echo Launch clockwork web server in background
python3 -m flask run --host="0.0.0.0" &

echo Wait 5 seconds to let server fully start
sleep 5

echo Check that server is onlinw
python -c "import urllib.request; print(urllib.request.urlopen('http://127.0.0.1:5000/').getcode())"

echo Run tests
pytest -vv clockwork_frontend_test

echo Frontend tests done.
