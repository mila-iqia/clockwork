
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
const refresh_endpoint = "/jobs/search?want_json=True&want_count=True"

// This id is used to identify the table to populate in the associated HTML file
const id_of_table_to_populate = "dashboard_table" // hardcoded into jobs.html also

/*  The point of having those two global variables
    is that you can externally call `refresh_display(display_filter)`.
    It's not nice to deal with global variables, but the alternative
    is that we export more of the arbitrary stuff to the outside.
*/

var latest_response_contents; // Stores the content of the latest response received
var latest_filtered_response_contents; // Results in applying filters on the latest response contents

var page_num;

function incrementValue()
{
    var value = parseInt(document.getElementById('page_num').value, 10);
    value = isNaN(value) ? 0 : value;
    if(value<10){
        value++;
            document.getElementById('page_num').value = value;
    }
    //console.log(value);
    launch_refresh_all_data(query_filter, display_filter);
}
function decrementValue()
{
    var value = parseInt(document.getElementById('page_num').value, 10);
    value = isNaN(value) ? 0 : value;
    if(value>1){
        value--;
            document.getElementById('page_num').value = value;
    }
    //console.log(value);
    launch_refresh_all_data(query_filter, display_filter);
}

function changeValue(newval) {
    var value = parseInt(document.getElementById('page_num').value, 10);
    value = newval;
    document.getElementById('page_num').value = value;
    launch_refresh_all_data(query_filter, display_filter);
}

// unfinished, need more info
function removeAllChildNodes(parent) {
    while (parent.firstChild) {
        parent.removeChild(parent.firstChild);
    }
}
function make_pagination(page_num, nbr_items_per_page, total_items) {
    var TotalPages = Math.ceil(total_items / nbr_items_per_page);
 
    let pagingDiv = document.getElementById("pagingDiv");
    removeAllChildNodes(pagingDiv);
    if (TotalPages > 1) { 
        if (+page_num > 1) {
            // if has more than one page, add a PREVIOUS link
            const prevLI = document.createElement('li')
            const prevLink = document.createElement('a')
            const prevI = document.createElement('i');
            prevI.className = "fa-solid fa-caret-left";

            pagingDiv.appendChild(prevLI);
            prevLI.appendChild(prevLink);
            prevLink.appendChild(prevI);

            prevLink.addEventListener('click', decrementValue)

        } else {
            // otherwise, add a PREVIOUS span
            const prevLI = document.createElement('li');
            const prevSpan = document.createElement('span');
            const prevI = document.createElement('i');
            prevI.className = "fa-solid fa-caret-left";

            pagingDiv.appendChild(prevLI);
            prevLI.appendChild(prevSpan);
            prevSpan.appendChild(prevI);
        }
        
        for (var i = 1; i <= TotalPages; i++) {
            if (i >= 1) {
                if (+page_num != i) {
                    const prevLI = document.createElement('li')
                    const pageLink = document.createElement('a')
                    pageLink.textContent=i;

                    pagingDiv.appendChild(prevLI);
                    prevLI.appendChild(pageLink);
                    
                    pageLink.addEventListener('click', changeValue.bind(null, i))

                } else {
                    const prevLI = document.createElement('li')
                    const pageSpan = document.createElement('span')
                    pageSpan.textContent=i;
                    prevLI.className = "current";

                    pagingDiv.appendChild(prevLI);
                    prevLI.appendChild(pageSpan);
                }
            }
        }

        if (+page_num < TotalPages) {
            // if not on the last page, add a NEXT link
            const nextLI = document.createElement('li')
            const nextLink = document.createElement('a')
            const nextI = document.createElement('i');
            nextI.className = "fa-solid fa-caret-right";

            pagingDiv.appendChild(nextLI);
            nextLI.appendChild(nextLink);
            nextLink.appendChild(nextI);

            nextLink.addEventListener('click', incrementValue)

        } else {
            // if on the last page, add a NEXT span
            const prevLI = document.createElement('li')
            const nextSpan = document.createElement('span')
            const nextI = document.createElement('i');
            nextI.className = "fa-solid fa-caret-right";

            pagingDiv.appendChild(prevLI);
            prevLI.appendChild(nextSpan);
            nextSpan.appendChild(nextI);

        }
    }
}

