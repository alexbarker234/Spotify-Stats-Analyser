$(window).on("load", function () {
    buttons = $('.nav-button')
    let index = -1;
    buttons.each(i => {
        if (window.location.href.startsWith(buttons[i].href)) 
            index = i;    
    });
    if (index != -1) buttons[index].classList.add('selected')
});
