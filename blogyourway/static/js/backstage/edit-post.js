const mobileNavBtn = document.getElementById("mobile-nav-posts");
mobileNavBtn.style.color = "white";

const easyMDE = new EasyMDE({
  element: document.getElementById("editor"),
  autofocus: true,
  toolbar: [
    "bold",
    "italic",
    "heading",
    "|",
    "undo",
    "redo",
    "|",
    "code",
    "quote",
    "unordered-list",
    "ordered-list",
    "horizontal-rule",
    "|",
    "link",
    "image",
    "|",
    "preview",
    "guide",
  ],
  minHeight: "200px",
  spellChecker: false,
});
easyMDE.value(postContent);

function validateUpdate() {
  var title = document.getElementById("title").value;
  if (title.trim() === "") {
    alert("You must enter the title for the post.");
    return false;
  }

  var subtitle = document.getElementById("subtitle").value;
  if (subtitle.trim() === "") {
    alert("Add a short description for this post as a subtitle.");
    return false;
  }

  var tags = document.getElementById("tags").value;
  if (tags.trim() === "") {
    alert("You must add one tag to the post at least.");
    return false;
  }
  const tagRegex =
    /^[\u4e00-\u9fa5a-zA-Z\s\-_.]+(,\s*[\u4e00-\u9fa5a-zA-Z\s\-_.]+)*$/;
  if (!tagRegex.test(tags)) {
    alert("You must separate tags with a comma (',').");
    return false;
  }

  var cover = document.getElementById("cover").value;
  if (cover.trim() === "") {
    alert("You must add a cover image for the post.");
    return false;
  }

  if (easyMDE.value().trim() === "") {
    alert("You did not write anything!");
    return false;
  }

  return true;
}
