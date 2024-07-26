function onSubmit(token) {
  document.getElementById("comment-form").submit();
}

function fetchReplacementImage(imgElement) {
  const originalSrc = imgElement.getAttribute("src");
  fetch(originalSrc)
    .then((response) => response.json())
    .then((data) => {
      if (data.imageUrl) {
        imgElement.setAttribute("src", data.imageUrl);
      } else {
        console.error("Image URL not found in the response.");
      }
    })
    .catch((error) =>
      console.error(`Error fetching replacement image: ${error}`),
    );
}

function sendReadCountRequest() {
  fetch("/readcount-increment?post_uid={{ post.post_uid }}").catch((error) =>
    console.error(`Error incrementing read count: ${error}`),
  );
}

function preventFormEnter(event) {
  if (event.key === "Enter") {
    event.preventDefault();
  }
}

hljs.highlightAll();
const tocContainer = document.querySelector(".toc");
tocContainer.classList.add("d-none");

document.addEventListener("DOMContentLoaded", function () {
  document.querySelectorAll(".ajax-profile-pic").forEach(fetchReplacementImage);
  setTimeout(sendReadCountRequest, 60);
  document
    .getElementById("comment-form")
    .addEventListener("keypress", preventFormEnter);
});

document.addEventListener("DOMContentLoaded", function () {
  var topLevelUl = tocContainer.querySelector("ul");
  if (topLevelUl && topLevelUl.children.length > 0) {
    tocContainer.classList.remove("d-none");
    // Add the Table of Contents heading
    var tocHeading = document.createElement("h3");
    tocHeading.textContent = "Table of Contents";
    tocContainer.insertBefore(tocHeading, tocContainer.firstChild);

    // Function to add class based on depth
    function addTocLevelClass(ulElement, level) {
      var items = ulElement.children;
      for (var i = 0; i < items.length; i++) {
        var item = items[i];
        if (item.tagName.toLowerCase() === "li") {
          item.classList.add("toclevel-" + level);

          // Check for nested UL and apply classes recursively
          var nestedUl = item.querySelector("ul");
          if (nestedUl) {
            addTocLevelClass(nestedUl, level + 1);
          }
        }
      }
    }

    // Start the process from the top level UL
    addTocLevelClass(topLevelUl, 1);
  }
});
