const mobileNavBtn = document.getElementById("mobile-nav-settings");
mobileNavBtn.style.color = "white";

function validatePasswords() {
  // Get the input values
  var currentPassword = document.getElementById("current").value;
  var newPassword = document.getElementById("new").value;
  var confirmNewPassword = document.getElementById("confirm").value;

  // Regular expression to check valid password format (at least 6 characters)
  var passwordFormat = /^(?=.*[a-z])(?=.*[A-Z]).{8,}$/;

  // Check if current password is valid (not empty and matches the format)
  if (!currentPassword.match(passwordFormat)) {
    alert(
      "Current password is invalid. It should be at least 6 characters long and contain both letters and numbers.",
    );
    return false;
  }

  // Check if new password is valid (not empty and matches the format)
  if (!newPassword.match(passwordFormat)) {
    alert(
      "New password is invalid. It should be at least 8 characters long and contain both uppercases and lowercases.",
    );
    return false;
  }

  // Check if new password matches the confirmed new password
  if (newPassword !== confirmNewPassword) {
    alert("New password and Confirm new password do not match.");
    return false;
  }

  // All checks pass, proceed with your logic here
  return true;
}

document
  .getElementById("general-form")
  .addEventListener("keypress", function (event) {
    if (event.key === "Enter") {
      event.preventDefault();
    }
  });

document
  .getElementById("changepw-form")
  .addEventListener("keypress", function (event) {
    if (event.key === "Enter") {
      event.preventDefault();
    }
  });

// Define helper functions outside the event listener
function createInputGroup(orderNumber) {
  const div = document.createElement("div");
  div.className = "input-group mb-2";

  const span = createSpan(orderNumber);
  const input = createInput(orderNumber);
  const select = createSelect(orderNumber);
  const button = createRemoveButton();

  div.append(span, input, select, button);
  return div;
}

function createSpan(orderNumber) {
  const span = document.createElement("span");
  span.className = "input-group-text";
  span.textContent = "Link " + orderNumber;
  return span;
}

function createInput(orderNumber) {
  const input = document.createElement("input");
  input.type = "text";
  input.className = "form-control";
  input.name = "url-" + orderNumber;
  input.placeholder = "Url goes here";
  return input;
}

function createSelect(orderNumber) {
  const select = document.createElement("select");
  select.className = "form-select";
  select.name = "platform-" + orderNumber;
  ["facebook", "instagram", "twitter", "medium", "linkedin", "github"].forEach(
    (platform) => {
      const option = document.createElement("option");
      option.value = platform;
      option.textContent = platform.charAt(0).toUpperCase() + platform.slice(1);
      select.appendChild(option);
    },
  );
  return select;
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
  inputCount--;
  updateOrderNumbers();
}

function updateOrderNumbers() {
  const inputGroups = document.querySelectorAll(".input-group");
  inputGroups.forEach((group, index) => {
    const orderNumber = index + 1;
    group.querySelector(".input-group-text").textContent =
      "Link " + orderNumber;
    group.querySelector("input").name = "url-" + orderNumber;
    group.querySelector("select").name = "platform-" + orderNumber;
  });
}

document.addEventListener("DOMContentLoaded", function () {
  const maxInputs = 5;
  const inputWrapper = document.querySelector("#inputContainer");
  const addButton = document.querySelector("#add");
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
