# A Flask blog

* A Github public repo https://github.com/hegwout/flask-blog, web blog for only one user.Frendly user interface
* python framework flask, sqlite storage

## User interface

* user login, default user: admin, default password:admin
* blue boostrap theme
* A logo in the navication bar
* A admin setting page: blog title, blog description, blog head image, navi bar setting, show the head image in home page
* Custumized HTML embered footer, can use html, javascript
* Copyright

## Features

 * Support markdown
 * File upload and save to a foler "upload"
 * Rich text editor
 * Top 10 posts on the right of each page, and home page

## Support:
* git init and fetch to my repo: https://github.com/hegwout/flask-blog
* github ci/cd  can auto deploy latest main branch to my EC2 server

## Local debug commands

To run and debug the Flask blog locally, use the following commands:

```bash
# Create and activate a virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Set environment variables and run the app
export FLASK_APP=app.py
export FLASK_ENV=development
flask run
```

You can now access the blog at [http://localhost:5000](http://localhost:5000).
