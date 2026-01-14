"""
Test JWT token generation and validation
"""
from auth import create_access_token, get_password_hash, verify_password, authenticate_user
from database import SessionLocal
from models import User
from jose import jwt, JWTError
from config import settings
from datetime import timedelta

def test_token():
    """Test token creation and validation"""
    db = SessionLocal()
    
    try:
        # Test authentication
        print("1. Testing authentication...")
        user = authenticate_user(db, "admin", "admin123")
        if user:
            print(f"   [OK] User authenticated: {user.username}")
        else:
            print("   [FAIL] Authentication failed!")
            return
        
        # Test token creation
        print("\n2. Testing token creation...")
        access_token = create_access_token(
            data={"sub": user.username}, 
            expires_delta=timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
        )
        print(f"   [OK] Token created: {access_token[:50]}...")
        
        # Test token decoding
        print("\n3. Testing token decoding...")
        try:
            payload = jwt.decode(access_token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
            print(f"   [OK] Token decoded successfully")
            print(f"   - Subject (username): {payload.get('sub')}")
            print(f"   - Expiration: {payload.get('exp')}")
        except JWTError as e:
            print(f"   [FAIL] Token decoding failed: {e}")
            return
        
        # Test user lookup
        print("\n4. Testing user lookup from token...")
        username = payload.get("sub")
        db_user = db.query(User).filter(User.username == username).first()
        if db_user:
            print(f"   [OK] User found: {db_user.username}")
            print(f"   - Active: {db_user.is_active}")
            print(f"   - Role ID: {db_user.role_id}")
        else:
            print(f"   [FAIL] User not found with username: {username}")
            return
        
        print("\n[SUCCESS] All token tests passed!")
        
    except Exception as e:
        print(f"\n[ERROR] Error during testing: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()

if __name__ == "__main__":
    test_token()
