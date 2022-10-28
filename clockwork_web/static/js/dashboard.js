
/*
    Two main functions :
        // async call, fetches data from server
        launch_refresh_all_data()

        // uses global variables, does not fetch data
        refresh_display(display_filter)
*/

//date stuff
var TimeAgo = (function() {
var self = {};
  
  // Public Methods
self.locales = {
    prefix: '',
    sufix:  'ago',
    
    seconds: 'less than a minute',
    minute:  'about a minute',
    minutes: '%d minutes',
    hour:    'about an hour',
    hours:   'about %d hours',
    day:     'a day',
    days:    '%d days',
    month:   'about a month',
    months:  '%d months',
    year:    'about a year',
    years:   '%d years'
};
  
self.inWords = function(timeAgo) {
    var seconds = Math.floor((new Date() - parseInt(timeAgo)) / 1000),
        separator = this.locales.separator || ' ',
        words = this.locales.prefix + separator,
        interval = 0,
        intervals = {
          year:   seconds / 31536000,
          month:  seconds / 2592000,
          day:    seconds / 86400,
          hour:   seconds / 3600,
          minute: seconds / 60
    };
    
    var distance = this.locales.seconds;
    
    for (var key in intervals) {
        interval = Math.floor(intervals[key]);
      
        if (interval > 1) {
            distance = this.locales[key + 's'];
            break;
        } else if (interval === 1) {
            distance = this.locales[key];
            break;
        }
    }
    
        distance = distance.replace(/%d/i, interval);
        words += distance + separator + this.locales.sufix;

        return words.trim();
    };
  
    return self;
}());

// We set up a request to retrieve the jobs list as JSON
const refresh_endpoint = "/jobs/list?want_json=True"

// This id is used to identify the table to populate in the associated HTML file
const id_of_table_to_populate = "dashboard_table" // hardcoded into jobs.html also

/*  The point of having those two global variables
    is that you can externally call `refresh_display(display_filter)`.
    It's not nice to deal with global variables, but the alternative
    is that we export more of the arbitrary stuff to the outside.
*/

var latest_response_contents; // Stores the content of the latest response received
var latest_filtered_response_contents; // Results in applying filters on the latest response contents

function format_date(timestamp) {
    /*
        Format a timestamp in order to display it in the following format:
        yyyy-mm-dd HH:MM
    */
    let date_to_format = new Date(timestamp*1000); // The timestamp should be in milliseconds, not in seconds

    // Format each element
    year = date_to_format.getFullYear();
    month = (date_to_format.getMonth()+1).toLocaleString('en-US', {minimumIntegerDigits: 2, useGrouping:false}); // Months are represented by indices from 0 to 11. Thus, 1 is added to the month. Moreover, this use of 'toLocaleString' is used to display each month with two digits (even the months from 1 to 9)
    day = date_to_format.getDate().toLocaleString('en-US', {minimumIntegerDigits: 2, useGrouping:false}); // This use of 'toLocaleString' is used to display each day with two digits (even the days from 1 to 9)

    hours = date_to_format.getHours().toLocaleString('en-US', {minimumIntegerDigits: 2, useGrouping:false}); // This use of 'toLocaleString' is used to display each hour with two digits (even the hours from 0 to 9)
    minutes = date_to_format.getMinutes().toLocaleString('en-US', {minimumIntegerDigits: 2, useGrouping:false}); // This use of 'toLocaleString' is used to display the minutes with two digits (even when there is less than 10 minutes in the current hour)

    return `${year}-${month}-${day} ${hours}:${minutes}`;
}

