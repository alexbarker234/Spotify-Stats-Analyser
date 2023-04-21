$(window).on('load', function () {
    if (window.location.pathname === '/stats') {
        loadStats()
    }
})

function loadStats() {
    console.log("loading")
    $.getJSON('/total-listens').done(function (data) {
        let artistDiv = $('#total-listens');
        console.log(data)
        artistDiv.html(data)
    })
}
