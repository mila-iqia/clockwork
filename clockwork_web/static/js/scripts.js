jQuery(document).ready(function($){
    //$('.num').counterUp({
    //    delay: 10,
    //    time: 1000
    //});

    search_table = document.querySelector('#search_table');
    if (search_table) Sortable.initTable(search_table);

    $("input[name='user_name']").click(function () {
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

            $(this).find("input[name='user_name']").each(function(){
                if ($("#user_option_other").is(":checked")) {
                    user = $("#user_option_other_textarea").val();
                } else if ($("#user_option_only_me").is(":checked")) {
                    user = $("#user_option_only_me").val();
                } else {
                    user = null;
                }
            });

            $(this).find("input[name='clusters_names']").each(function(){
                if ($(this).is(":checked")) clusters.push( $(this).val() );
            });
            
            $(this).find("input[name='states']").each(function(){
                if ($(this).is(":checked")) states.push( $(this).val() );
            });

            $('form#nbr_per_page').find("select[name='nbr_items_per_page']").each(function(){
                nbr = $(this).val();
            });

            clusters = clusters.toString();
            states = states.toString();

            if (user) {
                params['user_name'] = user;
            }
            params['clusters_names'] = clusters;
            params['states'] = states;
            if (nbr) {
                params['nbr_items_per_page'] = nbr;
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

    $('#nbr_items_per_page').on('change', function() {
        $("form.searchform").formSubmit();
    });

});