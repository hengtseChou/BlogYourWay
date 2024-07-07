const mobileNavBtn = document.getElementById("mobile-nav-posts");
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

function validateNewPost() {
  var title = document.getElementById("title").value;
  if (title.trim() === "") {
    alert("You must enter the title for the post.");
    return false;
  }

  var subtitle = document.getElementById("subtitle").value;
  if (subtitle.trim() === "") {
    alert("Add a short description for this post as a subtitle.");
    return false;
  }

  var tags = document.getElementById("tags").value;
  if (tags.trim() === "") {
    alert("You must add one tag to the post at least.");
    return false;
  }
  const tagRegex = /^[\u4e00-\u9fa5a-zA-Z\s]+(,\s*[\u4e00-\u9fa5a-zA-Z\s]+)*$/;
  if (!tagRegex.test(tags)) {
    alert("You must separate tags with a comma (',').");
    return false;
  }

  var slug = document.getElementById("slug").value;
  const slugRegex = /^[a-z0-9]+(?:-[a-z0-9]+)*$/;
  if (!slugRegex.test(slug)) {
    alert("Your custom slug is not a URL-friendly string.");
    return false;
  }

  // var cover = document.getElementById("cover").value;
  // if (cover.trim() === "") {
  //   alert("You must add a cover image for the post.");
  //   return false;
  // }

  if (easyMDE.value().trim() === "") {
    alert("Write something for your post!");
    return false;
  }

  return true;
}

function toggleCoverUrl() {
  var coverSection = document.getElementById("cover-section");
  var addButton = document.getElementById("add-cover-button");

  coverSection.style.display = "block";
  addButton.style.display = "none";
}

function toggleSlug() {
  var slugSection = document.getElementById("slug-section");
  var addButton = document.getElementById("add-slug-button");

  slugSection.style.display = "block";
  addButton.style.display = "none";
}

document.addEventListener("DOMContentLoaded", function () {
  const form = document.getElementById("form");
  form.addEventListener("keypress", function (event) {
    if (event.key === "Enter") {
      event.preventDefault();
    }
  });

  var modal = document.getElementById("newPostModal");
  // Listen for the 'hidden.bs.modal' event, which is fired after the modal has been hidden
  modal.addEventListener("hidden.bs.modal", function () {
    var slugSection = document.getElementById("slug-section");
    var slugAddButton = document.getElementById("add-slug-button");

    var coverSection = document.getElementById("cover-section");
    var coverAddButton = document.getElementById("add-cover-button");

    slugSection.style.display = "none";
    slugAddButton.style.display = "block";
    coverSection.style.display = "none";
    coverAddButton.style.display = "block";
  });
});
