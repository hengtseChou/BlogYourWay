const mobileNavBtn = document.getElementById("mobile-nav-projects");
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
easyMDE.value(projectContent);

function createInputGroup(orderNumber) {
  const div = document.createElement("div");
  div.className = "input-group mb-2";

  const span = createSpan(orderNumber);
  const input = createInput(orderNumber);
  const select = createCaption(orderNumber);
  const button = createRemoveButton();

  div.append(span, input, select, button);
  return div;
}

function createSpan(orderNumber) {
  const span = document.createElement("span");
  span.className = "input-group-text";
  span.textContent = "Image " + orderNumber;
  return span;
}

function createInput(orderNumber) {
  const input = document.createElement("input");
  input.type = "text";
  input.className = "form-control project-img";
  input.name = "url-" + orderNumber;
  input.placeholder = "url";
  return input;
}

function createCaption(orderNumber) {
  const input = document.createElement("input");
  input.type = "text";
  input.className = "form-control project-img-caption";
  input.name = "caption-" + orderNumber;
  input.placeholder = "caption";
  return input;
}

function createRemoveButton() {
  const button = document.createElement("button");
  button.className = "btn btn-remove panel-btn";
  button.setAttribute("aria-label", "Close");
  button.textContent = "Remove";
  button.addEventListener("click", handleRemove);
  return button;
}

function handleRemove(event) {
  event.preventDefault();
  event.target.closest(".input-group").remove();
  updateOrderNumbers();
}

function updateOrderNumbers() {
  const inputGroups = document.querySelectorAll(".input-group");
  inputGroups.forEach((group, index) => {
    const orderNumber = index + 1;
    group.querySelector(".input-group-text").textContent =
      "Image " + orderNumber;
    group.querySelector(".project-img").name = "url-" + orderNumber;
    group.querySelector(".project-img-caption").name = "caption-" + orderNumber;
  });
}

function validateUpdate() {
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

  var slug = document.getElementById("slug").value;
  const slugRegex = /^[a-z0-9]+(?:-[a-z0-9]+)*$/;
  if (!slugRegex.test(slug)) {
    alert("Your custom slug is not a URL-friendly string.");
    return false;
  }

  if (easyMDE.value().trim() === "") {
    alert("Write something for your project!");
    return false;
  }

  var url1 = document.getElementById("url-1").value;
  if (url1.trim() === "") {
    alert("You must insert an image for the project.");
    return false;
  }

  const urlRegex =
    /^(https?:\/\/)?([\da-z\.-]+)\.([a-z\.]{2,6})([\/\w \.-]*)*\/?$/;
  var projectImgs = document.querySelectorAll(".project-img");
  for (var i = 0; i < projectImgs.length; i++) {
    if (!urlRegex.test(projectImgs[i].value.trim())) {
      alert("Invalid url for image " + (i + 1));
      return false;
    }
  }

  return true;
}

document.addEventListener("DOMContentLoaded", function () {
  const maxInputs = 5;
  const inputWrapper = document.querySelector("#inputContainer");
  const addButton = document.querySelector("#add-more-image");
  let inputCount = 1;

  function addInputField(orderNumber) {
    const inputGroup = createInputGroup(orderNumber);
    inputWrapper.appendChild(inputGroup);
    updateOrderNumbers();
  }

  addButton.addEventListener("click", function (e) {
    e.preventDefault();
    if (inputCount < maxInputs) {
      addInputField(++inputCount);
    }
  });

  inputWrapper.addEventListener("click", function (e) {
    if (e.target.classList.contains("btn-remove")) {
      e.preventDefault();
      e.target.closest(".input-group").remove();
      inputCount--;
      updateOrderNumbers();
    }
  });
});
