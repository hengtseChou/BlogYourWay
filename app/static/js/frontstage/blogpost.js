// Define the function to handle form submission with a token
function onSubmit(token) {
  document.getElementById("comment-form").submit();
}

// Define the function to fetch replacement images
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

// Define the function to send the read count request
function sendReadCountRequest() {
  fetch("/readcount-increment?post_uid={{ post.post_uid }}").catch((error) =>
    console.error(`Error incrementing read count: ${error}`),
  );
}

// Define the function to prevent form submission on Enter key press
function preventFormEnter(event) {
  if (event.key === "Enter") {
    event.preventDefault();
  }
}

// Define the function to setup the Table of Contents
function setupTableOfContents() {
  const tocContainer = document.querySelector(".toc");
  const topLevelUl = tocContainer.querySelector("ul");
  if (topLevelUl && topLevelUl.children.length > 0) {
    tocContainer.classList.remove("d-none");

    // Add the Table of Contents heading
    const tocHeading = document.createElement("h3");
    tocHeading.textContent = "Table of Contents";
    tocContainer.insertBefore(tocHeading, tocContainer.firstChild);

    // Function to add class based on depth
    function addTocLevelClass(ulElement, level) {
      const items = ulElement.children;
      for (let i = 0; i < items.length; i++) {
        const item = items[i];
        if (item.tagName.toLowerCase() === "li") {
          item.classList.add("toclevel-" + level);

          // Check for nested UL and apply classes recursively
          const nestedUl = item.querySelector("ul");
          if (nestedUl) {
            addTocLevelClass(nestedUl, level + 1);
          }
        }
      }
    }

    // Start the process from the top level UL
    addTocLevelClass(topLevelUl, 1);
  }
}

// Attach syntax highlighting
hljs.highlightAll();

// Initialize Table of Contents container as hidden
const tocContainer = document.querySelector(".toc");
tocContainer.classList.add("d-none");

// Attach all event listeners and initializations inside DOMContentLoaded
document.addEventListener("DOMContentLoaded", function () {
  document.querySelectorAll(".ajax-profile-pic").forEach(fetchReplacementImage);
  setTimeout(sendReadCountRequest, 60);
  const form = document.getElementById("comment-form");
  form.addEventListener("keypress", preventFormEnter);
  setupTableOfContents();
});
