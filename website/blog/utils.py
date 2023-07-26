from bs4 import BeautifulSoup

def modify_post_format(html_string):
    soup = BeautifulSoup(html_string, 'html.parser')

    # Find all tags in the HTML
    # except figure and img tag
    tags = soup.find_all(lambda tag: tag.name not in ['figure', 'img'])

    # Add padding to each tag
    for tag in tags:
        current_style = tag.get('style', '')
        new_style = f"{current_style} padding-top: 10px; padding-bottom: 10px; "
        tag['style'] = new_style

    headings = soup.find_all(['h1', 'h2', 'h3', 'h4', 'h5', 'h6'])

    # Modify the style attribute for each heading tag
    for heading in headings:
        current_style = heading.get('style', '')
        new_style = f"{current_style} font-family: 'Ubuntu', 'Arial', sans-serif;;"
        heading['style'] = new_style
    
    imgs = soup.find_all(['img'])

    # center image and modify size
    for img in imgs:
        current_style = img.get('style', '')
        new_style = f"{current_style} display: block; margin: 0 auto; max-width: 90%; min-width: 30% ;height: auto;"
        img['style'] = new_style

    captions = soup.find_all(['figcaption'])

    # center image and modify size
    for caption in captions:
        current_style = caption.get('style', '')
        new_style = f"{current_style} text-align: center"
        caption['style'] = new_style

    # Return the modified HTML
    return str(soup)