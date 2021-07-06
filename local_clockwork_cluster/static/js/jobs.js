

//const refresh_endpoint = "/api/0/list_jobs"
const refresh_endpoint = "/jobs/api/list"  // needs to be more principled, but let's design that better later

const id_of_table_to_populate = "table_98429387" // hardcoded into jobs.html also

/*
    Two main functions (async calls) :
        launch_refresh_all_data
*/

function launch_refresh_all_data() {
    /*
        We just clicked on "refresh", or maybe we have freshly loaded
        the page and need to create the table for the first time.

        Keep in mind that any REST API call made here is done
        under the identity of the authenticated user so we don't need
        to worry about identification. The user cookie is passed automatically
        in the headers.
    */
    let url = refresh_endpoint;
    const request = new Request(url,
        {   method: 'POST',
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
        vacate_table(); // idempotent if not table is present
        populate_table(response_contents)
    }).catch(error => {
        console.error(error);
    });
};


/*
    Helpers:
        
        vacate_table()
        populate_table(response_contents)
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
    removeAllChildNodes(table);
    /*
    [].forEach.call(table.children, function(child) {
        table.removeChild(child);
    });
    */
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
