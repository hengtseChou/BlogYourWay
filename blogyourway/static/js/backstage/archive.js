const mobileNavBtn = document.getElementById("mobile-nav-archive");
mobileNavBtn.style.color = "white";

document.addEventListener("DOMContentLoaded", function () {
  const deleteButtons = document.querySelectorAll(".delete-post-btn");
  const deleteModalLink = document.getElementById("deletePostBtn");
  deleteButtons.forEach((button) => {
    button.addEventListener("click", function () {
      const postUid = this.dataset.postUid;
      deleteModalLink.href = `/backstage/delete/post?&uid=${postUid}`; // Update the modal's delete link
    });
  });
});
