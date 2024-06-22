const mobileNavBtn = document.getElementById("mobile-nav-archive");
mobileNavBtn.style.color = "white";

document.addEventListener("DOMContentLoaded", function () {
  const deleteButtons = document.querySelectorAll(".delete-article-btn");
  const deleteModalLink = document.getElementById("deleteArticleBtn");
  deleteButtons.forEach((button) => {
    button.addEventListener("click", function () {
      const articleUid = this.dataset.articleUid;
      deleteModalLink.href = `/backstage/delete/article?&uid=${articleUid}`; // Update the modal's delete link
    });
  });
});
