jQuery(document).ready(function($){
    //$('.num').counterUp({
    //    delay: 10,
    //    time: 1000
    //});

    search_table = document.querySelector('#search_table');
    if (search_table) Sortable.initTable(search_table);

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
            states = [];

            $(this).find("input[name='username']").each(function(){
                if ($("#user_option_other").is(":checked")) {
                    user = $("#user_option_other_textarea").val();
                } else if ($("#user_option_only_me").is(":checked")) {
                    user = $("#user_option_only_me").val();
                } else {
                    user = null;
                }
            });

            $(this).find("input[name='cluster_name']").each(function(){
                if ($(this).is(":checked")) clusters.push( $(this).val() );
            });
            
            $(this).find("input[name='state']").each(function(){
                if ($(this).is(":checked")) states.push( $(this).val() );
            });

            // not a real solution to GEN-160
            //$('form#nbr_per_page').find("select[name='nbr_items_per_page']").each(function(){
            //    nbr = $(this).val();
            //});

            clusters = clusters.toString();
            states = states.toString();

            if (user) {
                params['username'] = user;
            }
            params['cluster_name'] = clusters;
            params['state'] = states;
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
    
    $('.form-check-state').on('change', function(e) {
        if ($('.form-check-state:checked').length == 0 && !this.checked)
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

    

    //$('#nbr_items_per_page').on('change', function() {
        //$("form.searchform").formSubmit();
    //});

});