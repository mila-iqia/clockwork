
/*
    Two main functions :
        // async call, fetches data from server
        launch_refresh_all_data()

        // uses global variables, does not fetch data
        refresh_display(display_filter)
*/

// We set up a request to retrieve the jobs list as JSON
const refresh_endpoint = "/jobs/list?want_json=True"

// This id is used to identify the table to populate in the associated HTML file
const id_of_table_to_populate = "table_98429387" // hardcoded into jobs.html also

/*  The point of having those two global variables
    is that you can externally call `refresh_display(display_filter)`.
    It's not nice to deal with global variables, but the alternative
    is that we export more of the arbitrary stuff to the outside.
*/

var latest_response_contents; // Stores the content of the latest response received
var latest_filtered_response_contents; // Results in applying filters on the latest response contents



function launch_refresh_all_data(query_filter, display_filter) {
    /*
        We just clicked on "refresh", or maybe we have freshly loaded
        the page and need to create the table for the first time.

        // things that affect the data fetched
        query_filter = {
            "user": "all", // or specific user
            "time": 3600, // int, for number of seconds to go backwards
        }

        // things that we toggle in the interface
        display_filter = {
            "cluster_name": {
                "mila": true,
                "beluga": true,
                "cedar": true,
                "graham": true
            },
            "job_state": {
                "PENDING": true,
                "RUNNING": true,
                "COMPLETING": true,
                "COMPLETED": true,
                "OUT_OF_MEMORY": true,
                "TIMEOUT": true,
                "FAILED": true,
                "CANCELLED": true
            }
        }

        Keep in mind that any REST API call made here is done
        under the identity of the authenticated user so we don't need
        to worry about identification. The user cookie is passed automatically
        in the headers.
    */

    let url = refresh_endpoint;
    // If a user is specified, add its username to the request
    if (query_filter["user"].localeCompare("all") != 0) {
      url = url + "&user=" + query_filter["user"];
    };

    // Send the request, and retrieve the response
    const request = new Request(url,
        {   method: 'GET',
            headers: {
                'Content-Type': 'application/json'
            }
        });
    fetch(request)
    .then(response => {
        if (response.status === 200) {
            return response.json();
        } else {
            throw new Error('Something went wrong on api server!');
        }
    })
    .then(response_contents => {
        latest_response_contents = response_contents;
        refresh_display(display_filter);
    }).catch(error => {
        console.error(error);
    });
};

function refresh_display(display_filter) {
    /*
        Clear and populate the jobs table with the latest response content,
        filtered by the "display filters" given as parameters.
    */
    latest_filtered_response_contents = apply_filter(latest_response_contents, display_filter);
    vacate_table(); // idempotent if not table is present
    populate_table(latest_filtered_response_contents);
}



/*
    Helpers:
        retrieve_username_from_email(email)
        removeAllChildNodes(parent)
        vacate_table()
        populate_table(response_contents)
        apply_filter(response_contents, display_filter)
*/


// https://www.javascripttutorial.net/dom/manipulating/remove-all-child-nodes/
function removeAllChildNodes(parent) {
    while (parent.firstChild) {
        parent.removeChild(parent.firstChild);
    }
}


function vacate_table() {
    // mix of
    //    https://stackoverflow.com/questions/14094697/how-to-create-new-div-dynamically-change-it-move-it-modify-it-in-every-way-po
    //    https://stackoverflow.com/questions/24775725/loop-through-childnodes

    let table = document.getElementById(id_of_table_to_populate);

    /*  Everyone says that this can cause problems with parsing the DOM again,
        but given how many removals we need to do, it seems like it's cheap
        comparatively to removing every one of the 1000 rows.

        They also say that it can leak memory if there are handlers in the elements
        removed, but I don't think we've put anything in particular there.
        We might need to do some profiling later, and revisit this.
    */
    table.innerHTML = "";
    //removeAllChildNodes(table);
    /*
    [].forEach.call(table.children, function(child) {
        table.removeChild(child);
    });
    */
}

function apply_filter(response_contents, display_filter) {

    /*  Since `display_filter` has two dicts that contain (str, bool),
        this makes it very easy to check if, for example,
            when D_job["cluster_name"] is "mila"
            is display_filter["cluster_name"]["mila"] true ?
        We do it for "cluster_name" and "job_state".

        Note that "job_state" is one of 8 possible strings in UPPERCASE,
        and not the projection down to 4 states that we use for toggle switches.
    */

    return response_contents.filter( D_job => {
        return display_filter["cluster_name"][D_job["slurm"]["cluster_name"]] && display_filter["job_state"][D_job["slurm"]["job_state"]]
    });
    //return response_contents;
}


