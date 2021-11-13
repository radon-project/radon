jQuery("#backtotop").click(function () {
    jQuery("body,html").animate({
        scrollTop: 0
    }, 600);
});

jQuery(window).scroll(function () {
    if (jQuery(window).scrollTop() > 150) {
        jQuery("#backtotop").addClass("visible");
    } else {
        jQuery("#backtotop").removeClass("visible");
    }
});

jQuery("#callcomment").click(function () {
    jQuery("#commentbox").animate({
        scrollTo: 90
    }, 600);
});

jQuery(window).scroll(function () {
    if (jQuery(window).scrollTop() > 150) {
        jQuery("#commentbox").addClass("visible");
    } else {
        jQuery("#commentbox").removeClass("visible");
    }
});
