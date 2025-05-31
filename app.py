import os
from flask import Flask, render_template, request, redirect, url_for, flash, send_from_directory, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from datetime import datetime
import markdown
from flask_wtf.csrf import CSRFProtect

app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'dev')
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///blog.db'
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size

# Ensure upload directory exists with proper permissions
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
os.chmod(app.config['UPLOAD_FOLDER'], 0o755)

# Initialize CSRF protection
csrf = CSRFProtect(app)

# Add markdown filter
@app.template_filter('markdown')
def markdown_filter(text):
    return markdown.markdown(text, extensions=['extra', 'codehilite'])

db = SQLAlchemy(app)
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

# Models
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(120), nullable=False)
    posts = db.relationship('Post', backref='author', lazy=True)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

class Post(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    content = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)

class Settings(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    blog_title = db.Column(db.String(100), default='My Blog')
    blog_description = db.Column(db.Text)
    head_image = db.Column(db.String(200))
    show_head_image = db.Column(db.Boolean, default=True)
    footer_html = db.Column(db.Text)
    copyright_text = db.Column(db.String(200))

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# Routes
@app.route('/')
def index():
    posts = Post.query.order_by(Post.created_at.desc()).all()
    top_posts = Post.query.order_by(Post.created_at.desc()).limit(10).all()
    settings = Settings.query.first()
    return render_template('index.html', posts=posts, top_posts=top_posts, settings=settings)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        user = User.query.filter_by(username=username).first()
        
        if user and user.check_password(password):
            login_user(user)
            return redirect(url_for('index'))
        flash('Invalid username or password')
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('index'))

@app.route('/post/new', methods=['GET', 'POST'])
@login_required
def new_post():
    if request.method == 'POST':
        title = request.form.get('title')
        content = request.form.get('content_required')
        post = Post(title=title, content=content, author=current_user)
        db.session.add(post)
        db.session.commit()
        return redirect(url_for('index'))
    return render_template('new_post.html')

@app.route('/settings', methods=['GET', 'POST'])
@login_required
def settings():
    settings = Settings.query.first()
    if not settings:
        settings = Settings()
        db.session.add(settings)
        db.session.commit()

    if request.method == 'POST':
        settings.blog_title = request.form.get('blog_title')
        settings.blog_description = request.form.get('blog_description')
        settings.show_head_image = bool(request.form.get('show_head_image'))
        settings.footer_html = request.form.get('footer_html')
        settings.copyright_text = request.form.get('copyright_text')

        if 'head_image' in request.files:
            file = request.files['head_image']
            if file and file.filename:
                filename = secure_filename(file.filename)
                file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                file.save(file_path)
                os.chmod(file_path, 0o644)  # Set proper file permissions
                settings.head_image = filename

        db.session.commit()
        flash('Settings updated successfully')
        return redirect(url_for('settings'))

    return render_template('settings.html', settings=settings)

@app.route('/uploads/<filename>')
def uploaded_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

