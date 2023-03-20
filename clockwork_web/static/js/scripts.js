jQuery(document).ready(function($){
    //$('.num').counterUp({
    //    delay: 10,
    //    time: 1000
    //});

    $('[data-bs-toggle="tooltip"]').tooltip();

    $("input[name='username']").click(function () {
        if ($("#user_option_other").is(":checked")) {
            $("#user_option_other_textarea").removeAttr("disabled");
            $("#user_option_other_textarea").focus();

        } else {
            $("#user_option_other_textarea").attr("disabled", "disabled");
        }
    });

    (function($) {
    $.fn.formSubmit = function() {
        return this.each(function() {
            params = {};
            clusters = [];
            job_states = [];

            $(this).find("input[name='username']").each(function(){
                if ($("#user_option_other").is(":checked")) {
                    user = normalize_username($("#user_option_other_textarea").val());
                } else if ($("#user_option_only_me").is(":checked")) {
                    user = $("#user_option_only_me").val();
                } else {
                    user = null;
                }
            });

            $(this).find("input[name='cluster_name']").each(function(){
                if ($(this).is(":checked")) clusters.push( $(this).val() );
            });
            
            $(this).find("input[name='aggregated_job_state']").each(function(){
                if ($(this).is(":checked")) job_states.push( $(this).val() );
            });

            // not a real solution to GEN-160
            //$('form#nbr_per_page').find("select[name='nbr_items_per_page']").each(function(){
            //    nbr = $(this).val();
            //});

            clusters = clusters.toString();
            job_states = job_states.toString();

            if (user) {
                params['username'] = user;
            }
            params['cluster_name'] = clusters;
            params['aggregated_job_state'] = job_states;
            if (web_settings['nbr_items_per_page']) {
                params['nbr_items_per_page'] = web_settings['nbr_items_per_page'];
            }

            var formData = $.param( params );
            var formData = decodeURIComponent(formData);
            var fullUrl = window.location.origin;
            var finalUrl = fullUrl+"/jobs/search?"+formData;

            //console.log(formData);
            window.location.href = finalUrl;
        });
    };
    })(jQuery)


    $("form.searchform").submit(function (e) {
        e.preventDefault();
        $(this).formSubmit();
    });

    $('.form-check-clusters').on('change', function(e) {
        if ($('.form-check-clusters:checked').length == 0 && !this.checked)
            this.checked = true;
    });

    $('.form-check-job-state').on('change', function(e) {
        if ($('.form-check-job-state:checked').length == 0 && !this.checked)
            this.checked = true;
    });

    $("#show_hide_password a.reveal").on('click', function(event) {
        event.preventDefault();
        if($('#show_hide_password input').attr("type") == "text"){
            $('#show_hide_password input').attr('type', 'password');
            $('#show_hide_password a.reveal i').addClass( "fa-eye-slash" );
            $('#show_hide_password a.reveal i').removeClass( "fa-eye" );
        }else if($('#show_hide_password input').attr("type") == "password"){
            $('#show_hide_password input').attr('type', 'text');
            $('#show_hide_password a.reveal i').removeClass( "fa-eye-slash" );
            $('#show_hide_password a.reveal i').addClass( "fa-eye" );
        }
    });

     $('.copy-btn').on("click", function(){
        value = $(this).data('clipboard-text'); //Upto this I am getting value

        var $temp = $("<input>");
          $("body").append($temp);
          $temp.val(value).select();
          document.execCommand("copy");
          $temp.remove();
    })

    $("#show_hide_password a.copy_clipboard").on('click', function(event) {
        event.preventDefault();

        value = $('input#clockwork_api_key').val(); //Upto this I am getting value

        var $temp = $("<input>");
            $("body").append($temp);
             $temp.val(value).select();
            document.execCommand("copy");
            $temp.remove();

        $('#show_hide_password a.copy_clipboard i').addClass( "fa-thumbs-up" );
        $('#show_hide_password a.copy_clipboard i').removeClass( "fa-copy" );

        setTimeout(function(){
            $('#show_hide_password a.copy_clipboard i').removeClass( "fa-thumbs-up" );
            $('#show_hide_password a.copy_clipboard i').addClass( "fa-copy" );
        },5000);


    });

    function show_popup(){
       $("div.ribbon").animate({top: '0'});
    };
    window.setTimeout( show_popup, 2000 ); // 5 seconds


    function normalize_username(username){
        /*
            Add the @mila.quebec suffix to the username if not present
        */
       if (username != null && !username.includes("@")){
            username += "@mila.quebec";
       }
       return username;
    };


    //$('#nbr_items_per_page').on('change', function() {
        //$("form.searchform").formSubmit();
    //});

});
