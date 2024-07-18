const mobileNavBtn = document.getElementById("mobile-nav-posts");
mobileNavBtn.style.color = "white";

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

  var coverUrl = document.getElementById("cover_url").value;
  if (coverUrl.trim() !== "") {
    // Only validate non-empty URLs
    const urlRegex =
      /^(https?:\/\/)?([\da-z\.-]+)\.([a-z\.]{2,6})([\/\w \.-]*)*\/?$/;
    if (!urlRegex.test(coverUrl)) {
      alert("Please enter a valid URL for the cover image.");
      return false;
    }
  }

  var slug = document.getElementById("custom_slug").value;
  if (slug.trim() !== "") {
    // Only validate non-empty slugs
    const slugRegex = /^[a-z0-9]+(?:-[a-z0-9]+)*$/;
    if (!slugRegex.test(slug)) {
      alert(
        "Your custom slug is invalid. Use only lowercase letters, numbers, and hyphens. Must start and end with a letter or number.",
      );
      return false;
    }
  }

  if (easyMDE.value().trim() === "") {
    alert("Your post cannot be empty!");
    return false;
  }
  console.log("Validation passed");

  return true;
}

function toggleCoverUrl() {
  var coverSection = document.getElementById("cover-section");
  var addButton = document.getElementById("add-cover-button");

  coverSection.classList.remove("d-none");
  addButton.classList.add("d-none");
}

function toggleSlug() {
  var slugSection = document.getElementById("slug-section");
  var addButton = document.getElementById("add-slug-button");

  slugSection.classList.remove("d-none");
  addButton.classList.add("d-none");
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

    slugSection.classList.add("d-none");
    slugAddButton.classList.remove("d-none");
    coverSection.classList.add("d-none");
    coverAddButton.classList.remove("d-none");
  });
});
