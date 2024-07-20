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

// convert utc time from server side to local time from client side
function convertUTCToLocal() {
  const timezone = Intl.DateTimeFormat().resolvedOptions().timeZone;
  const formatSettings = {
    "utc-to-local-long": {
      timeZone: timezone,
      year: "numeric",
      month: "2-digit",
      day: "2-digit",
      hour: "2-digit",
      minute: "2-digit",
      second: "2-digit",
      hour12: false,
    },
    "utc-to-local-medium": {
      timeZone: timezone,
      year: "numeric",
      month: "2-digit",
      day: "2-digit",
    },
    "utc-to-local-short": {
      timeZone: timezone,
      year: "numeric",
      month: "long",
      day: "numeric",
    },
  };

  Object.keys(formatSettings).forEach((className) => {
    const elements = document.querySelectorAll("." + className);
    elements.forEach((element) => {
      const utcDateString = element.textContent.trim();
      const date = new Date(utcDateString + "Z"); // Adding 'Z' to specify UTC

      if (className === "utc-to-local-long") {
        const optionsDate = {
          timeZone: timezone,
          year: "numeric",
          month: "2-digit",
          day: "2-digit",
        };
        const optionsTime = {
          timeZone: timezone,
          hour: "2-digit",
          minute: "2-digit",
          second: "2-digit",
          hour12: false,
        };
        const localDate = date.toLocaleDateString("en-CA", optionsDate);
        const localTime = date.toLocaleTimeString("en-CA", optionsTime);
        element.textContent = `${localDate} ${localTime}`;
      } else {
        const localDateString = date.toLocaleString(
          "en-CA",
          formatSettings[className],
        );
        element.textContent = localDateString;
      }
    });
  });
}

updateCurrentYear();
convertUTCToLocal();
