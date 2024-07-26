function convertUTCToLocalYear() {
  const elements = document.querySelectorAll(".utc-to-local-year");
  elements.forEach((element) => {
    const utcDate = new Date(element.textContent.trim());
    const localYear = utcDate.getFullYear();
    element.textContent = localYear;
  });
}

function convertUTCToLocalMonthDay() {
  const elements = document.querySelectorAll(".utc-to-local-month-day");
  elements.forEach((element) => {
    const utcDate = new Date(element.textContent.trim());
    const options = { month: "long" };
    const localMonth = utcDate.toLocaleDateString(undefined, options);
    const localDay = utcDate.getDate();
    element.textContent = `${localMonth}, ${localDay}`;
  });
}

hljs.highlightAll();

// Call the functions after the DOM is fully loaded
document.addEventListener("DOMContentLoaded", function () {
  convertUTCToLocalYear();
  convertUTCToLocalMonthDay();
});