function launch_refresh_all_data(query_filter, display_filter) {
    /*
        We just clicked on "refresh", or maybe we have freshly loaded
        the page and need to create the table for the first time.

        // things that affect the data fetched
        query_filter = {
            "username": "all", // or specific username
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
                "CANCELLED": true,
                "PREEMPTED": true,
            }
        }

        Keep in mind that any REST API call made here is done
        under the identity of the authenticated user so we don't need
        to worry about identification. The user cookie is passed automatically
        in the headers.
    */

    let url = refresh_endpoint;
    // If a user is specified, add its username to the request
    if (query_filter["username"].localeCompare("all") != 0) {
      url = url + "&username=" + query_filter["username"];
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
    latest_filtered_response_contents = apply_filter(latest_response_contents["jobs"], display_filter);
    vacate_table(); // idempotent if not table is present
    populate_table(latest_filtered_response_contents);
    //kaweb - for some reason, the sortable init only works on reload/first load, not after changing filters
    Sortable.init();
    //kaweb - tooltips work though
    var tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'))
    var tooltipList = tooltipTriggerList.map(function (tooltipTriggerEl) {
      return new bootstrap.Tooltip(tooltipTriggerEl)
    });
    //kaweb - attempt to count results
    count_jobs(latest_filtered_response_contents);
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
    th = document.createElement('th'); th.innerHTML = "Cluster"; tr.appendChild(th);
    th = document.createElement('th'); th.innerHTML = "Job ID"; tr.appendChild(th);
    th = document.createElement('th'); th.innerHTML = "Job name [:20]"; tr.appendChild(th);
    th = document.createElement('th'); th.innerHTML = "Job state"; tr.appendChild(th);
    th = document.createElement('th'); th.innerHTML = "Start time"; tr.appendChild(th);
    th = document.createElement('th'); th.innerHTML = "End time"; tr.appendChild(th);
    th = document.createElement('th'); th.innerHTML = "Links"; th.setAttribute("data-sortable", "false"); tr.appendChild(th);
    th = document.createElement('th'); th.innerHTML = "Actions"; th.setAttribute("data-sortable", "false"); tr.appendChild(th);
    thead.appendChild(tr);
    table.appendChild(thead);

    let tbody = document.createElement('tbody');
    /* then add the information for all the jobs */
    [].forEach.call(response_contents, function(D_job) {
        D_job_slurm = D_job["slurm"];
        //kaweb - displaying the job state in lowercase to manipulate it in CSS
        job_state = D_job_slurm["job_state"].toLowerCase();
        let tr = document.createElement('tr');
        let td;
        td = document.createElement('td'); td.innerHTML = D_job_slurm["cluster_name"]; tr.appendChild(td);
        td = document.createElement('td'); td.innerHTML = (
            "<a href=\"" + "/jobs/one?job_id=" + D_job_slurm["job_id"] + "\">" + D_job_slurm["job_id"] + "</a>"); tr.appendChild(td);
        td = document.createElement('td'); td.innerHTML = (D_job_slurm["name"] ? D_job_slurm["name"] : "").substring(0, 20); tr.appendChild(td);  // truncated after 20 characters (you can change this magic number if you want)
        //td = document.createElement('td'); td.innerHTML = D_job_slurm["job_state"]; tr.appendChild(td);
        //kaweb - using the job state as a shorthand to insert icons through CSS
        td = document.createElement('td'); td.innerHTML = (
            "<span class=\"status " + job_state + "\">" + job_state + "</span>"); tr.appendChild(td);

        // start time
        td = document.createElement('td');
        if (D_job_slurm["start_time"] == null) {
            td.innerHTML = "";
        } else {
            // If you want to display the time as "2021-07-06 22:19:46" for readability
            // you need to set it up because this is going to be written as a unix timestamp.
            // This might include injecting another field with a name
            // such as "start_time_human_readable" or something like that, and using it here.

            //td.innerHTML = D_job_slurm["start_time"].toString(); // For a timestamp
            //td.innerHTML = TimeAgo.inWords(Date.now() - D_job_slurm["start_time"]); // For a relative time
            td.innerHTML = format_date(D_job_slurm["start_time"]); // For a human readable time
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

            //td.innerHTML = D_job_slurm["end_time"].toString(); // For a timestamp
            //td.innerHTML = TimeAgo.inWords(Date.now() - D_job_slurm["start_time"]); // For a relative time
            td.innerHTML = format_date(D_job_slurm["end_time"]);
        }
        tr.appendChild(td);

        // links
        td = document.createElement('td'); 
        td.className = "links";
        td.innerHTML = (
            "<a href='' data-bs-toggle='tooltip' data-bs-placement='right' title='Link to somewhere'><i class='fa-solid fa-file'></i></a>"
            + 
            "<a href='' data-bs-toggle='tooltip' data-bs-placement='right' title='Link to another place'><i class='fa-solid fa-link-horizontal'></i></a>"
        ); 
        tr.appendChild(td);

        // actions
        td = document.createElement('td'); 
        td.className = "actions";
        td.innerHTML = (
            "<a href='' class='stop' data-bs-toggle='tooltip' data-bs-placement='right' title='Cancel job'><i class='fa-solid fa-ban'></i></a>"
        ); 
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

function count_jobs(response_contents) {

    let running = document.getElementById("dashboard_running");
    let completed = document.getElementById("dashboard_completed");
    let pending = document.getElementById("dashboard_pending");
    let stalled = document.getElementById("dashboard_stalled");

    let counter_running = 0;
    let counter_completed = 0;
    let counter_pending = 0;
    let counter_stalled = 0;

    /* then add the information for all the jobs */
    [].forEach.call(response_contents, function(D_job) {
        D_job_slurm = D_job["slurm"];
        job_state = D_job_slurm["job_state"].toLowerCase();

        if (job_state == "running" || job_state == "completing") {
            counter_running++;
        } 
        if (job_state == "completed") {
            counter_completed++;
        } 
        if (job_state == "pending") {
            counter_pending++;
        } 
        if (job_state == "timeout" || job_state == "out_of_memory" || job_state == "failed" || job_state == "cancelled" || job_state == "preempted") {
            counter_stalled++;
        } 
    });
    running.textContent = counter_running;
    completed.textContent = counter_completed;
    pending.textContent = counter_pending;
    stalled.textContent = counter_stalled;
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