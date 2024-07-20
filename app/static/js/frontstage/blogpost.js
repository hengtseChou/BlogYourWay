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
