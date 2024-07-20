function showInputGroup() {
  const inputGroups = document.querySelectorAll(
    "#link-container .input-group.d-none",
  );
  if (inputGroups.length > 0) {
    inputGroups[0].classList.remove("d-none");
  } else {
    alert("You can have at most 5 social links.");
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

function validateNewPassword() {
  // Get the input values
  var newPassword = document.getElementById("pw-new_pw").value;
  var confirmNewPassword = document.getElementById("pw-new_pw_repeat").value;

  // Regular expression to check valid password format (at least 6 characters)
  var passwordFormat = /^(?=.*[a-z])(?=.*[A-Z]).{8,}$/;

  // Check if new password is valid (not empty and matches the format)
  if (!newPassword.match(passwordFormat)) {
    alert(
      "Invalid new password. It should be at least 8 characters long and contain both uppercases and lowercases.",
    );
    return false;
  }

  // Check if new password matches the confirmed new password
  if (newPassword !== confirmNewPassword) {
    alert("Confirmation of the new password failed.");
    return false;
  }

  // All checks pass, proceed with your logic here
  return true;
}

function preventFormSubmitOnEnter(form) {
  form.addEventListener("keydown", function (event) {
    if (event.key === "Enter" || event.keyCode === 13) {
      event.preventDefault();
    }
  });
}

function addListenersToAllForms() {
  const forms = document.querySelectorAll("form");
  forms.forEach((form) => preventFormSubmitOnEnter(form));
}

document.addEventListener("DOMContentLoaded", addListenersToAllForms);
