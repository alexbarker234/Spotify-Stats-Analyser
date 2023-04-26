$(window).on("load", function () {
    if (window.location.pathname === "/stats") {
        loadStats();
    }
});

function loadStats() {
    console.log("loading");
    $.getJSON("/total-listens").done(function (data) {
        let artistDiv = $("#total-listens");
        console.log(data);
        artistDiv.html(data);
    });
    $.getJSON("/top-tracks/50").done(function (data) {
        //console.log(data);
        let index = 0;
        data.forEach((track) => {
            let topTracksDiv = $("#top-tracks");
            trackDiv = $("<div>", { class: "track-container" }).css({
                "animation-delay": `${index * 0.03}s`,
            });
            trackImage = $("<img>", { src: track.image_url })
            trackImage.click(function(e) {
                let newURL = window.location.href + `/track/${track.id}`
                location.href = newURL
            })
            trackDiv.append(trackImage);
            trackDiv.append(
                $("<p>", {
                    class: "track-title",
                    html: `${index + 1}. ${track.name}`,
                })
            );
            trackDiv.append(
                $("<p>", {
                    class: "track-details",
                    html: `${track.listens} streams • ${track.minutes ?? ""}`,
                })
            );
            topTracksDiv.append(trackDiv);
            index++;
        });
    });
}
