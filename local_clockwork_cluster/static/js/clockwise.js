
/*
    Two main functions (async calls) :
        launch_refresh_all_data
        launch_refresh_markdown2html
*/

function launch_refresh_all_data(note_or_folder_jid) {
    /*
        We just clicked on an item with jid `note_or_folder_jid`.
        We want to update the hierarchy accordingly.
        This makes use of the previously-defined functions.
    */

    // const url = "/joplin_live/mono/ancestors_folders_of_single_folder/b3ccb4c5d79249be95c166e81e115410";
    let url = "/joplin_live/mono/ancestors_folders_of_single_folder/" + note_or_folder_jid;
    const request = new Request(url,
        {   method: 'GET',
        });
    fetch(request)
    .then(response => {
        if (response.status === 200) {
            return response.json();
        } else {
            throw new Error('Something went wrong on api server!');
        }
    })
    .then(response => {
        cleanup_everything();
        update_folder_hierarchy(response);
        update_notes_component(response);
        update_note_markdown(response);
        update_note_meta_info(response);
        /* another async call */
        launch_refresh_markdown2html(response["note_contents"]["body"]);
    }).catch(error => {
        console.error(error);
    });
};

function launch_refresh_markdown2html(body_as_markdown) {
    /*  We'll make another async call, but this time to 
            /convert_markdown2html_note [POST] with {"body_as_markdown": ...}
        that returns
            {'body_as_html': ...}
    */            
    const url = "/joplin_live/rest/convert_markdown2html_note";
    const request = new Request(url,
        {   method: 'POST',
            body: JSON.stringify({
                'body_as_markdown': body_as_markdown
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
    .then(response => {
        //console.log(response);
        //console.log("A");
        update_note_html(response);
        //console.log("B");
    }).catch(error => {
        console.error(error);
    });
};





/*
    Helpers:
        
        cleanup_everything
        update_folder_hierarchy
        update_notes_component
        update_note_markdown
        update_note_html
*/



function cleanup_everything() {
    // mix of
    //    https://stackoverflow.com/questions/14094697/how-to-create-new-div-dynamically-change-it-move-it-modify-it-in-every-way-po
    //    https://stackoverflow.com/questions/24775725/loop-through-childnodes
    
    let hierarchy_folders_component = document.getElementById("hierarchy_folders_component");
    [].forEach.call(hierarchy_folders_component.children, function(child) {
        hierarchy_folders_component.removeChild(child);
    });

    let notes_component = document.getElementById("notes_component");
    [].forEach.call(notes_component.children, function(child) {
        notes_component.removeChild(child);
    });

    document.getElementById("note_body_as_markdown_textarea").innerText = "";
    document.getElementById("note_meta_info").innerText = "";
    document.getElementById("section_note_html").innerText = "";

}


function update_folder_hierarchy(response_contents) {
    /* 
        `response_contents` here is a dict with fields 
            {
                "folders_ancestry" : LD_folders_ancestry,
                "notes_last_level": notes_last_level,
                "note_jid": note_jid,
                "folder_jid": folder_jid,
                "note_contents": note_contents
            }
        For starters, we can say that response_contents["folders_ancestry"]
        is a list of elements of the form
            {
                "title" : string,
                "jid": string,
                "parent_jid": string,
                "status" : "open" or "closed",
                "note_count" : int,
                "children": list
            }
        that can have children of the same form.
        We want to clean up the content of
            hierarchy = document.getElementById("hierarchy_folders_component");
        and then insert the content again.
    */
    // Okay, so we need to massage the data structure just a little bit right now.
    let folders_tree = {"title": "Joplin", "jid": "", "parent_jid": "", "status": "open",
                        "children": response_contents["folders_ancestry"]}

    let hierarchy_folders_component = document.getElementById("hierarchy_folders_component");

    function recursive_insertion(insertion_point, folders_tree) {

        /*
            The idea here is that we will create recursive instances
            `subtree_container` to house all the entries.
            The entries themselves will be clickable and have side-effects,
            but the `subtree_container` are just containers for
            the tree-structure to be displayed like a tree.
        */
        
        let subtree_container = document.createElement('div');
        subtree_container.classList.add("subtree_container");  // in case we want to style it
        // subtree_container.style.marginLeft = '40px'; // done in css

            let subtree_folder = document.createElement('div');
            subtree_folder.classList.add("subtree_folder");  // in case we want to style it

            subtree_folder.innerText = folders_tree['title'];  // 'title' is a field from the server; not a JS thing
                let folder_icon = document.createElement('i');
                folder_icon.classList.add("material-icons");
                if (folders_tree["status"] == "open") {
                    folder_icon.innerText = "folder_open";
                } else {
                    folder_icon.innerText = "folder";
                }
            subtree_folder.prepend(folder_icon);
            subtree_folder.onclick = function() {
                //console.debug(folders_tree["jid"]);
                var url = "../../../joplin_live/arcanix/folder/" + folders_tree["jid"];
                //console.debug(url);
                window.location = url;
            }
            subtree_container.appendChild(subtree_folder);
            insertion_point.appendChild(subtree_container);

        //console.log("appended " + folders_tree['title']);
        [].forEach.call(folders_tree['children'], function(e) {
            // could be empty, in which case this recursion terminates
            recursive_insertion(subtree_container, e);
        });
    }

    recursive_insertion(hierarchy_folders_component, folders_tree);

}


function update_notes_component(response_contents) {
    /* 
        `response_contents` here is a dict with fields 
            {
                "folders_ancestry" : LD_folders_ancestry,
                "notes_last_level": notes_last_level,
                "note_jid": note_jid,
                "folder_jid": folder_jid,
                "note_contents": note_contents
            }
    */

    /* Process response_contents["notes_component"] now. */
    let notes_component = document.getElementById("notes_component");

    /*
    Note that we are not displaying response_contents["note_contents"] here,
    but rather response_contents["notes_last_level"], which are the notes
    found in the folder_jid.
    */
    let table = document.createElement('table');
    table.classList.add("striped");
    let thead = document.createElement('thead');
        let tr = document.createElement('tr');
            let th0 = document.createElement('th');
                th0.innerText = "title";
            tr.append(th0);
        thead.append(tr);
    table.append(thead);

    let tbody = document.createElement('tbody');
        [].forEach.call(response_contents["notes_last_level"], function(note_info) {
            let tr = document.createElement('tr');
            tr.classList.add("note_row");
                let td0 = document.createElement('td');
                    let url = "../../../joplin_live/arcanix/note/" + note_info["jid"];
                    td0.innerHTML = "<a href=\"" + url + "\">" + note_info["title"] + "</a>";
                    /*
                    // TODO : update this to have hyperlinks
                    td0.innerText = note_info["title"];
                    td0.onclick = function() {
                        console.log(note_info);
                        var url = "../../../joplin_live/arcanix/note/" + note_info["jid"];
                        // console.log(url);
                        window.location = url;
                    }*/
                    // td0.style.cursor = "pointer";
                tr.append(td0);
            tbody.append(tr);
        });
    table.append(tbody);             
    notes_component.append(table);
}


function update_note_markdown(response_contents) {
    /* 
        `response_contents` here is a dict with fields 
            {
                "folders_ancestry" : LD_folders_ancestry,
                "notes_last_level": notes_last_level,
                "note_jid": note_jid,
                "folder_jid": folder_jid,
                "note_contents": note_contents
            }
    */    
    console.debug(response_contents["note_contents"])
    /* To be used in callback to an http request. */
    // Populate the note body.
    if ((response_contents["note_contents"]) && (response_contents["note_contents"]["body"].length > 0)) {
        document.getElementById("note_body_as_markdown_textarea").innerHTML = (
            response_contents["note_contents"]["body"]
        )
    }
}


function update_note_meta_info(response_contents) {
    /* 
        `response_contents` here is a dict with fields 
            {
                "folders_ancestry" : LD_folders_ancestry,
                "notes_last_level": notes_last_level,
                "note_jid": note_jid,
                "folder_jid": folder_jid,
                "note_contents": note_contents
            }
    */    

    /* To be used in callback to an http request. */
    // Populate the note meta information.

    /*
    All the meta data that could be listed is the following.

        altitude: "113.8750"
        application_data: ""
        author: "Guillaume Alain"
        body: "Voici la solution pour mon problème de Apple qui ne donne pas l’option de formatter avec encryption.↵↵vesuvan:~ gyomalin$ diskutil list↵/dev/disk0 (internal, physical):↵   #:                       TYPE NAME                    SIZE       IDENTIFIER↵   0:      GUID_partition_scheme                        *1.0 TB     disk0↵   1:                        EFI EFI                     209.7 MB   disk0s1↵   2:                 Apple_APFS Container disk2         1.0 TB     disk0s2↵↵/dev/disk1 (external, physical):↵   #:                       TYPE NAME                    SIZE       IDENTIFIER↵   0:      GUID_partition_scheme                        *12.0 TB    disk1↵   1:                        EFI EFI                     209.7 MB   disk1s1↵   2:          Apple_CoreStorage LaCie                   12.0 TB    disk1s2↵   3:                 Apple_Boot Boot OS X               134.2 MB   disk1s3↵↵/dev/disk2 (synthesized):↵   #:                       TYPE NAME                    SIZE       IDENTIFIER↵   0:      APFS Container Scheme -                      +1.0 TB     disk2↵                                 Physical Store disk0s2↵   1:                APFS Volume Macintosh HD            779.3 GB   disk2s1↵   2:                APFS Volume Preboot                 45.2 MB    disk2s2↵   3:                APFS Volume Recovery                509.8 MB   disk2s3↵   4:                APFS Volume VM                      3.2 GB     disk2s4↵↵/dev/disk3 (external, virtual):↵   #:                       TYPE NAME                    SIZE       IDENTIFIER↵   0:                  Apple_HFS LaCie                  +12.0 TB    disk3↵                                 Logical Volume on disk1s2↵                                 3F1CF1C5-8097-4DEC-851F-26A968521092↵                                 Unlocked Encrypted↵↵/dev/disk4 (external, physical):↵   #:                       TYPE NAME                    SIZE       IDENTIFIER↵   0:     FDisk_partition_scheme                        *1.0 TB     disk4↵   1:                  Apple_HFS T51G                    1.0 TB     disk4s1↵↵vesuvan:~ gyomalin$ diskutil eraseDisk JHFS+ "T51G" GPT /dev/disk4↵Started erase on disk4↵Unmounting disk↵↵vesuvan:~ gyomalin$ diskutil list↵/dev/disk0 (internal, physical):↵   #:                       TYPE NAME                    SIZE       IDENTIFIER↵   0:      GUID_partition_scheme                        *1.0 TB     disk0↵   1:                        EFI EFI                     209.7 MB   disk0s1↵   2:                 Apple_APFS Container disk2         1.0 TB     disk0s2↵↵/dev/disk1 (external, physical):↵   #:                       TYPE NAME                    SIZE       IDENTIFIER↵   0:      GUID_partition_scheme                        *12.0 TB    disk1↵   1:                        EFI EFI                     209.7 MB   disk1s1↵   2:          Apple_CoreStorage LaCie                   12.0 TB    disk1s2↵   3:                 Apple_Boot Boot OS X               134.2 MB   disk1s3↵↵/dev/disk2 (synthesized):↵   #:                       TYPE NAME                    SIZE       IDENTIFIER↵   0:      APFS Container Scheme -                      +1.0 TB     disk2↵                                 Physical Store disk0s2↵   1:                APFS Volume Macintosh HD            779.4 GB   disk2s1↵   2:                APFS Volume Preboot                 45.2 MB    disk2s2↵   3:                APFS Volume Recovery                509.8 MB   disk2s3↵   4:                APFS Volume VM                      3.2 GB     disk2s4↵↵/dev/disk3 (external, virtual):↵   #:                       TYPE NAME                    SIZE       IDENTIFIER↵   0:                  Apple_HFS LaCie                  +12.0 TB    disk3↵                                 Logical Volume on disk1s2↵                                 3F1CF1C5-8097-4DEC-851F-26A968521092↵                                 Unlocked Encrypted↵↵/dev/disk4 (external, physical):↵   #:                       TYPE NAME                    SIZE       IDENTIFIER↵   0:      GUID_partition_scheme                        *1.0 TB     disk4↵   1:                        EFI EFI                     209.7 MB   disk4s1↵   2:                  Apple_HFS T51G                    999.9 GB   disk4s2↵↵vesuvan:~ gyomalin$ diskutil cs convert disk4s2 -passphrase↵↵This is an example workflow to encrypt an USB thumbdrive with HSF+ (Journaled) with diskutilusing the command line.↵↵Assuming you start with a MS-DOS formatted USB stick.↵Step 1: List all currently mounted disks diskutil list:↵/dev/disk2 (external, physical):↵   #:                       TYPE NAME                    SIZE       IDENTIFIER↵   0:     FDisk_partition_scheme                        *8.1 GB     disk2↵   1:                 DOS_FAT_32 MYSTORAGE               8.1 GB     disk2s1↵↵You see the disk MYSTORAGE has the identifier disk2s1 and is DOS_FAT_32 formatted.↵↵Step 2: Now format the disk disk2 as HSF+ (Journaled):↵diskutil eraseDisk JHFS+ "New Storage" GPT disk2↵↵The name of the disk will be "New Storage". At this time it is not yet encrypted. Look at the list of disks diskutil list:↵↵/dev/disk2 (external, physical):↵   #:                       TYPE NAME                    SIZE       IDENTIFIER↵   0:      GUID_partition_scheme                        *8.1 GB     disk2↵   1:                        EFI EFI                     209.7 MB   disk2s1↵   2:                  Apple_HFS New Storage             7.7 GB     disk2s2↵↵Step 3: Now you see the "New Storage" partition with identifier disk2s2. Encrypt this partition using:↵↵diskutil cs convert disk2s2 -passphrase↵Enter the passphrase when prompted.↵↵If you list the disks now, you also see the encrypted logical volume diskutil list:↵↵/dev/disk2 (external, physical):↵   #:                       TYPE NAME                    SIZE       IDENTIFIER↵   0:      GUID_partition_scheme                        *8.1 GB     disk2↵   1:                        EFI EFI                     209.7 MB   disk2s1↵   2:          Apple_CoreStorage New Storage             7.7 GB     disk2s2↵   3:                 Apple_Boot Boot OS X               134.2 MB   disk2s3↵↵/dev/disk3 (external, virtual):↵   #:                       TYPE NAME                    SIZE       IDENTIFIER↵   0:                  Apple_HFS New Storage            +7.3 GB     disk3↵                                 Logical Volume on disk2s2↵                                 8B474F90-34B7-49FE-95E0-E8B260C51CCF↵                                 Unlocked Encrypted↵↵* * *↵↵If you skip step 3, you can also encrypt the disk using Finder:↵[![](:/87be6dc8fe45e8d0b1af628208355da3)](https://i.stack.imgur.com/rLUYi.png)↵Just right-click on the drive and select "Encrypt drive-name".↵↵**> Caution:**>  If you choose this alternative approach, the disk gets formatted as APFS encrypted disk"
        created_time: 1559400459000
        encryption_applied: 0
        encryption_cipher_text: ""
        is_conflict: 0
        is_todo: 0
        jid: "ce7295b1d215452694d21c0ca6c9b44c"
        latitude: "45.49599542"
        longitude: "-73.61672986"
        order: 0
        parent_jid: "3cf3e3cc11f142bba9b71a0068fb4307"
        source: "evernote.desktop.mac"
        source_application: "net.cozic.joplin-desktop"
        source_url: ""
        title: "formatting Samsung T5"
        todo_completed: 0
        todo_due: 0
        type_: 1
        updated_time: 1559400559000
        user_created_time: 1559400459000
        user_updated_time: 1559400559000
    */

    if ((response_contents["note_contents"]) && (response_contents["note_contents"]["body"].length > 0)) {

        E = {
            "title": response_contents["note_contents"]["title"],
            "jid": response_contents["note_contents"]["jid"],
            "parent_jid": response_contents["note_contents"]["parent_jid"],
            "source_url": response_contents["note_contents"]["source_url"],
            //
            "altitude": response_contents["note_contents"]["altitude"],
            "latitude": response_contents["note_contents"]["latitude"],
            "longitude": response_contents["note_contents"]["longitude"],
            // "application_data": response_contents["note_contents"]["application_data"],
            "created_time": response_contents["note_contents"]["created_time"],
            "updated_time": response_contents["note_contents"]["updated_time"],
            "user_created_time": response_contents["note_contents"]["user_created_time"],
            "user_updated_time": response_contents["note_contents"]["user_updated_time"],
            //
            "is_conflict": response_contents["note_contents"]["is_conflict"],
            "is_todo": response_contents["note_contents"]["is_todo"],
            };
        document.getElementById("note_meta_info").innerHTML = "<pre>\n" + JSON.stringify(E, null, '  ') + "\n</pre>";
        document.getElementById("note_meta_title").innerText = E["title"];
    }
}


function update_note_html(response_contents) {
    /*
    This is the response from 
        /joplin_live/rest_routes/convert_markdown2html_note
    that contains the field "body_as_html".
    */
   let section_note_html = document.getElementById("section_note_html");
   //console.debug(response_contents);
   console.debug(response_contents['body_as_html']);
   section_note_html.innerHTML = response_contents['body_as_html'];
}
