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

function set_nbr_items_per_page(nbr_items_per_page) {
  /*
    Contact the server in order to modify the number of items to display per
    page, set in the user's settings.

    Parameter:
    - nbr_items_per_page    The preferred number of items to display per page,
                            ie the number to store in the settings
  */

  // Define the URL
  let url = "/settings/web/nbr_items_per_page/set?nbr_items_per_page=".concat("", nbr_items_per_page)

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
}
