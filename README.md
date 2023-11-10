# Little Blog

This is a hobby project, for building a independent blogging/portfolio engine to accommodate my preferences. Back-end is built with <ins><i>Flask</i></ins>, along with several extenstions; Front-end is mainly develop through <ins><i>Bootstrap 5</i></ins> and some useful javascript libraries, such as [easy-markdown-editor](https://github.com/Ionaru/easy-markdown-editor), which is adpoted as the content editor in this project.

This project uses <ins><i>poetry</i></ins> for managing dependencies, <ins><i>pytest</i></ins> and <ins><i>pytest-cov</i></ins> for testing, <ins><i>black</i></ins> and <ins><i>isort</i></ins> for formatting, and <ins><i>ruff</i></ins> for linting.

## Requirements for deployment

You will need: 

1. A web hosting service.

2. A MongoDB machine (on cloud).

3. A redis machine (on cloud).

Remember to add a `.env` file for enviroment variables (check `application/config.py` to see what fields are needed).

## Features

### Done

- [x] Posts CRUD (with markdown formation).
- [x] Support tags for posts.
- [x] Readtime and reading progress bar on each post.
- [x] Good looking comment section (with google reCAPCHA).
- [x] Good looking code block in posts (with highliht.js).
- [x] Customized and click-through trackable social links. 
- [x] Personalized blog banner and profile picture.
- [x] Personalized user autobiography.
- [x] Good looking website and backstage.
- [x] RWD support.
- [x] Track website traffic/post traffic and read ratios.
- [x] Well defined event logging. 

### Now

- [ ] Integrated user traffic dashboard.
- [ ] Post traffic/read ratio dashboard for post control.
### Next 

- [ ] Portfolio CRUD.
- [ ] Personal changelog CRUD.
- [ ] Table of Content for posts.

### Later

- [ ] Support tags for both posts and portfolios.
- [ ] Enhance UI/UX on landing page.
- [ ] Track time spent on pages with sockerio.
- [ ] Modal box images in posts.
- [ ] Serves images in the database.
- [ ] Admin dashboard for checking logging/view overall traffic.

## Issue board

[Little-blog notion issue board](https://hengtse.notion.site/Little-Blog-119b66fdef244c1ab3041aeb5bda473b?pvs=4)