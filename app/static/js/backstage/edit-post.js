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
easyMDE.value(postContent);

function validateUpdate() {
  var title = document.getElementById("title").value;
  if (title.trim() === "") {
    alert("You must enter the title for the post.");
    return false;
  }

  var subtitle = document.getElementById("subtitle").value;
  if (subtitle.trim() === "") {
    alert("Add a short description as a subtitle for this post.");
    return false;
  }

  var tags = document.getElementById("tags").value;
  if (tags.trim() === "") {
    alert("You must add one tag to the post at least.");
    return false;
  }
  const tagRegex =
    /^[\u4e00-\u9fa5a-zA-Z\s\-_.]+(,\s*[\u4e00-\u9fa5a-zA-Z\s\-_.]+)*$/;
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
  return true;
}

function preventFormEnter(event) {
  if (event.key === "Enter") {
    event.preventDefault();
  }
}

document.addEventListener("DOMContentLoaded", function () {
  form.addEventListener("keypress", preventFormEnter);
});
