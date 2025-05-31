from app import app, db, User, Settings

def init_database():
    with app.app_context():
        # Create all tables
        db.create_all()
        
        # Create default admin user if not exists
        if not User.query.filter_by(username='admin').first():
            admin = User(username='admin')
            admin.set_password('admin')
            db.session.add(admin)
        
        # Create default settings if not exists
        if not Settings.query.first():
            settings = Settings(
                blog_title='My Blog',
                blog_description='Welcome to my blog!',
                show_head_image=True,
                copyright_text='© 2024 My Blog. All rights reserved.'
            )
            db.session.add(settings)
        
        # Commit changes
        db.session.commit()

if __name__ == '__main__':
    init_database()
    print("Database initialized successfully!") 