from bs4 import BeautifulSoup
import markdown
from website.extensions.db import db_posts

class HTML_Formatter:

    def __init__(self, html_string) :
        self.soup = BeautifulSoup(html_string, 'html.parser')

    def add_padding(self):        

        # Find all tags in the HTML
        # except figure and img tag
        tags = self.soup.find_all(lambda tag: tag.name not in ['figure', 'img'])

        # Add padding to each tag
        for tag in tags:
            current_style = tag.get('style', '')
            new_style = f"{current_style} padding-top: 10px; padding-bottom: 10px; "
            tag['style'] = new_style

        return self
    
    def change_heading_font(self):        

        # Modify the style attribute for each heading tag
        headings = self.soup.find_all(['h1', 'h2', 'h3', 'h4', 'h5', 'h6'])

        # Modify the style attribute for each heading tag
        for heading in headings:
            current_style = heading.get('style', '')
            new_style = f"{current_style} font-family: 'Ubuntu', 'Arial', sans-serif;;"
            heading['style'] = new_style

        return self
    
    def modify_figure(self, max_width='90%'):

        imgs = self.soup.find_all(['img'])

        # center image and modify size
        for img in imgs:
            current_style = img.get('style', '')
            new_style = f"{current_style} display: block; margin: 0 auto; max-width: {max_width}; min-width: 30% ;height: auto;"
            img['style'] = new_style

        captions = self.soup.find_all(['figcaption'])

        # center caption
        for caption in captions:
            current_style = caption.get('style', '')
            new_style = f"{current_style} text-align: center"
            caption['style'] = new_style

        return self
    
    def to_string(self):

        return str(self.soup)


    def to_blogpost(self):

        blogpost = self.add_padding().\
            change_heading_font().\
            modify_figure().\
            to_string()

        return blogpost
    
    def to_about(self):
        
        about = self.add_padding().\
            modify_figure(max_width='50%').\
            to_string()
        
        return about
    
def all_user_tags(username):

    result = db_posts.find({
        'author': username, 
        'archived': False
    })
    
    tags_dict = {}
    for post in result:
        post_tags = post['tags']
        for tag in post_tags:
            if tag not in tags_dict:
                tags_dict[tag] = 1
            else:
                tags_dict[tag] += 1

    sorted_tags_key = sorted(tags_dict, key=tags_dict.get, reverse=True)
    sorted_tags = {}
    for key in sorted_tags_key:
        sorted_tags[key] = tags_dict[key]

    return sorted_tags

md = markdown.Markdown(
    extensions=[
        'markdown_captions'
    ]
)
        