function count_jobs(response_contents) {

    let completed = document.getElementById("dashboard_completed");
    let running = document.getElementById("dashboard_running");
    let pending = document.getElementById("dashboard_pending");
    let stalled = document.getElementById("dashboard_stalled");

    let counter_completed = 0;
    let counter_running = 0;
    let counter_pending = 0;
    let counter_stalled = 0;

    /* then add the information for all the jobs */
    [].forEach.call(response_contents, function(D_job) {
        D_job_slurm = D_job["slurm"];
        job_state = D_job_slurm["job_state"].toLowerCase();

        if (job_state == "completed") {
            counter_completed++;
        } 
        if (job_state == "running" || job_state == "completing") {
            counter_running++;
        } 
        if (job_state == "pending") {
            counter_pending++;
        } 
        if (job_state == "timeout" || job_state == "out_of_memory" || job_state == "failed" || job_state == "cancelled") {
            counter_stalled++;
        } 
    });
    completed.textContent = counter_completed;
    running.textContent = counter_running;
    pending.textContent = counter_pending;
    stalled.textContent = counter_stalled;

}

function format_date(timestamp) {
    /*
        Format a timestamp in order to display it in the a format according to the
        user's web settings.
    */
    let date_to_format = new Date(timestamp*1000); // The timestamp should be in milliseconds, not in seconds

    // Date
    // As word
    // This is donc directly when creating the jobs list

    // As timestamp
    if ("date_format" in web_settings && web_settings["date_format"] == "unix_timestamp"){
        return timestamp.toString();
    }
    else {
        // Format each element
        year = date_to_format.getFullYear();
        month = (date_to_format.getMonth()+1).toLocaleString('en-US', {minimumIntegerDigits: 2, useGrouping:false}); // Months are represented by indices from 0 to 11. Thus, 1 is added to the month. Moreover, this use of 'toLocaleString' is used to display each month with two digits (even the months from 1 to 9)
        day = date_to_format.getDate().toLocaleString('en-US', {minimumIntegerDigits: 2, useGrouping:false}); // This use of 'toLocaleString' is used to display each day with two digits (even the days from 1 to 9)

        // As MM/DD/YYYY
        if ("date_format" in web_settings && web_settings["date_format"] == "MM/DD/YYYY"){
            formatted_date = `${month}/${day}/${year}`;
        }

        // As DD/MM/YYYY
        else if ("date_format" in web_settings && web_settings["date_format"] == "DD/MM/YYYY"){
            formatted_date = `${day}/${month}/${year}`;
        }

        // As YYYY/MM/DD (arbitrary default value)
        else {
            formatted_date = `${year}/${month}/${day}`;
        }

        // Hour
        // AM/PM
        if ("time_format" in web_settings && web_settings["time_format"] == "AM/PM"){
            formatted_time = date_to_format.toLocaleString('en-US', { hour: 'numeric', minute: 'numeric', hour12: true });
        }
        // 24h
        else {
            formatted_time = date_to_format.toLocaleString('en-US', { hour: 'numeric', minute: 'numeric', hourCycle: 'h23' }); // hourCycle is set to h23 because otherwise, midnight is "24h" instead of "00h" on Chrome
        }
        
        return `${formatted_date} ${formatted_time}`;
    }
}

