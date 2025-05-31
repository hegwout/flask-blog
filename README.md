# Cursor Blog

A modern blog platform built with Flask, featuring AI tools integration and chat functionality.

## Features

- User authentication and authorization
- Blog post creation and management
- Rich text editor with file upload support
- AI tools directory with search and filtering
- AI chat interface
- Responsive design
- File upload support
- Admin settings panel

## Tech Stack

- Python 3.x
- Flask
- SQLAlchemy
- Flask-Login
- Bootstrap 5
- CKEditor
- Gunicorn
- Nginx

## Installation

1. Clone the repository:
```bash
git clone https://github.com/yourusername/cursor-blog.git
cd cursor-blog
```

2. Create and activate virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Initialize the database:
```bash
python app.py
```

5. Run the development server:
```bash
python app.py
```

The application will be available at `http://localhost:5000`

## Deployment

1. Update the `nginx.conf` with your domain and paths
2. Run the deployment script:
```bash
./deploy.sh
```

## Configuration

- Update `nginx.conf` with your domain name
- Set environment variables in `.env` file
- Configure Gunicorn settings in `gunicorn_config.py`

## License

MIT License
