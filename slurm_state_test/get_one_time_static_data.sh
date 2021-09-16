
python3 remote_scan.py --cluster_desc=cluster_desc/mila.json   --write_data_to_file=static_data/mila_data.json
python3 remote_scan.py --cluster_desc=cluster_desc/beluga.json --write_data_to_file=static_data/beluga_data.json
python3 remote_scan.py --cluster_desc=cluster_desc/cedar.json  --write_data_to_file=static_data/cedar_data.json
python3 remote_scan.py --cluster_desc=cluster_desc/graham.json --write_data_to_file=static_data/graham_data.json

python3 anonymize_static_data.py static_data/mila_data.json   static_data/mila_data_anon.json 
python3 anonymize_static_data.py static_data/beluga_data.json static_data/beluga_data_anon.json 
python3 anonymize_static_data.py static_data/cedar_data.json  static_data/cedar_data_anon.json 
python3 anonymize_static_data.py static_data/graham_data.json static_data/graham_data_anon.json 
