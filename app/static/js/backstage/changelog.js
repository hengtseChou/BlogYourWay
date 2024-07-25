const easyMDE = new EasyMDE({
  element: document.getElementById("editor"),
  autofocus: true,
  toolbar: [
    "bold",
    "italic",
    "heading",
    "|",
    "undo",
    "redo",
    "|",
    "code",
    "quote",
    "unordered-list",
    "ordered-list",
    "horizontal-rule",
    "|",
    "link",
    "image",
    "|",
    "preview",
    "guide",
  ],
  minHeight: "200px",
  spellChecker: false,
});

const elem = document.getElementById("date");
const datepicker = new Datepicker(elem, {
  buttonClass: "btn",
});

function toggleLink() {
  var linkSection = document.getElementById("link-section");
  var addButton = document.getElementById("add-link-button");

  linkSection.classList.remove("d-none");
  addButton.classList.add("d-none");
}

document.addEventListener("DOMContentLoaded", function () {
  const form = document.getElementById("form");
  form.addEventListener("keypress", function (event) {
    if (event.key === "Enter") {
      event.preventDefault();
    }
  });

  var modal = document.getElementById("newChangelogModal");
  // Listen for the 'hidden.bs.modal' event, which is fired after the modal has been hidden
  modal.addEventListener("hidden.bs.modal", function () {
    var linkSection = document.getElementById("link-section");
    var addButton = document.getElementById("add-link-button");

    linkSection.classList.add("d-none");
    addButton.classList.remove("d-none");
  });
});

document.getElementById("today").addEventListener("click", function () {
  const today = new Date();
  const day = String(today.getDate()).padStart(2, "0");
  const month = String(today.getMonth() + 1).padStart(2, "0");
  const year = today.getFullYear();

  const formattedDate = `${month}/${day}/${year}`;
  document.getElementById("date").value = formattedDate;
});