@app.route('/post/<int:post_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_post(post_id):
    post = Post.query.get_or_404(post_id)
    if post.author != current_user:
        flash('You do not have permission to edit this post.')
        return redirect(url_for('index'))
    
    if request.method == 'POST':
        post.title = request.form.get('title')
        post.content = request.form.get('content_required')
        db.session.commit()
        flash('Post has been updated!')
        return redirect(url_for('index'))
    
    return render_template('edit_post.html', post=post)

@app.route('/post/<int:post_id>/delete', methods=['POST'])
@login_required
def delete_post(post_id):
    post = Post.query.get_or_404(post_id)
    if post.author != current_user:
        flash('You do not have permission to delete this post.')
        return redirect(url_for('index'))
    
    db.session.delete(post)
    db.session.commit()
    flash('Post has been deleted!')
    return redirect(url_for('index'))

@app.route('/upload', methods=['POST'])
@login_required
def upload_file():
    if 'upload' not in request.files:
        return {'error': {'message': 'No file uploaded'}}, 400
    
    file = request.files['upload']
    if file.filename == '':
        return {'error': {'message': 'No file selected'}}, 400
    
    if file:
        filename = secure_filename(file.filename)
        # Add timestamp to filename to prevent duplicates
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"{timestamp}_{filename}"
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(file_path)
        os.chmod(file_path, 0o644)  # Set proper file permissions
        
        # Return the URL for the uploaded file
        url = url_for('uploaded_file', filename=filename, _external=True)
        return {
            'url': url,
            'uploaded': True
        }
    
    return {'error': {'message': 'File upload failed'}}, 400

@app.route('/chat', methods=['GET', 'POST'])
@login_required
def chat():
    if request.method == 'POST':
        message = request.form.get('message')
        if message:
            # Here you would typically integrate with an AI service
            # For now, we'll just echo the message
            response = f"Echo: {message}"
            return jsonify({'response': response})
    return render_template('chat.html')

@app.route('/ai-tools')
def ai_tools():
    tools = [
        # Language & Writing
        {
            'name': 'ChatGPT',
            'description': 'Advanced language model for conversation and text generation',
            'url': 'https://chat.openai.com',
            'category': 'Language',
            'popularity': 5
        },
        {
            'name': 'Claude',
            'description': 'Anthropic\'s AI assistant for conversation and analysis',
            'url': 'https://www.anthropic.com/claude',
            'category': 'Language',
            'popularity': 5
        },
        {
            'name': 'Perplexity AI',
            'description': 'AI-powered search engine with detailed answers and citations',
            'url': 'https://www.perplexity.ai',
            'category': 'Language',
            'popularity': 4
        },
        {
            'name': 'Character.AI',
            'description': 'Chat with AI characters and historical figures',
            'url': 'https://character.ai',
            'category': 'Language',
            'popularity': 4
        },
        {
            'name': 'Pi by Inflection',
            'description': 'Personal AI assistant focused on helpful conversations',
            'url': 'https://pi.ai',
            'category': 'Language',
            'popularity': 4
        },
        
        # Image Generation & Editing
        {
            'name': 'DALL-E',
            'description': 'AI image generation from text descriptions',
            'url': 'https://openai.com/dall-e-2',
            'category': 'Image',
            'popularity': 5
        },
        {
            'name': 'Midjourney',
            'description': 'AI art generation through Discord',
            'url': 'https://www.midjourney.com',
            'category': 'Image',
            'popularity': 5
        },
        {
            'name': 'Stable Diffusion',
            'description': 'Open-source image generation model',
            'url': 'https://stability.ai',
            'category': 'Image',
            'popularity': 5
        },
        {
            'name': 'Leonardo.ai',
            'description': 'AI art generation and editing platform',
            'url': 'https://leonardo.ai',
            'category': 'Image',
            'popularity': 4
        },
        {
            'name': 'Canva AI',
            'description': 'AI-powered design and image editing tools',
            'url': 'https://www.canva.com/ai',
            'category': 'Image',
            'popularity': 4
        },
        
        # Video Creation & Editing
        {
            'name': 'RunwayML',
            'description': 'AI-powered video editing and generation',
            'url': 'https://runwayml.com',
            'category': 'Video',
            'popularity': 5
        },
        {
            'name': 'Synthesia',
            'description': 'AI video generation with virtual presenters',
            'url': 'https://www.synthesia.io',
            'category': 'Video',
            'popularity': 4
        },
        {
            'name': 'HeyGen',
            'description': 'AI video generation with talking avatars',
            'url': 'https://www.heygen.com',
            'category': 'Video',
            'popularity': 4
        },
        {
            'name': 'Descript',
            'description': 'AI-powered audio and video editing',
            'url': 'https://www.descript.com',
            'category': 'Video',
            'popularity': 4
        },
        {
            'name': 'Pictory',
            'description': 'AI video summarization and editing',
            'url': 'https://pictory.ai',
            'category': 'Video',
            'popularity': 3
        },
        
        # Audio & Music
        {
            'name': 'ElevenLabs',
            'description': 'AI voice cloning and text-to-speech',
            'url': 'https://elevenlabs.io',
            'category': 'Audio',
            'popularity': 5
        },
        {
            'name': 'Murf',
            'description': 'AI voice generator for text-to-speech',
            'url': 'https://murf.ai',
            'category': 'Audio',
            'popularity': 4
        },
        {
            'name': 'Mubert',
            'description': 'AI music generation platform',
            'url': 'https://mubert.com',
            'category': 'Audio',
            'popularity': 4
        },
        {
            'name': 'Soundraw',
            'description': 'AI music generator for content creators',
            'url': 'https://soundraw.io',
            'category': 'Audio',
            'popularity': 3
        },
        {
            'name': 'Voicemod',
            'description': 'Real-time AI voice changer',
            'url': 'https://www.voicemod.net',
            'category': 'Audio',
            'popularity': 3
        },
        
        # Productivity & Business
        {
            'name': 'Notion AI',
            'description': 'AI writing assistant integrated with Notion',
            'url': 'https://www.notion.so/product/ai',
            'category': 'Productivity',
            'popularity': 5
        },
        {
            'name': 'Tome',
            'description': 'AI-powered presentation generator',
            'url': 'https://tome.app',
            'category': 'Productivity',
            'popularity': 4
        },
        {
            'name': 'Beautiful.ai',
            'description': 'AI-powered presentation design tool',
            'url': 'https://www.beautiful.ai',
            'category': 'Productivity',
            'popularity': 4
        },
        {
            'name': 'Otter.ai',
            'description': 'AI meeting assistant for transcription and notes',
            'url': 'https://otter.ai',
            'category': 'Productivity',
            'popularity': 4
        },
        {
            'name': 'Fireflies.ai',
            'description': 'AI meeting transcription and analysis',
            'url': 'https://fireflies.ai',
            'category': 'Productivity',
            'popularity': 4
        },
        
        # Development & Coding
        {
            'name': 'GitHub Copilot',
            'description': 'AI pair programmer that helps write better code',
            'url': 'https://github.com/features/copilot',
            'category': 'Development',
            'popularity': 5
        },
        {
            'name': 'Tabnine',
            'description': 'AI code completion tool',
            'url': 'https://www.tabnine.com',
            'category': 'Development',
            'popularity': 4
        },
        {
            'name': 'Codeium',
            'description': 'Free AI code completion and chat',
            'url': 'https://codeium.com',
            'category': 'Development',
            'popularity': 4
        },
        {
            'name': 'Cursor',
            'description': 'AI-first code editor',
            'url': 'https://cursor.sh',
            'category': 'Development',
            'popularity': 4
        },
        {
            'name': 'Replit Ghost',
            'description': 'AI pair programmer in the browser',
            'url': 'https://replit.com/ghost',
            'category': 'Development',
            'popularity': 3
        },
        
        # Marketing & Content
        {
            'name': 'Jasper',
            'description': 'AI content generation for marketing and business',
            'url': 'https://www.jasper.ai',
            'category': 'Marketing',
            'popularity': 5
        },
        {
            'name': 'Copy.ai',
            'description': 'AI copywriting tool for marketing content',
            'url': 'https://www.copy.ai',
            'category': 'Marketing',
            'popularity': 4
        },
        {
            'name': 'Grammarly',
            'description': 'AI writing assistant for grammar and style',
            'url': 'https://www.grammarly.com',
            'category': 'Marketing',
            'popularity': 5
        },
        {
            'name': 'Writesonic',
            'description': 'AI writing and content generation platform',
            'url': 'https://writesonic.com',
            'category': 'Marketing',
            'popularity': 4
        },
        {
            'name': 'Anyword',
            'description': 'AI copywriting and optimization platform',
            'url': 'https://anyword.com',
            'category': 'Marketing',
            'popularity': 3
        },
        
        # Research & Analysis
        {
            'name': 'Elicit',
            'description': 'AI research assistant for literature review',
            'url': 'https://elicit.org',
            'category': 'Research',
            'popularity': 4
        },
        {
            'name': 'Consensus',
            'description': 'AI-powered research and fact-checking',
            'url': 'https://consensus.app',
            'category': 'Research',
            'popularity': 4
        },
        {
            'name': 'Scholarcy',
            'description': 'AI-powered research paper summarization',
            'url': 'https://www.scholarcy.com',
            'category': 'Research',
            'popularity': 3
        },
        {
            'name': 'Semantic Scholar',
            'description': 'AI-powered academic search engine',
            'url': 'https://www.semanticscholar.org',
            'category': 'Research',
            'popularity': 4
        },
        {
            'name': 'Scite',
            'description': 'AI-powered citation analysis',
            'url': 'https://scite.ai',
            'category': 'Research',
            'popularity': 3
        },
        
        # Education & Learning
        {
            'name': 'Duolingo Max',
            'description': 'AI-powered language learning with GPT-4',
            'url': 'https://www.duolingo.com/max',
            'category': 'Education',
            'popularity': 4
        },
        {
            'name': 'Khanmigo',
            'description': 'AI tutor by Khan Academy',
            'url': 'https://www.khanacademy.org/khan-labs',
            'category': 'Education',
            'popularity': 4
        },
        {
            'name': 'Quizlet AI',
            'description': 'AI-powered study tools and flashcards',
            'url': 'https://quizlet.com/ai',
            'category': 'Education',
            'popularity': 3
        },
        {
            'name': 'Coursera AI',
            'description': 'AI-powered learning platform',
            'url': 'https://www.coursera.org/ai',
            'category': 'Education',
            'popularity': 4
        },
        {
            'name': 'Memrise AI',
            'description': 'AI language learning with native speakers',
            'url': 'https://www.memrise.com',
            'category': 'Education',
            'popularity': 3
        }
    ]
    return render_template('ai_tools.html', tools=tools)

def init_db():
    with app.app_context():
        db.create_all()
        # Create default admin user if not exists
        if not User.query.filter_by(username='admin').first():
            admin = User(username='admin')
            admin.set_password('admin')
            db.session.add(admin)
            db.session.commit()

if __name__ == '__main__':
    init_db()
    app.run(debug=True) 