/**
 *  Javascript functions related to the user information
 **/


function enable_dark_mode() {
  /*
    Contact the server in order to enable the dark mode for the current user.
  */

  // Define the URL
  let url = "/settings/web/dark_mode/set"

  // Send the request and retrieve the response
  const request = new Request(url,
      {   method: 'GET',
          headers: {
              'Content-Type': 'application/json'
          }
      });
  fetch(request)
  .then(response => {
      if (response.status === 200) {
          // We do nothing here... for now
      } else {
          throw new Error('Something went wrong on API server!');
      };
    }
  )
};

function disable_dark_mode() {
  /*
    Contact the server in order to disable the dark mode (ie enable the light mode)
    for the current user.
  */

  // Define the URL
  let url = "/settings/web/dark_mode/unset"

  // Send the request and retrieve the response
  const request = new Request(url,
      {   method: 'GET',
          headers: {
              'Content-Type': 'application/json'
          }
      });
  fetch(request)
  .then(response => {
      if (response.status === 200) {
          // We do nothing here... for now
      } else {
          throw new Error('Something went wrong on API server!');
      };
    }
  )
};

function enable_column(page_name, column_name) {
  /*
      Contact the server in order to show the corresponding column on the given page
      (for now, the only possible page name is "jobs_list").

      Parameters:
      page_name	It can only get the value "jobs_list".
                It identifies the page where the column should or
                should not appear
      column_name			Name identifying the column to display or not on
                the page identified by corresponding_page
  */

  // Define the URL
  let url = `/settings/web/column/set?page=${page_name}&column=${column_name}`;

  // Send the request and retrieve the response
  const request = new Request(url,
    {   method: 'GET',
        headers: {
            'Content-Type': 'application/json'
        }
    });
  fetch(request)
  .then(response => {
      if (response.status === 200) {
          // We do nothing here... for now
      } else {
          throw new Error('Something went wrong on API server when updating the column ' + column_name + ' on the page ' + page_name);
      };
    }
  )
};

function disable_column(page_name, column_name) {
  /*
      Contact the server in order to hide the corresponding column on the given page
      (for now, the page name can only be"jobs_list").

      Parameters:
      page_name	It can only get the value "jobs_list".
                It identifies the page where the column should or
                should not appear
      column_name			Name identifying the column to display or not on
                the page identified by corresponding_page
  */

  // Define the URL
  let url = "/settings/web/column/unset?";
  url = url+"page="+page_name;
  url = url+"&column="+column_name;

  // Send the request and retrieve the response
  const request = new Request(url,
    {   method: 'GET',
        headers: {
            'Content-Type': 'application/json'
        }
    });
  fetch(request)
  .then(response => {
      if (response.status === 200) {
          // We do nothing here... for now
      } else {
          throw new Error('Something went wrong on API server when updating the column ' + column_name + ' on the page ' + page_name);
      };
    }
  )
};

function set_language(language) {
  /*
    Contact the server in order to update the preferred language of the user,
    set in the user's settings.

    Parameter:
    - language  The preferred language to use when displaying information to the user
  */

  // Define the URL
  let url = "/settings/web/language/set?language="+language;
  
  // Send the request and retrieve the response
  const request = new Request(url,
    {   method: 'GET',
        headers: {
            'Content-Type': 'application/json'
        }
    }
  );

  fetch(request)
  .then(response => {
      if (response.status === 200) {
          // We do nothing here... for now
      } else {
          throw new Error('Something went wrong on API server when changing language to "'+language+'".');
      };
    }
  )
}

function set_nbr_items_per_page(nbr_items_per_page) {
  /*
    Contact the server in order to modify the number of items to display per
    page, set in the user's settings.

    Parameter:
    - nbr_items_per_page    The preferred number of items to display per page,
                            ie the number to store in the settings
  */

  // Define the URL
  let url = "/settings/web/nbr_items_per_page/set?nbr_items_per_page="+nbr_items_per_page

  // Send the request and retrieve the response
  const request = new Request(url,
      {   method: 'GET',
          headers: {
              'Content-Type': 'application/json'
          }
      });
  fetch(request)
  .then(response => {
      if (response.status === 200) {
          // We do nothing here... for now
      } else {
          throw new Error('Something went wrong on API server when changing number of items to display per page to "'+nbr_items_per_page+'".');
      };
    }
  )
}

function set_date_format(date_format) {
  /*
    Contact the server in order to update the date format used to display
    the "date part" of the timestamps on the web interface for the user.

    Parameter:
    - date_format   The date format, chosen by the user, to use to display
                    the "date part" of the timestamps on the web interface
  */

  // Define the URL to send the request
  let url = "/settings/web/date_format/set?date_format=".concat("", date_format);

   // Send the request and retrieve the response
   const request = new Request(url,
    {   method: 'GET',
        headers: {
            'Content-Type': 'application/json'
        }
    });
  fetch(request)
  .then(response => {
      if (response.status === 200) {
          // We do nothing here... for now
      } else {
          throw new Error('Something went wrong on API server!');
      };
    }
  )
};

function set_time_format(time_format) {
  /*
    Contact the server in order to update the time format used to display
    the "time part" of the timestamps on the web interface for the user.

    Parameter:
    - time_format   The time format, chosen by the user, to use to display
                    the "time part" from the timestamps on the web interface
  */

  // Define the URL to send the request
  let url = "/settings/web/time_format/set?time_format="+time_format;

   // Send the request and retrieve the response
   const request = new Request(url,
    {   method: 'GET',
        headers: {
            'Content-Type': 'application/json'
        }
    });
  fetch(request)
  .then(response => {
      if (response.status === 200) {
          // We do nothing here... for now
      } else {
          throw new Error('Something went wrong on API server!');
      };
    }
  )
};