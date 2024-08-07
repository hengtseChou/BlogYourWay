const navigation = {
  posts: "mobile-nav-posts",
  "edit-post": "mobile-nav-posts",
  projects: "mobile-nav-projects",
  "edit-projects": "mobile-nav-projects",
  changelog: "mobile-nav-changelog",
  "edit-changelog": "mobile-nav-changelog",
  about: "mobile-nav-about",
  theme: "mobile-nav-theme",
  archive: "mobile-nav-archive",
  settings: "mobile-nav-settings",
};

const currentPanel = document.getElementById("current-panel").innerHTML;
const mobileNavBtn = document.getElementById(navigation[currentPanel]);
mobileNavBtn.classList.add("text-white");
