function isUniqueEmail(email) {
  const baseUrl = window.location.origin;
  const url = `${baseUrl}/is-unique`; // Replace with your actual endpoint URL
  const params = new URLSearchParams({ email: email });

  return fetch(`${url}?${params}`, {
    method: "GET",
    headers: {
      "Content-Type": "application/json",
    },
  })
    .then((response) => {
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      return response.json();
    })
    .then((result) => {
      if (typeof result === "boolean") {
        return result;
      } else {
        throw new Error("Unexpected response format");
      }
    })
    .catch((error) => {
      console.error("There was a problem with the fetch operation:", error);
      return false; // Default to false in case of an error
    });
}

function isUniqueUsername(username) {
  const baseUrl = window.location.origin;
  const url = `${baseUrl}/is-unique`; // Replace with your actual endpoint URL
  const params = new URLSearchParams({ username: username });

  return fetch(`${url}?${params}`, {
    method: "GET",
    headers: {
      "Content-Type": "application/json",
    },
  })
    .then((response) => {
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      return response.json();
    })
    .then((result) => {
      if (typeof result === "boolean") {
        return result;
      } else {
        throw new Error("Unexpected response format");
      }
    })
    .catch((error) => {
      console.error("There was a problem with the fetch operation:", error);
      return false; // Default to false in case of an error
    });
}

function validateStep1() {
  // Perform input validation for Step 1
  var email = document.getElementById("email").value;
  var password = document.getElementById("password").value;

  // both fields not empty
  if (email.trim() === "" || password.trim() === "") {
    alert("Enter email and password to continue.");
    return false;
  }

  var emailRegex = /^\S+@\S+\.\S+$/;
  if (!emailRegex.test(email)) {
    alert("Enter a valid email address.");
    return false;
  }

  var passwordRegex = /^(?=.*[a-z])(?=.*[A-Z]).{8,}$/;
  if (!passwordRegex.test(password)) {
    alert(
      "Password must be 8 characters long and contain both uppercase and lowercase letters.",
    );
    return false;
  }

  isUniqueEmail(email).then((isUnique) => {
    if (isUnique) {
      // Hide Step 1, show Step 2
      document.getElementById("step1").classList.add("hide");
      document.getElementById("step1").style.display = "none";

      document.getElementById("step2").style.display = "block";
      setTimeout(function () {
        document.getElementById("step2").classList.remove("hide");
      }, 100);
    } else {
      alert("This email is already registered. Please try another one.");
      return false;
    }
  });
}

function validateStep2() {
  // Perform input validation for Step 2
  var username = document.getElementById("username").value;
  var blogname = document.getElementById("blogname").value;
  var termsChecked = document.getElementById("terms").checked;

  if (username.trim() === "" || blogname.trim() === "") {
    alert("Enter username and blog name to continue.");
    return false;
  }

  if (username[0] === "-" || username[username.length - 1] === "-") {
    alert("Username cannot begins or ends with a hyphen.");
    return false;
  }

  var usernameRegex = /^[a-z0-9](?:[a-z0-9\-]*[a-z0-9])?$/;
  if (!usernameRegex.test(username)) {
    alert(
      'Invalid username. Please use only letters (lowercase), numbers, and "-".',
    );
    return false;
  }

  if (!termsChecked) {
    alert("You must read the terms to continue.");
    return false;
  }

  return isUniqueUsername(username)
    .then((isUnique) => {
      if (isUnique) {
        // Hide Step 1, show Step 2
        return true;
      } else {
        alert(
          "This username is already taken. Please choose another username.",
        );
        return false;
      }
    })
    .catch((error) => {
      console.error("Error checking username uniqueness:", error);
      return false;
    });
}
// Update the form submission logic to use the validateStep2 function
document.querySelector("form").addEventListener("submit", function (event) {
  event.preventDefault(); // Prevent default form submission
  validateStep2().then((isValid) => {
    if (isValid) {
      this.submit(); // Proceed with form submission if validation passes
    }
  });
});

document.getElementById("step1").addEventListener("keypress", function (event) {
  if (event.key === "Enter") {
    event.preventDefault();
  }
});
