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

document.addEventListener("DOMContentLoaded", () => {
  document.querySelectorAll(".ajax-profile-pic").forEach(fetchReplacementImage);
  setTimeout(sendReadCountRequest, 30000);
  document
    .getElementById("comment-form")
    .addEventListener("keypress", preventFormEnter);
});

document.addEventListener("DOMContentLoaded", function () {
  // Select the TOC container
  var tocContainer = document.querySelector(".toc");

  if (tocContainer) {
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
    var topLevelUl = tocContainer.querySelector("ul");
    if (topLevelUl) {
      addTocLevelClass(topLevelUl, 1);
    }
  } else {
    // Modify the first paragraph tag in the div with class 'blogpost-content'
    var blogPostContent = document.querySelector(".blogpost-content");
    if (blogPostContent) {
      var firstParagraph = blogPostContent.querySelector("p");
      if (firstParagraph && firstParagraph.textContent.length > 5) {
        firstParagraph.textContent = firstParagraph.textContent.slice(5);
      }
    }
  }
});
