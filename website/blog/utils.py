import markdown
from bs4 import BeautifulSoup
import re

def parse_markdown_to_text(markdown_content):
    # Convert the Markdown content to HTML
    html_content = markdown.markdown(markdown_content)
    
    # Use BeautifulSoup to extract only the text from the HTML
    soup = BeautifulSoup(html_content, 'html.parser')
    text = soup.get_text()
    print(text)

    # Remove new line characters
    text = re.sub(r'\n+', ' ', text)
    
    return text.strip()