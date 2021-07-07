
/*
    Two main functions :
        // async call, fetches data from server
        launch_refresh_all_data()  

        // uses global variables, does not fetch data
        refresh_display(display_filter)  
*/



//const refresh_endpoint = "/api/0/list_jobs"
const refresh_endpoint = "/jobs/api/list"  // hardcoded into job_routes.py

const id_of_table_to_populate = "table_98429387" // hardcoded into jobs.html also

/*  The point of having those two global variables
    is that you can call externally call `refresh_display(display_filter)`.
    It's not nice to deal with global variables, but the alternative
    is that we export more of the arbitrary stuff to the outside.
 */

var latest_response_contents;
var latest_filtered_response_contents;



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
    const request = new Request(url,
        {   method: 'POST',
            body: JSON.stringify({
                    "query_filter" : query_filter,
                }),
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
    latest_filtered_response_contents = apply_filter(latest_response_contents, display_filter);
    vacate_table(); // idempotent if not table is present
    populate_table(latest_filtered_response_contents);
}



/*
    Helpers:
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
        return display_filter["cluster_name"][D_job["cluster_name"]] && display_filter["job_state"][D_job["job_state"]]
    });
    //return response_contents;
}


function populate_table(response_contents) {
    /* 
        `response_contents` here is a list of dict with fields 
            {
                'cluster_name': ... ,
                'best_guess_for_username': ... ,
                'job_id': ... ,
                'name': ... ,
                ...
            }

            <td>{{e['cluster_name']}}</td>
            <td><a href="/jobs/list/{{e['best_guess_for_username']}}"> {{e['best_guess_for_username']}} </a></td>
            <td><a href="/jobs/single_job/{{e['job_id']}}"> {{e['job_id']}} </a></td>
            <td>{{e.get('name', "")[:32]}}</td> <!-- truncate after 32 chars -->
            <td>{{e['job_state']}}</td>
    */

    let table = document.getElementById(id_of_table_to_populate);

    /* create the table header */
    let thead = document.createElement('thead');
    let tr = document.createElement('tr');
    let th;
    th = document.createElement('th'); th.innerHTML = "cluster_name"; tr.appendChild(th);
    th = document.createElement('th'); th.innerHTML = "username (best guess)"; tr.appendChild(th);
    th = document.createElement('th'); th.innerHTML = "job_id"; tr.appendChild(th);
    th = document.createElement('th'); th.innerHTML = "job name (truncated)"; tr.appendChild(th);
    th = document.createElement('th'); th.innerHTML = "job_state"; tr.appendChild(th);
    thead.appendChild(tr);
    table.appendChild(thead);

    let tbody = document.createElement('tbody');
    /* then add the information for all the jobs */
    [].forEach.call(response_contents, function(D_job) {

        let tr = document.createElement('tr');
        let td;
        td = document.createElement('td'); td.innerHTML = D_job["cluster_name"]; tr.appendChild(td);
        td = document.createElement('td'); td.innerHTML = D_job["best_guess_for_username"]; tr.appendChild(td); // TODO : add href
        td = document.createElement('td'); td.innerHTML = D_job["job_id"]; tr.appendChild(td); // TODO : add href
        td = document.createElement('td'); td.innerHTML = D_job["name"].substring(0, 32); tr.appendChild(td);  // truncated after 32 characters (you can change this magic number if you want)
        td = document.createElement('td'); td.innerHTML = D_job["job_state"]; tr.appendChild(td);
        tbody.appendChild(tr);

    });
    table.appendChild(tbody);

    /* some of that can be used for adding the href back in the code above
        let td0 = document.createElement('td');
            let url = "../../../joplin_live/arcanix/note/" + note_info["jid"];
            td0.innerHTML = "<a href=\"" + url + "\">" + note_info["title"] + "</a>";
            */

}
