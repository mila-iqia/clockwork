REST API quick reference
========================

Accessible with external request authenticated with CLOCKWEB_WEB_API key
------------------------------------------------------------------------

Those are accessible with the clockwork_tools module,
but they can also be reached with cURL, Postman, or other tools
to connect to REST endpoints.

..
   Comment: When you edit the :endpoints: entries below, keep in mind that
   the notation is a bit convoluted. It's a combination of the blueprint name
   at the time it's defined and not the time when it's added to the main app.
   Then it's followed by the name of the python function that defines the route inside
   the source code, and not the "path" given to it.

.. qrefflask:: clockwork_web.main:app
   :undoc-static:
   :endpoints: rest_jobs.route_api_v1_jobs_list, rest_jobs.route_api_v1_jobs_one, rest_nodes.route_api_v1_nodes_list, rest_nodes.route_api_v1_nodes_one

Accessible in browser authenticated with session cookie
-------------------------------------------------------

Those would usually be accessed by clicking on the web interface.

.. qrefflask:: clockwork_web.main:app
   :undoc-static:
   :endpoints: nodes.route_list, nodes.route_one, jobs.route_list, jobs.route_one, jobs.route_single_job_p_job_id
   
   
   