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
easyMDE.value(changelogContent);

const elem = document.getElementById("date");
const datepicker = new Datepicker(elem, {
  buttonClass: "btn",
});

function validateUpdate() {
  var title = document.getElementById("title").value;
  if (title.trim() === "") {
    alert("You must enter the title for the changelog.");
    return false;
  }

  var date = document.getElementById("date").value;
  if (date.trim() === "") {
    alert("You must enter the date for the changelog.");
    return false;
  }

  var category = document.getElementById("category").value;
  if (category.trim() === "") {
    alert("You must select a category for the changelog.");
    return false;
  }

  var tags = document.getElementById("tags").value;
  if (tags.trim() === "") {
    alert("You must add one tag to the changelog at least.");
    return false;
  }
  const tagRegex = /^[\u4e00-\u9fa5a-zA-Z\s]+(,\s*[\u4e00-\u9fa5a-zA-Z\s]+)*$/;
  if (!tagRegex.test(tags)) {
    alert("You must separate tags with a comma (',').");
    return false;
  }

  var link = document.getElementById("link").value;
  if (link.trim() !== "") {
    // Only validate non-empty URLs
    const urlRegex =
      /https?:\/\/(www\.)?[-a-zA-Z0-9@:%._\+~#=]{1,256}\.[a-zA-Z0-9()]{1,6}\b([-a-zA-Z0-9()@:%_\+.~#?&//=]*)/;
    if (!urlRegex.test(link)) {
      alert("Please enter a valid URL.");
      return false;
    }
  }

  if (easyMDE.value().trim() === "") {
    alert("The changelog content cannot be empty!");
    return false;
  }

  return true;
}

// Define the function to set today's date
function setTodayDate() {
  const today = new Date();
  const day = String(today.getDate()).padStart(2, "0");
  const month = String(today.getMonth() + 1).padStart(2, "0");
  const year = today.getFullYear();

  const formattedDate = `${month}/${day}/${year}`;
  document.getElementById("date").value = formattedDate;
}

// Add event listener inside DOMContentLoaded
document.addEventListener("DOMContentLoaded", function () {
  const todayBtn = document.getElementById("today");
  todayBtn.addEventListener("click", setTodayDate);
});
