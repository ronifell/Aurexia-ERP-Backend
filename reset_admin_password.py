"""
Reset admin password
"""
from database import SessionLocal
from models import User
from auth import get_password_hash, verify_password

def reset_admin_password():
    """Reset admin user password"""
    db = SessionLocal()
    
    try:
        # Find admin user
        admin_user = db.query(User).filter(User.username == "admin").first()
        
        if not admin_user:
            print("Admin user not found!")
            return
        
        # New password
        new_password = "admin123"
        
        # Hash the password
        print(f"Hashing password: {new_password}")
        new_hash = get_password_hash(new_password)
        print(f"New hash: {new_hash[:50]}...")
        
        # Verify the hash works
        print("Verifying hash...")
        is_valid = verify_password(new_password, new_hash)
        print(f"Verification result: {is_valid}")
        
        if not is_valid:
            print("ERROR: Password verification failed immediately after hashing!")
            return
        
        # Update the user
        admin_user.password_hash = new_hash
        db.commit()
        
        print("\n✓ Admin password reset successfully!")
        print(f"Username: admin")
        print(f"Password: {new_password}")
        
        # Verify again after commit
        print("\nVerifying after database commit...")
        db.refresh(admin_user)
        is_valid_after = verify_password(new_password, admin_user.password_hash)
        print(f"Verification result: {is_valid_after}")
        
    except Exception as e:
        print(f"Error resetting password: {e}")
        import traceback
        traceback.print_exc()
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    reset_admin_password()
