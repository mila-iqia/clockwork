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
