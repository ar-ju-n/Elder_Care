import os
import re
from bs4 import BeautifulSoup, Comment
from pathlib import Path

def remove_styles(html_content):
    """Remove both inline styles and style tags from HTML content."""
    soup = BeautifulSoup(html_content, 'html.parser')
    
    # Remove style attributes from all tags
    for tag in soup.find_all(True):
        if 'style' in tag.attrs:
            del tag.attrs['style']
    
    # Remove all <style> tags
    for style_tag in soup.find_all('style'):
        style_tag.decompose()
    
    # Remove style attributes from link tags (optional)
    for link in soup.find_all('link', rel='stylesheet'):
        link.decompose()
    
    # Remove any HTML comments that might contain CSS
    for comment in soup.find_all(string=lambda text: isinstance(text, Comment)):
        if 'style' in comment.lower():
            comment.extract()
    
    return str(soup)

def process_html_files(directory):
    """Process all HTML files in the given directory and its subdirectories."""
    html_files = list(Path(directory).rglob('*.html'))
    processed = 0
    
    print(f"Found {len(html_files)} HTML files to process...")
    
    for file_path in html_files:
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Process all HTML files, not just those with style attributes
            new_content = remove_styles(content)
            
            # Only write if content changed
            if new_content != content:
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(new_content)
                processed += 1
                print(f"Processed: {file_path}")
                
        except Exception as e:
            print(f"Error processing {file_path}: {str(e)}")
    
    return processed

def main():
    project_dir = os.path.dirname(os.path.abspath(__file__))
    print(f"Starting to process HTML files in: {project_dir}")
    
    # Process both the main directory and templates directory
    processed_count = process_html_files(project_dir)
    templates_dir = os.path.join(project_dir, 'templates')
    if os.path.exists(templates_dir):
        processed_count += process_html_files(templates_dir)
    
    print(f"\nProcessing complete! Processed {processed_count} HTML files.")

if __name__ == "__main__":
    main()
