// Function to set carousel image height
function setCarouselImageHeight() {
  const carousel = document.getElementById("carousel");
  const images = carousel.querySelectorAll(".carousel-item img");
  const containerWidth = carousel.clientWidth;

  // Calculate height for 16:9 aspect ratio
  const height = (containerWidth * 9) / 16;

  // Set height and min-height for each image
  images.forEach(function (img) {
    img.style.height = height + "px";
    img.style.minHeight = height + "px";
  });
}

// Function to initialize the carousel image height setting
function initializeCarouselImageHeight() {
  // Set the height when the page loads
  setCarouselImageHeight();

  // Adjust the height when the window is resized
  window.addEventListener("resize", setCarouselImageHeight);
}

// Attach syntax highlighting
hljs.highlightAll();

// Attach all event listeners and initializations inside DOMContentLoaded
document.addEventListener("DOMContentLoaded", function () {
  initializeCarouselImageHeight();
});
