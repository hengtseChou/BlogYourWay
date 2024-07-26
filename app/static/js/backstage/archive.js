// Function to add delete post event listeners
function addDeletePostEventListeners() {
  const deletePostBtns = document.querySelectorAll(".delete-post-btn");
  const deletePostModal = document.getElementById("deletePostBtn");

  deletePostBtns.forEach((button) => {
    button.addEventListener("click", function () {
      const postUid = this.dataset.postUid;
      deletePostModal.href = `/backstage/delete/post?&uid=${postUid}`;
    });
  });
}

// Function to add delete project event listeners
function addDeleteProjectEventListeners() {
  const deleteProjectBtns = document.querySelectorAll(".delete-project-btn");
  const deleteProjectModal = document.getElementById("deleteProjectBtn");

  deleteProjectBtns.forEach((button) => {
    button.addEventListener("click", function () {
      const projectUid = this.dataset.projectUid;
      deleteProjectModal.href = `/backstage/delete/project?&uid=${projectUid}`;
    });
  });
}

// Function to add delete changelog event listeners
function addDeleteChangelogEventListeners() {
  const deleteChangelogBtns = document.querySelectorAll(
    ".delete-changelog-btn",
  );
  const deleteChangelogModal = document.getElementById("deleteChangelogBtn");

  deleteChangelogBtns.forEach((button) => {
    button.addEventListener("click", function () {
      const changelogUid = this.dataset.changelogUid;
      deleteChangelogModal.href = `/backstage/delete/changelog?&uid=${changelogUid}`;
    });
  });
}

document.addEventListener("DOMContentLoaded", function () {
  addDeletePostEventListeners();
  addDeleteProjectEventListeners();
  addDeleteChangelogEventListeners();
});
