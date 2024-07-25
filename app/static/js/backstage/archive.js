document.addEventListener("DOMContentLoaded", function () {
  const deletePostBtn = document.querySelectorAll(".delete-post-btn");
  const deletePostModal = document.getElementById("deletePostBtn");
  deletePostBtn.forEach((button) => {
    button.addEventListener("click", function () {
      const postUid = this.dataset.postUid;
      deletePostModal.href = `/backstage/delete/post?&uid=${postUid}`; // Update the modal's delete link
    });
  });

  const deleteProjectBtn = document.querySelectorAll(".delete-project-btn");
  const deleteProjectModal = document.getElementById("deleteProjectBtn");
  deleteProjectBtn.forEach((button) => {
    button.addEventListener("click", function () {
      const projectUid = this.dataset.projectUid;
      deleteProjectModal.href = `/backstage/delete/project?&uid=${projectUid}`; // Update the modal's delete link
    });
  });

  const deleteChangelogBtn = document.querySelectorAll(".delete-changelog-btn");
  const deleteChangelogModal = document.getElementById("deleteChangelogBtn");
  deleteChangelogBtn.forEach((button) => {
    button.addEventListener("click", function () {
      const changelogUid = this.dataset.changelogUid;
      deleteChangelogModal.href = `/backstage/delete/changelog?&uid=${changelogUid}`; // Update the modal's delete link
    });
  });
});
