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
