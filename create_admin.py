import getpass
from app import create_app, db
from app.models.user import User

def create_admin():
    print("--- InternBridge Admin Creator ---")
    app = create_app()
    with app.app_context():
        email = input("Enter admin email: ").strip().lower()
        if not email:
            print("Email cannot be empty.")
            return

        existing_user = User.query.filter_by(email=email).first()
        if existing_user:
            print(f"User with email '{email}' already exists. Updating role to 'admin'.")
            existing_user.role = 'admin'
            db.session.commit()
            print("User role updated successfully.")
            return

        full_name = input("Enter admin full name (default: Admin User): ").strip() or "Admin User"
        
        while True:
            password = getpass.getpass("Enter admin password: ")
            if len(password) < 8:
                print("Password must be at least 8 characters long.")
                continue
            
            confirm_password = getpass.getpass("Confirm password: ")
            if password != confirm_password:
                print("Passwords do not match.")
                continue
            break

        admin_user = User(full_name=full_name, email=email, role='admin')
        admin_user.set_password(password)
        
        db.session.add(admin_user)
        db.session.commit()
        print(f"\nSuccess! Admin account '{email}' created successfully.")

if __name__ == "__main__":
    create_admin()