function check_web_settings_column_display(page_name, column_name){
    /*
        Check whether or not the web setting associated to the display of a job property
        as column on an array on a page (here "dashboard") is set. If it is set,
        check its boolean value.

        Such a web setting, if set, is accessible by calling web_settings[page_name][column_name].
        The different columns (ie jobs properties) for the dashboard page are now the following:
        ["clusters", "job_id", "job_name", "job_state", "start_time", "submit_time", "end_time", "links", "actions"]
        
        Parameters:
            page_name       The name of the page on which we should display or not the
                            job properties requested by the user in its preferences. For now,
                            the values "dashboard" or "jobs_list" are expected
            column_name     The column showing a specific job property, to display or not regarding
                            the preferences of the user.

        Returns:
            True if the web_setting is unset or True, False otherwise.
    */
            return !(("column_display" in web_settings) && (page_name in web_settings["column_display"]) && (column_name in web_settings["column_display"][page_name])) || web_settings["column_display"][page_name][column_name];
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

    // The following lines are commented alongside the call to make_pagination
    // below because we do not want to add pagination on the dashboard for now.
    //page_num = document.getElementById('page_num').value;
    //url = url + "&page_num=" + page_num;
    
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
    alljobs_filtered = apply_filter(latest_response_contents["jobs"], display_filter);
    
    total_jobs = latest_response_contents["nbr_total_jobs"];
        
    //for testing only - use a smaller number
    //nbr_items_per_page = 3;

    // The following lines are commented because we do not want to add pagination
    // on the dashboard for now.
    //page_num = document.getElementById('page_num').value;
    //nbr_items_per_page = display_filter['num_per_page'];
    //nbr_pages = Math.ceil(total_jobs / nbr_items_per_page);

    vacate_table(); // idempotent if not table is present
    populate_table(latest_filtered_response_contents);
    //kaweb - for some reason, the sortable init only works on reload/first load, not after changing filters
    //Sortable.init();
    //kaweb - tooltips work though
    var tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'))
    var tooltipList = tooltipTriggerList.map(function (tooltipTriggerEl) {
      return new bootstrap.Tooltip(tooltipTriggerEl)
    });

    //kaweb - attempt to count results
    count_jobs(alljobs_filtered);

    //kaweb - build pagination here
    // The following line is commented because we do not want to add pagination
    // on the dashboard for now.
    //make_pagination(page_num, nbr_items_per_page, total_jobs)
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
            <td><a href="/jobs/one?job_id={{e['job_id']}}"> {{e['job_id']}} </a></td>
            <td>{{e.get('name', "")[:32]}}</td> <!-- truncate after 32 chars -->
            <td>{{e['job_state']}}</td>
            ...
    */
    // Initialize the name of the current page
    let page_name = "dashboard";

    let table = document.getElementById(id_of_table_to_populate);

    /* create the table header */
    let thead = document.createElement('thead');
    let tr = document.createElement('tr');
    let th;
    // Clusters header
    if (check_web_settings_column_display(page_name, "clusters")) {
        th = document.createElement('th');
        th.innerHTML = "Cluster";
        tr.appendChild(th);
    }
    // Job ID header
    if (check_web_settings_column_display(page_name, "job_id")) {
        th = document.createElement('th');
        th.innerHTML = "Job ID";
        tr.appendChild(th);
    }
    // Job name header
    if (check_web_settings_column_display(page_name, "job_name")) {
        th = document.createElement('th');
        th.innerHTML = "Job name [:20]";
        tr.appendChild(th);
    }
    // Job state header
    if (check_web_settings_column_display(page_name, "job_state")) {
        th = document.createElement('th');
        th.innerHTML = "Job state";
        tr.appendChild(th);
    }
    // Submit time header
    if (check_web_settings_column_display(page_name, "submit_time")) {
        th = document.createElement('th');
        th.innerHTML = "Submit time";
        tr.appendChild(th);
    }
    // Start time header
    if (check_web_settings_column_display(page_name, "start_time")) {
        th = document.createElement('th');
        th.innerHTML = "Start time";
        tr.appendChild(th);
    }
    // End time header
    if (check_web_settings_column_display(page_name, "end_time")) {
        th = document.createElement('th');
        th.innerHTML = "End time";
        tr.appendChild(th);
    }
    // Links header
    if (check_web_settings_column_display(page_name, "links")) {
        th = document.createElement('th');
        th.innerHTML = "Links";
        th.setAttribute("data-sortable", "false");
        tr.appendChild(th);
    }
    // Actions header
    if (check_web_settings_column_display(page_name, "actions")) {
        th = document.createElement('th');
        th.innerHTML = "Actions";
        th.setAttribute("data-sortable", "false");
        tr.appendChild(th);
    }
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
        let a;

        // Clusters
        if (check_web_settings_column_display(page_name, "clusters")) {
            td = document.createElement('td');
            if (D_job_slurm["cluster_name"]) {
                a = document.createElement("a");
                a.setAttribute("href", "/clusters/one?cluster_name=" + D_job_slurm["cluster_name"]);
                a.innerHTML = D_job_slurm["cluster_name"];
                td.appendChild(a);
            }
            else {
                td.innerHTML = D_job_slurm["cluster_name"];
            }
            tr.appendChild(td);
        }
        // Job ID
        if (check_web_settings_column_display(page_name, "job_id")) {
            td = document.createElement('td');
            td.innerHTML = ("<a href=\"" + "/jobs/one?job_id=" + D_job_slurm["job_id"] + "\">" + D_job_slurm["job_id"] + "</a>");
            tr.appendChild(td);
        }
        // Job name
        if (check_web_settings_column_display(page_name, "job_name")) {
            td = document.createElement('td');
            td.innerHTML = (D_job_slurm["name"] ? D_job_slurm["name"] : "").substring(0, 20);
            tr.appendChild(td);  // truncated after 20 characters (you can change this magic number if you want)
        }
        // Job state
        if (check_web_settings_column_display(page_name, "job_state")) {
            //td = document.createElement('td'); td.innerHTML = D_job_slurm["job_state"]; tr.appendChild(td);
            //kaweb - using the job state as a shorthand to insert icons through CSS
            td = document.createElement('td'); 
            td.className = "state";
            
            var formatted_job_state = job_state.replace(/_/g, " ");
            
            td.innerHTML = ("<span class=\"status " + job_state + "\">" + formatted_job_state + "</span>");
            tr.appendChild(td);
        }
        // Submit_time, start time and end_time of the jobs
        let job_times = ["submit_time", "start_time", "end_time"];
        for (var i=0; i<job_times.length; i++) {
            let job_time = job_times[i];
            if (check_web_settings_column_display(page_name, job_time)) {
                td = document.createElement('td');
                if (D_job_slurm[job_time] == null) {
                    td.innerHTML = "";
                } else {
                    // If you want to display the time as "2021-07-06 22:19:46" for readability
                    // you need to set it up because this is going to be written as a unix timestamp.
                    // This might include injecting another field with a name
                    // such as "start_time_human_readable" or something like that, and using it here.
        
                    if ("date_format" in web_settings && web_settings["date_format"] == "words") {
                        td.innerHTML = TimeAgo.inWords(Date.now() - D_job_slurm[job_time]); // For a relative time
                    }
                    else {
                        td.innerHTML = format_date(D_job_slurm[job_time]); // For a human readable time or a timestamp
                    }
                }
                tr.appendChild(td);
            }
        };
        
        // Links
        if (check_web_settings_column_display(page_name, "links")) {
            td = document.createElement('td'); 
            td.className = "links";
            
            // This link works only for Narval and Beluga. See CW-141.
            if ((D_job_slurm["cluster_name"] == "narval") || (D_job_slurm["cluster_name"] == "beluga")) {
                // https://portail.narval.calculquebec.ca/secure/jobstats/<username>/<jobid>
                let target_url = `https://portail.${D_job_slurm["cluster_name"]}.calculquebec.ca/secure/jobstats/${D_job_slurm["username"]}/${D_job_slurm["job_id"]}`
                link0_innerHTML  = `<a href='${target_url}' data-bs-toggle='tooltip' data-bs-placement='right' title='this job on DRAC portal'><i class='fa-solid fa-file'></i></a>`
            } else {
                link0_innerHTML = ""
            }
            // This is just a placeholder for now.
            link1_innerHTML = "<a href='' data-bs-toggle='tooltip' data-bs-placement='right' title='Link to another place'><i class='fa-solid fa-link-horizontal'></i></a>"
            td.innerHTML = link0_innerHTML + link1_innerHTML
            tr.appendChild(td);
        }

        // Actions
        if (check_web_settings_column_display(page_name, "actions")) {
            td = document.createElement('td'); 
            td.className = "actions";
            td.innerHTML = (
                "<a href='' class='stop' data-bs-toggle='tooltip' data-bs-placement='right' title='Cancel job'><i class='fa-solid fa-xmark'></i></a>"
            ); 
            tr.appendChild(td);
        }

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