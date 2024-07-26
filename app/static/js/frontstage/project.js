hljs.highlightAll();

document.addEventListener("DOMContentLoaded", function () {
  function setCarouselImageHeight() {
    var carousel = document.getElementById("carousel");
    var images = carousel.querySelectorAll(".carousel-item img");
    var containerWidth = carousel.clientWidth;

    // Calculate height for 16:9 aspect ratio
    var height = (containerWidth * 9) / 16;

    // Set height and min-height for each image
    images.forEach(function (img) {
      img.style.height = height + "px";
      img.style.minHeight = height + "px";
    });
  }

  // Set the height when the page loads
  setCarouselImageHeight();

  // Adjust the height when the window is resized
  window.addEventListener("resize", setCarouselImageHeight);
});
