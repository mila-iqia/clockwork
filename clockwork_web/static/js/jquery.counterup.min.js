/*!
* jquery.counterup.js 1.0
*
* Copyright 2013, Benjamin Intal http://gambit.ph @bfintal
* Released under the GPL v2 License
*
* Date: Nov 26, 2013
*/
!function($){"use strict";$.fn.counterUp=function(t){var e=$.extend({time:400,delay:10},t);return this.each((function(){var t=$(this),n=e;t.waypoint((function(){var e=[],u=n.time/n.delay,a=t.text(),r=/[0-9]+,[0-9]+/.test(a);a=a.replace(/,/g,"");/^[0-9]+$/.test(a);for(var o=/^[0-9]+\.[0-9]+$/.test(a),c=o?(a.split(".")[1]||[]).length:0,i=u;i>=1;i--){var s=parseInt(a/u*i);if(o&&(s=parseFloat(a/u*i).toFixed(c)),r)for(;/(\d+)(\d{3})/.test(s.toString());)s=s.toString().replace(/(\d+)(\d{3})/,"$1,$2");e.unshift(s)}t.data("counterup-nums",e),t.text("0");t.data("counterup-func",(function(){t.text(t.data("counterup-nums").shift()),t.data("counterup-nums").length?setTimeout(t.data("counterup-func"),n.delay):(t.data("counterup-nums"),t.data("counterup-nums",null),t.data("counterup-func",null))})),setTimeout(t.data("counterup-func"),n.delay)}),{offset:"100%",triggerOnce:!0})}))}}(jQuery);