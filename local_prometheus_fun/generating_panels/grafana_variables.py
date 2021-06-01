import json

def get_gpu_types_00():
    return json.loads(
r"""
        {
          "allValue": null,
          "current": {
            "selected": true,
            "tags": [],
            "text": [
              "All"
            ],
            "value": [
              "$__all"
            ]
          },
          "datasource": null,
          "definition": "label_values(type)",
          "description": null,
          "error": null,
          "hide": 0,
          "includeAll": true,
          "label": "GPU Types",
          "multi": true,
          "name": "gpu_types",
          "options": [
            {
              "selected": true,
              "text": "All",
              "value": "$__all"
            },
            {
              "selected": false,
              "text": "a100",
              "value": "a100"
            },
            {
              "selected": false,
              "text": "k80",
              "value": "k80"
            },
            {
              "selected": false,
              "text": "m40",
              "value": "m40"
            },
            {
              "selected": false,
              "text": "rtx8000",
              "value": "rtx8000"
            },
            {
              "selected": false,
              "text": "t4",
              "value": "t4"
            },
            {
              "selected": false,
              "text": "titanrtx",
              "value": "titanrtx"
            },
            {
              "selected": false,
              "text": "v100",
              "value": "v100"
            }
          ],
          "query": {
            "query": "label_values(type)",
            "refId": "StandardVariableQuery"
          },
          "refresh": 0,
          "regex": "",
          "skipUrlSync": false,
          "sort": 0,
          "tagValuesQuery": "",
          "tags": [],
          "tagsQuery": "",
          "type": "query",
          "useTags": false
        }
""")


def get_gpu_types(gpu_types:list):
    """
    This is a template that offers just a little more flexibility because
    we don't necessarily have the same gpus on all the clusters.

    gpu_types expects an argument such as ["a100", "k80", "m40", "rtx8000", "titanrtx", "t4", "v100"]
    """
    E = json.loads(
r"""
        {
          "allValue": null,
          "current": {
            "selected": true,
            "tags": [],
            "text": [
              "All"
            ],
            "value": [
              "$__all"
            ]
          },
          "datasource": null,
          "definition": "label_values(type)",
          "description": null,
          "error": null,
          "hide": 0,
          "includeAll": true,
          "label": "GPU Types",
          "multi": true,
          "name": "gpu_types",
          "options": [
            {
              "selected": true,
              "text": "All",
              "value": "$__all"
            }
          ],
          "query": {
            "query": "label_values(type)",
            "refId": "StandardVariableQuery"
          },
          "refresh": 0,
          "regex": "",
          "skipUrlSync": false,
          "sort": 0,
          "tagValuesQuery": "",
          "tags": [],
          "tagsQuery": "",
          "type": "query",
          "useTags": false
        }
""")
    E["options"] = E["options"] + [
            {
              "selected": False,
              "text": g,
              "value": g
            }
            for g in gpu_types
    ]
    return E