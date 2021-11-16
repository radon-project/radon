// //to disable cut, copy and paste
// $('html').bind('cut copy paste', function (e) {
//     e.preventDefault();
// });

// //to disable the entire page 
// $('html').bind('cut copy paste', function (e) {
//     e.preventDefault();
// });

// //to disable the entire page
// $("html").on("contextmenu", function (e) {
//     return false;
// });

function copyIt() {
    var copyText = document.getElementById("sharelink");
    copyText.select();
    copyText.setSelectionRange(0, 99999);
    document.execCommand("copy");
    var btn = document.getElementById("btn");
    btn.innerHTML = "<div><span class='fas fa-check'></span>Copied</div>";
    setTimeout(function () {
        btn.innerText = "Copy";
    }, 3000);
};
