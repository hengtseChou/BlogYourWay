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
easyMDE.value(userAbout);

const form = document.getElementById("form");
form.addEventListener("keypress", function (event) {
  if (event.key === "Enter") {
    event.preventDefault();
  }
});
