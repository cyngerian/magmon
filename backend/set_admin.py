from wsgi import app
from app.models import User, db

with app.app_context():
    user = User.query.get(1)
    if user:
        user.is_admin = True
        db.session.commit()
        print(f"User {user.username} is now an admin")
    else:
        print("User with ID 1 not found")
