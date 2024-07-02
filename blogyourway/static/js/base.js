// notification (toast) from flask
document.addEventListener("DOMContentLoaded", function () {
  setTimeout(function () {
    var notification = document.getElementById("notification");
    if (notification) {
      notification.style.opacity = "0";
      setTimeout(function () {
        notification.style.display = "none";
      }, 300);
    }
  }, 3000);
});

// update year tag in the footer
function updateCurrentYear() {
  var currentDate = new Date();
  var currentYear = currentDate.getFullYear();
  var yearTag = document.getElementById("yearTag");
  if (yearTag) {
    yearTag.innerHTML = currentYear;
  }
  var yearTagMobile = document.getElementById("yearTagMobile");
  if (yearTagMobile) {
    yearTagMobile.innerHTML = currentYear;
  }
}
updateCurrentYear();
