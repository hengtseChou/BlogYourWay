# Changelog

## Version 1.0.3 (2024-07-26)

### Fixed:

- Fixed javascript form validators.
- Fixed error when display table of contents.
- Fixed link styles in blog post.

## Version 1.0.2 (2024-07-26)

### Fixed:

- Added back highlight.js dependencies to projects and changelog.
- Highlight.js code block styles.

## Version 1.0.1 (2024-07-26)

### Fixed:

- Message when no changelog available.
- Style fix for changelog.

## Version 1.0.0 (2024-07-26)

### New Features

- **Authentication**:

  - Implemented secure user login and registration system.
  - Users log in using email and password.
  - Users are identified by their username.

- **User Profile Management**:

  - Users can edit their short and long bios.
  - Users can upload a personal profile picture.
  - Users can upload a site cover image.
  - Users can set up social links.

- **Homepage**:

  - Implemented a two-column system:
    - One column displays featured blog posts.
    - The other column shows user information, including profile picture and short bio.

- **Blogpost Management**:

  - Users can create, edit, and delete blog posts using a Markdown editor.
  - Users can define custom slugs for blog posts.

- **Comment System**:

  - Readers can leave anonymous comments or register and leave authenticated comments.
  - Both types of comments use Google reCAPTCHA for verification.

- **Project Showcases**:

  - Users can create, edit, and delete project showcases.
  - Project showcases include an image carousel to illustrate the project.
  - Users can define custom slugs for projects.

- **Tag System**:

  - Users can use tags to filter blog posts and projects.

- **Changelog**:

  - Users can upload their personal growth as a changelog over their website.

- **Backstage**:

  - Users can monitor their content's views from the backstage area.

- **Design System**:

  - Created a minimalistic and responsive design using Bootstrap 5 for a good user experience.

- **Forms**:

  - Used WTForms to provide CSRF protection.

- **SEO Enhancements**:

  - Implemented meta tags for social thumbnails and descriptions.
  - Users can define custom slugs for their blog posts and projects.

- **Codebase**:
  - Implemented a well-defined event logger.
  - Extended ORM for MongoDB.
