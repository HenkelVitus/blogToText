import os
import re
import requests
import string
from bs4 import BeautifulSoup
from tqdm import tqdm
from concurrent.futures import ThreadPoolExecutor


def sanitize_filename(title):
    valid_chars = f"-_.() {string.ascii_letters}{string.digits}"
    filename = ''.join(c for c in title if c in valid_chars)
    return filename.strip()


def remove_emojis(text):
    emoji_pattern = re.compile(
        pattern="["
                u"\U0001F600-\U0001F64F"  # emoticons
                u"\U0001F300-\U0001F5FF"  # symbols & pictographs
                u"\U0001F680-\U0001F6FF"  # transport & map symbols
                u"\U0001F1E0-\U0001F1FF"  # flags (iOS)
                "]+",
        flags=re.UNICODE
    )
    return emoji_pattern.sub(r'', text)


def download_image(image_url, images_dir):
    response = requests.get(image_url, stream=True)
    if response.status_code == 200:
        filename = os.path.basename(image_url)
        # modify the filename to be unique
        filename = str(len(os.listdir(images_dir))) + '_' + filename
        image_path = os.path.join(images_dir, filename)
        with open(image_path, 'wb') as file:
            for chunk in response.iter_content(1024):
                file.write(chunk)
        return image_path
    else:
        return None


def convert_to_tex(content, output_dir):
    # Each post will have its own subdirectory in the images directory
    sanitized_title = sanitize_filename(content['title']).lower().replace(' ', '_')
    images_dir = os.path.join(output_dir, 'images', sanitized_title)
    os.makedirs(images_dir, exist_ok=True)  # Make sure this line is here!

    tex = ''
    tex += '\\subsection{' + content['title'] + '}\n\n'
    tex += content['date'] + '\n\n'

    # Process the HTML body
    body = content['body']
    soup = BeautifulSoup(body.prettify(), 'html.parser')
    for tag in soup.descendants:  # We go through the descendants of the soup to capture all tags
        if tag.name == 'img':
            image_url = tag['src']
            image_path = download_image(image_url, images_dir)  # save image to the post's subdirectory
            if image_path:
                relative_image_path = os.path.relpath(image_path, os.path.join(output_dir, 'images')).replace('\\', '/')
                image_name = os.path.splitext(os.path.basename(image_path))[0]
                image_latex = f'\n\\begin{{figure}}[H]\n\t\\centering\n\t\\includegraphics[width=0.5\\textwidth]{{{relative_image_path}}}\n\t\\caption{{}}\n\t\\label{{fig:{image_name}}}\n\\end{{figure}}\n'
                tex += image_latex
        elif tag.name in ['div', 'p', 'span']:
            if not any(
                    child.name for child in tag.children):  # Only process the tag if it doesn't contain any other tag
                text = remove_emojis(tag.get_text())
                tex += text + '\n\n'

    return tex


def process_post(url, output_dir):
    response = requests.get(url)
    soup = BeautifulSoup(response.text, 'html.parser')

    post_div = soup.find('div', class_='post')

    # Extract post information
    script_tag = post_div.find('script', {'type': 'application/ld+json'})
    json_data = script_tag.string
    post_data = re.search(r'"headline": "(.*?)",', json_data, re.DOTALL)
    post_title = post_data.group(1)
    post_date = soup.find('h3', class_='post-title').text.strip()
    post_body = post_div.find('div', class_='post-body')

    # Convert to LaTeX
    content = {
        'title': post_title,
        'date': post_date,
        'body': post_body
    }
    tex_content = convert_to_tex(content, output_dir)

    # Create output directory if it doesn't exist
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    # Save LaTeX file
    sanitized_title = sanitize_filename(post_title)
    file_name = sanitized_title.lower().replace(' ', '_') + '.tex'
    file_path = os.path.join(output_dir, file_name)
    with open(file_path, 'w', encoding='utf-8') as file:
        file.write(tex_content)

    print(f"Processed post: {file_name}")


def process_urls(urls_file, output_dir):
    with open(urls_file, 'r') as file:
        urls = file.readlines()

    with ThreadPoolExecutor() as executor:
        futures = []
        for url in urls:
            url = url.strip()
            if url:
                future = executor.submit(process_post, url, output_dir)
                futures.append(future)

        for future in tqdm(futures):
            future.result()


def main():
    urls_file = 'urls.txt'  # Path to the file containing URLs
    output_dir = 'output'  # Name of the output directory

    process_urls(urls_file, output_dir)


if __name__ == '__main__':
    main()