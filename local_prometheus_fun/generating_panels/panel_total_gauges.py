
import json

def make_panel(
    cluster_name:str="mila",
    single_color:str="green",
    reservation:str="None",
    metric_name:str="slurm_gpus_total",
    **kwargs):
    """
    kwargs probably should have "gridPos", "id", "title", and nothing else

    single_color can be something like "rgb(150, 0, 100)"
    or a color name that grafana recognizes
    """
    panel_desc = get_template()
    panel_desc["fieldConfig"]["defaults"]["thresholds"]["steps"][0]["color"] = single_color

    for (k, v) in kwargs.items():
        assert k in ['gridPos', 'id', 'title']
        panel_desc[k] = v

    # Might as well recreate it here.
    panel_desc["targets"][0]["expr"] = '%s{type=~"$gpu_types",reservation="%s",cluster_name="%s"}' % (metric_name, reservation, cluster_name)
    return panel_desc


def get_template():
    return json.loads(r"""
{
    "fieldConfig": {
      "defaults": {
        "thresholds": {
          "mode": "absolute",
          "steps": [
            {
              "color": "green",
              "value": null
            }
          ]
        },
        "mappings": [],
        "color": {
          "mode": "thresholds"
        }
      },
      "overrides": []
    },
    "gridPos": {
      "h": 9,
      "w": 8,
      "x": 8,
      "y": 0
    },
    "id": 3,
    "options": {
      "reduceOptions": {
        "values": false,
        "calcs": [
          "lastNotNull"
        ],
        "fields": ""
      },
      "orientation": "horizontal",
      "text": {},
      "displayMode": "basic",
      "showUnfilled": true
    },
    "pluginVersion": "7.5.7",
    "targets": [
      {
        "expr": "slurm_gpus_total{type=~\"$gpu_types\",reservation=\"None\",cluster_name=\"beluga\"}",
        "legendFormat": "{{type}}",
        "interval": "",
        "exemplar": true,
        "refId": "A"
      }
    ],
    "title": "GPUs total on beluga cluster",
    "type": "bargauge",
    "timeFrom": null,
    "timeShift": null,
    "datasource": null
  }
""")