function populate_table(response_contents) {
    /*
        `response_contents` here is a list of dict with fields
            'slurm': {
                        'cluster_name': ... ,
                        'username': ... ,
                        'job_id': ... ,
                        'name': ... ,
                        ...
                    },
            'cw': {
                    ...
                  }


          For now, we mainly display the "slurm" informations of each job
            <td>{{e['cluster_name']}}</td>
            <td><a href="/jobs/list/{{e['username']}}"> {{e['username']}} </a></td>
            <td><a href="/jobs/one?job_id={{e['job_id']}}"> {{e['job_id']}} </a></td>
            <td>{{e.get('name', "")[:32]}}</td> <!-- truncate after 32 chars -->
            <td>{{e['job_state']}}</td>
    */

    let table = document.getElementById(id_of_table_to_populate);

    /* create the table header */
    let thead = document.createElement('thead');
    let tr = document.createElement('tr');
    let th;
    th = document.createElement('th'); th.innerHTML = "cluster"; tr.appendChild(th);
    th = document.createElement('th'); th.innerHTML = "user"; tr.appendChild(th);
    th = document.createElement('th'); th.innerHTML = "job_id"; tr.appendChild(th);
    th = document.createElement('th'); th.innerHTML = "job name [:20]"; tr.appendChild(th);
    th = document.createElement('th'); th.innerHTML = "job_state"; tr.appendChild(th);
    th = document.createElement('th'); th.innerHTML = "start time"; tr.appendChild(th);
    th = document.createElement('th'); th.innerHTML = "end time"; tr.appendChild(th);
    thead.appendChild(tr);
    table.appendChild(thead);

    let tbody = document.createElement('tbody');
    /* then add the information for all the jobs */
    [].forEach.call(response_contents, function(D_job) {
        D_job_slurm = D_job["slurm"];
        let tr = document.createElement('tr');
        let td;
        td = document.createElement('td'); td.innerHTML = D_job_slurm["cluster_name"]; tr.appendChild(td);
        td = document.createElement('td'); td.innerHTML = retrieve_username_from_email(D_job["cw"]["mila_email_username"]); tr.appendChild(td); // TODO : add href for meaningful people pertaining to single user ?
        td = document.createElement('td'); td.innerHTML = (
            "<a href=\"" + "/jobs/one?job_id=" + D_job_slurm["job_id"] + "\">" + D_job_slurm["job_id"] + "</a>"); tr.appendChild(td);
        td = document.createElement('td'); td.innerHTML = (D_job_slurm["name"] ? D_job_slurm["name"] : "").substring(0, 20); tr.appendChild(td);  // truncated after 20 characters (you can change this magic number if you want)
        td = document.createElement('td'); td.innerHTML = D_job_slurm["job_state"]; tr.appendChild(td);

        // start time
        td = document.createElement('td');
        if (D_job_slurm["start_time"] == null) {
            td.innerHTML = "";
        } else {
            // If you want to display the time as "2021-07-06 22:19:46" for readability
            // you need to set it up because this is going to be written as a unix timestamp.
            // This might include injecting another field with a name
            // such as "start_time_human_readable" or something like that, and using it here.
            td.innerHTML = D_job_slurm["start_time"].toString();
        }
        tr.appendChild(td);

        // end time
        td = document.createElement('td');
        if (D_job_slurm["end_time"] == null) {
            td.innerHTML = "";
        } else {
            // If you want to display the time as "2021-07-06 22:19:46" for readability
            // you need to set it up because this is going to be written as a unix timestamp.
            // This might include injecting another field with a name
            // such as "start_time_human_readable" or something like that, and using it here.
            td.innerHTML = D_job_slurm["end_time"].toString();
        }
        tr.appendChild(td);


        tbody.appendChild(tr);

    });
    table.appendChild(tbody);

    /* some of that can be used for adding the href back in the code above
        let td0 = document.createElement('td');
            let url = "../../../joplin_live/arcanix/note/" + note_info["jid"];
            td0.innerHTML = "<a href=\"" + url + "\">" + note_info["title"] + "</a>";
            */

}

function retrieve_username_from_email(email) {
    /*
        Retrieve the first part of the email identifying a user.

        The format of an input email is:
        firstname.name@mila.quebec

        The expected result for this function is:
        firstname.name
        (or more generally the party before the @)
    */
    if (email !== null) {
        const parsed_email = email.split("@");
        return parsed_email[0];
    }
    else {
      return "";
    }
}
