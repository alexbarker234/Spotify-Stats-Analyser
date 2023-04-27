$(window).on("load", function () {
    path = window.location.pathname.split("/");
    path.shift();
    if (path[0] === "stats" && path[1] === "track" && path[2]) {
        console.log("test");
        loadTrackStats(path[2]);
    }
});

function loadTrackStats(trackID) {
    console.log(trackID);
    $.getJSON(`/track-data/${trackID}`).done(function (data) {
        $("#album-art").append($("<img>", { src: data.imageUrl }));
        $("#total-streams").append($("<p>", { html: data.totalListens }));
        $("#total-minutes").append($("<p>", { html: data.totalMinutes }));
        $("#title").html(data.name);
    });
    $.getJSON(`/listens-graph/${trackID}`).done(function (data) {
        // add 0 values in missing days
        newData = [];
        for (let i = 0; i < data.length - 1; i++) {
            const currentDate = new Date(data[i].day);
            const nextDate = new Date(data[i + 1].day);
            newData.push(data[i]);
            while (currentDate.getTime() !== nextDate.getTime() - 86400000) {
                currentDate.setDate(currentDate.getDate() + 1);
                newData.push({
                    day: currentDate.toISOString().slice(0, 10),
                    listens: 0,
                });
            }
        }
        data = newData;

        const xValues = data.map((obj) => obj.day);
        const dataArr = data.map((obj) => obj.listens);

        new Chart("streamChart", {
            type: "line",
            data: {
                labels: xValues,
                datasets: [
                    {
                        data: dataArr,
                        //borderColor: "#1DB954",
                        borderColor: function (context) {
                            const chart = context.chart;
                            const { ctx, chartArea } = chart;

                            if (!chartArea) return;
                            
                            return getGradient(ctx, chartArea);
                        },
                        borderWidth: 2,
                        fill: false,
                        spanGaps: true,
                    },
                ],
            },
            options: {
                maintainAspectRatio: false,
                legend: { display: false },
                elements: {
                    point: {
                        radius: 0,
                    },
                },
                scales: {
                    xAxes: [
                        {
                            gridLines: {
                                display: false,
                            },
                            type: "time",
                            time: {
                                unit: "month",
                            },
                        },
                    ],
                    yAxes: [
                        {
                            gridLines: {
                                display: false,
                            },
                            ticks: {
                                beginAtZero: true,
                            },
                        },
                    ],
                },
            },
        });
    });
    $.getJSON(`https://spotify-lyric-api.herokuapp.com/?trackid=${trackID}`)
        .done(function (data) {
            for (let i = 0; i < 2; i++) {
                data.lines.forEach((element) =>
                    $("#lyrics").append(
                        $("<div>", { class: "lyric-line", html: element.words })
                    )
                );
            }
        })
        // try genius lyrics if spotify ones r broken
        .fail(function (jqxhr, textStatus, error) {
            $.getJSON(`/genius-lyrics/${trackID}`)
                .done(function (data) {
                    for (let i = 0; i < 2; i++) {
                        data.forEach((element) =>
                            $("#lyrics").append(
                                $("<div>", {
                                    class: "lyric-line",
                                    html: element,
                                })
                            )
                        );
                    }
                })
                .fail(function () {
                    console.log("could not get lyrics");
                });
        });
}

let width, height, gradient;
function getGradient(ctx, chartArea) {
    const chartWidth = chartArea.right - chartArea.left;
    const chartHeight = chartArea.bottom - chartArea.top;
    if (!gradient || width !== chartWidth || height !== chartHeight) {
        // Create the gradient because this is either the first render
        // or the size of the chart has changed
        width = chartWidth;
        height = chartHeight;
        gradient = ctx.createLinearGradient(
            chartArea.left,
            0,
            chartArea.right,
            0
        );

        var style = getComputedStyle(document.body)
        gradient.addColorStop(0, style.getPropertyValue('--purple'));
        gradient.addColorStop(1, style.getPropertyValue('--red'));
    }

    return gradient;
}
