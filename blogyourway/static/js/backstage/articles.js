const mobileNavBtn = document.getElementById("mobile-nav-articles");
mobileNavBtn.style.color = "white";

const tooltipTriggerList = document.querySelectorAll(
  '[data-bs-toggle="tooltip"]',
);
const tooltipList = [...tooltipTriggerList].map(
  (tooltipTriggerEl) => new bootstrap.Tooltip(tooltipTriggerEl),
);

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

document.addEventListener("DOMContentLoaded", function () {
  const form = document.getElementById("form");
  form.addEventListener("keypress", function (event) {
    if (event.key === "Enter") {
      event.preventDefault();
    }
  });
});

function validateNewPost() {
  var title = document.getElementById("title").value;
  if (title.trim() === "") {
    alert("You must enter the title for the article.");
    return false;
  }

  var subtitle = document.getElementById("subtitle").value;
  if (subtitle.trim() === "") {
    alert("Add a short description for this article as a subtitle.");
    return false;
  }

  var tags = document.getElementById("tags").value;
  if (tags.trim() === "") {
    alert("You must add one tag to the article at least.");
    return false;
  }
  const tagRegex = /^[\u4e00-\u9fa5a-zA-Z\s]+(,\s*[\u4e00-\u9fa5a-zA-Z\s]+)*$/;
  if (!tagRegex.test(tags)) {
    alert("You must separate tags with a comma (',').");
    return false;
  }

  var cover = document.getElementById("cover").value;
  if (cover.trim() === "") {
    alert("You must add a cover image for the article.");
    return false;
  }

  if (easyMDE.value().trim() === "") {
    alert("You did not write anything for your article!");
    return false;
  }

  return true;
}
