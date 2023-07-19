import markdown
from bs4 import BeautifulSoup
import re

def parse_markdown_to_text(markdown_content):
    # Convert the Markdown content to HTML
    html_content = markdown.markdown(markdown_content)
    
    # Use BeautifulSoup to extract only the text from the HTML
    soup = BeautifulSoup(html_content, 'html.parser')
    paragraphs = soup.find_all('p')
    
    # Extract the text from each paragraph and join them with white space
    text = ' '.join(paragraph.get_text() for paragraph in paragraphs)

    # Remove new line characters and replace them with white space
    text = re.sub(r'\n+', ' ', text)
    
    return text.strip()