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

function toggleSlug() {
  var slugSection = document.getElementById("slug-section");
  var addButton = document.getElementById("add-slug-button");

  slugSection.classList.remove("d-none");
  addButton.classList.add("d-none");
}

function showInputGroup() {
  const inputGroups = document.querySelectorAll(
    "#image-container .additional-image.d-none",
  );
  if (inputGroups.length > 0) {
    inputGroups[0].classList.remove("d-none");
  } else {
    alert("You can have at most 5 images in your project cover.");
  }
}

function clearInputGroupThenHide(button) {
  const inputGroup = button.closest(".input-group");
  if (inputGroup) {
    inputGroup.classList.add("d-none");
    const inputs = inputGroup.querySelectorAll("input");
    const selects = inputGroup.querySelectorAll("select");
    inputs.forEach((input) => (input.value = ""));
    selects.forEach((select) => (select.value = select.options[0].value));
  }
}
function validateNewProject() {
  var title = document.getElementById("title").value;
  if (title.trim() === "") {
    alert("You must enter the title for the project.");
    return false;
  }

  var desc = document.getElementById("desc").value;
  if (desc.trim() === "") {
    alert("You must a short description for the project.");
    return false;
  }

  var tags = document.getElementById("tags").value;
  if (tags.trim() === "") {
    alert("You must add at least one tag to the project.");
    return false;
  }
  const tagRegex = /^[\u4e00-\u9fa5a-zA-Z\s]+(,\s*[\u4e00-\u9fa5a-zA-Z\s]+)*$/;
  if (!tagRegex.test(tags)) {
    alert("Tags must be separated by a comma (',').");
    return false;
  }

  var url0 = document.getElementById("url0").value;
  if (url0.trim() === "") {
    alert("You must insert at least 1 image for the project.");
    return false;
  }

  const urlRegex =
    /https?:\/\/(www\.)?[-a-zA-Z0-9@:%._\+~#=]{1,256}\.[a-zA-Z0-9()]{1,6}\b([-a-zA-Z0-9()@:%_\+.~#?&//=]*)/;
  var projectImgs = document.querySelectorAll(".project-img");
  for (var i = 0; i < projectImgs.length; i++) {
    let url = projectImgs[i].value.trim();
    if (url !== "" && !urlRegex.test(url)) {
      alert("Invalid URL for image " + (i + 1));
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
    alert("Write something for your project!");
    return false;
  }

  return true;
}

document.addEventListener("DOMContentLoaded", function () {
  const form = document.getElementById("form");
  form.addEventListener("keypress", function (event) {
    if (event.key === "Enter") {
      event.preventDefault();
    }
  });

  var modal = document.getElementById("newProjectModal");
  // Listen for the 'hidden.bs.modal' event, which is fired after the modal has been hidden
  modal.addEventListener("hidden.bs.modal", function () {
    var slugSection = document.getElementById("slug-section");
    var addButton = document.getElementById("add-slug-button");

    slugSection.classList.add("d-none");
    addButton.classList.remove("d-none");
  });
});
