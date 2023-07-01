import sqlite3
from jinja2 import Template
import datetime
import re
import os
import sys

# Check if the output directory exists, create it if necessary
output_dir = 'out'
if not os.path.exists(output_dir):
    os.makedirs(output_dir)

# Get the path to the SQLite database from command-line argument
if len(sys.argv) < 2:
    sys.exit("Please provide the path to the SQLite database as a command-line argument.")
db_path = sys.argv[1]

print(f"Extracting ghost blog from {db_path}..")

# Connect to the SQLite database
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

# Fetch page data from settings
keys = ['og_title', 'description', 'cover_image']
page_data = {}

for key in keys:
    cursor.execute("SELECT value FROM settings WHERE key=?", (key,))
    value = cursor.fetchone()
    if value:
        page_data[key] = value[0]
    else:
        page_data[key] = ""

# Extract and list posts
cursor.execute("SELECT title, slug, html, created_at FROM posts")
posts = cursor.fetchall()

# HTML template for individual post pages
post_template = Template(open('page_template.html').read())

# HTML template for the index page
index_template = Template(open('index_template.html').read())

# Function to clean the post HTML
def clean_html(post_html):
    # Remove instances of '__GHOST_URL__/'
    cleaned_html = post_html.replace('__GHOST_URL__/', '')

    # Remove 'class' instances with parameters
    cleaned_html = re.sub(r'class=".*?"', '', cleaned_html)

    # Strip <img> tags from everything except 'src'
    cleaned_html = re.sub(r'<img((?!src=).)*>', '', cleaned_html)

    return cleaned_html

# Generate individual HTML pages for each post
for post in posts:
    post_title = post[0]
    post_slug = post[1]
    post_html = post[2]
    post_created_at = post[3]

    # Format the post creation date
    created_at = datetime.datetime.strptime(post_created_at, "%Y-%m-%d %H:%M:%S")

    # Clean the post HTML
    cleaned_html = clean_html(post_html)

    # Render the HTML template with the cleaned post data
    rendered_html = post_template.render(title=post_title, content=cleaned_html, created_at=created_at)

    # Write the rendered HTML to a file in the output directory
    file_name = os.path.join(output_dir, f'{post_slug}.html')
    with open(file_name, 'w') as file:
        file.write(rendered_html)

# Extract page data
page_title = page_data['og_title']
page_description = page_data['description']
page_cover_image = page_data['cover_image']

# Clean the page cover image URL
cleaned_cover_image = page_cover_image.replace('__GHOST_URL__/', '')

index_links = [{'title': post[0], 'url': post[1], 'date': post[3]} for post in reversed(posts)]

# Render the HTML template with page data
index_html = index_template.render(title=page_title, description=page_description, cover_image=cleaned_cover_image, posts=index_links)

# Write the index HTML to a file in the output directory
index_file = os.path.join(output_dir, 'index.html')
with open(index_file, 'w') as file:
    file.write(index_html)

# Close the database connection
conn.close()

# Print extraction summary
num_pages = len(posts)
print(f"Extraction completed. {num_pages} pages extracted.")

# Provide closing message with preview command
print(f"\nTo preview the generated pages run the following command:\n")
print("$ python -m http.server -d out\n")
