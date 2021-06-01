"""
2021-07-01
I think that this script was mostly done to test out whether I could access Grafana with the REST API.
I don't seriously think that it's an important thing to spend time on. Let's move on.
"""

import panel_total_gauges
import grafana_variables
import requests

def main():
    # f00()
    f01()

def f01():

    panel0 = panel_total_gauges.make_panel(
        id=1,
        cluster_name="mila",
        single_color="green",
        metric_name="slurm_gpus_total",
        title="Mila - GPUs total",
        gridPos=dict(h=8, w=3, x=0, y=0),
    )

    panel1 = panel_total_gauges.make_panel(
        id=2,
        cluster_name="mila",
        single_color="rgb(255, 128, 0)",
        metric_name="slurm_gpus_alloc",
        title="Mila - GPUs alloc",
        gridPos=dict(h=8, w=3, x=3, y=0),
    )

    panel2 = panel_total_gauges.make_panel(
        id=3,
        cluster_name="mila",
        single_color="rgb(51, 204, 204)",
        metric_name="slurm_gpus_idle",
        title="Mila - GPUs idle",
        gridPos=dict(h=8, w=3, x=6, y=0),
    )

    panel3 = panel_total_gauges.make_panel(
        id=4,
        cluster_name="mila",
        single_color="rgb(255, 51, 51)",
        metric_name="slurm_gpus_drain",
        title="Mila - GPUs down",
        gridPos=dict(h=8, w=3, x=9, y=0),
    )

    headers = { "Authorization": "Bearer eyJrIjoiZ0s0UHVZQ200bEJVOXVGc0JlckFlRjlzaTJWVDF6Q1UiLCJuIjoiYWRtaW4iLCJpZCI6MX0=",
                "Accept": "application/json",
                "Content-Type": "application/json"}
    resp = requests.post('http://deepgroove.local:3000/api/dashboards/db',
                    headers=headers,
                    json = {
                        "dashboard": {
                            "id": None,
                            "uid": None,
                            "title": "Mila cluster",
                            "tags": [ "mila_cluster", "slurm" ],
                            "timezone": "browser",
                            "schemaVersion": 16,
                            "refresh": "30s",
                            "panels": [panel0, panel1, panel2, panel3],
                            # this was lifted from an actual grafana panel made from GUI
                            "templating": {"list": [grafana_variables.get_gpu_types(["a100", "k80", "m40", "rtx8000", "titanrtx", "t4", "v100"])]}
                        },
                        "folderId": 5,
                        "overwrite": True
                    })
    print(resp.text)




def f00():

    headers = { "Authorization": "Bearer eyJrIjoiZ0s0UHVZQ200bEJVOXVGc0JlckFlRjlzaTJWVDF6Q1UiLCJuIjoiYWRtaW4iLCJpZCI6MX0=",
                "Accept": "application/json",
                "Content-Type": "application/json"}
    resp = requests.get('http://deepgroove.local:3000/api/folders', headers=headers)
    # '[{"id":5,"uid":"sifuuVeGk","title":"machine_populated"}]'

    # this required "json=" instead of "data=" because "data"
    # was supposed to be a string and not a dict
    resp = requests.post('http://deepgroove.local:3000/api/dashboards/db',
                    headers=headers,
                    json = {
                        "dashboard": {
                            "id": None,
                            "uid": None,
                            "title": "Production Overview",
                            "tags": [ "templated" ],
                            "timezone": "browser",
                            "schemaVersion": 16,
                            "version": 0,
                            "refresh": "25s"
                        },
                        "folderId": 5,
                        "message": "Made changes to xyz",
                        "overwrite": False
                    })
    #'{"id":7,"slug":"production-overview","status":"success","uid":"zLLf7I6Gz","url":"/d/zLLf7I6Gz/production-overview","version":1}'

if __name__ == "__main__":
    main()



"""
{
  "dashboard": {
    "id": null,
    "uid": null,
    "title": "Production Overview",
    "tags": [ "templated" ],
    "timezone": "browser",
    "schemaVersion": 16,
    "version": 0,
    "refresh": "25s"
  },
  "folderId": 5,
  "message": "Made changes to xyz",
  "overwrite": false
}
"""




"""
{
  "annotations": {
    "list": [
      {
        "builtIn": 1,
        "datasource": "-- Grafana --",
        "enable": true,
        "hide": true,
        "iconColor": "rgba(0, 211, 255, 1)",
        "name": "Annotations & Alerts",
        "type": "dashboard"
      }
    ]
  },
  "editable": true,
  "gnetId": null,
  "graphTooltip": 0,
  "id": 6,
  "links": [],
  "panels": [
      ...
  ],
  "schemaVersion": 27,
  "style": "dark",
  "tags": [],
  "templating": {
    "list": []
  },
  "time": {
    "from": "now-6h",
    "to": "now"
  },
  "timepicker": {},
  "timezone": "",
  "title": "New dashboard Copy",
  "uid": "hiTqX46Gz",
  "version": 1
}

"""