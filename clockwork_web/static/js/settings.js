/*
    This page gathers some functions used by the template settings.html.
    It should only be included in this template, as it uses some variables
    and HTML elements which may not exist in other templates.
*/

/*
    Generate the content of the dropdown menu for chosing what the number
    of elements to display per listing page should be for the current user.

    Parameters:
        - current_nbr_items_per_page    The number of items to display per
                                        listing page which is currently stored
                                        in the user settings
*/
function fill_nbr_items_per_page_dropdown_menu(current_nbr_items_per_page) {
    // Initialise the list of options for the values of nbr_items_per_page
    // proposed to the user
    // NB: Let's also allow user to go back to default 40 items per page.
    let nbr_items_per_page_options = [25, 40, 50, 100];

    // Add the current_nbr_items_per_page to this list if it is not contained
    // in it yet
    if (!nbr_items_per_page_options.includes(current_nbr_items_per_page)) {
        nbr_items_per_page_options.push(current_nbr_items_per_page);
    }

    // Sort the list
    nbr_items_per_page_options.sort(function(a,b) {
        return a-b;
    });

    // Fill the dropdown menu with the content of the list
    let nbr_items_per_page_menu = document.getElementById("nbr_items_per_page_selection"); // Retrieve the dropdown menu
    nbr_items_per_page_menu.innerHTML = ""; // Clear its content
    for (let i=0; i<nbr_items_per_page_options.length; i++) {
        let option = document.createElement("option");
        option.value = nbr_items_per_page_options[i]; // Value of the option
        option.text = nbr_items_per_page_options[i]; // Text that appears for this option in the dropdown menu
        // Preselect the current option
        if (nbr_items_per_page_options[i] == current_nbr_items_per_page) {
            option.selected = true;
        }
        nbr_items_per_page_menu.appendChild(option);
    }
}
