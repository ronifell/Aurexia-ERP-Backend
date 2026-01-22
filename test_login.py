"""Test login endpoint"""
import requests
import sys

try:
    # Test login
    response = requests.post(
        'http://localhost:8000/api/auth/login',
        data={'username': 'admin', 'password': 'admin123'},
        headers={'Content-Type': 'application/x-www-form-urlencoded'}
    )
    print(f"Status Code: {response.status_code}")
    print(f"Response: {response.text}")
    print(f"Headers: {dict(response.headers)}")
    
    if response.status_code == 200:
        print("\n✓ Login successful!")
        data = response.json()
        print(f"Token: {data.get('access_token', 'N/A')[:50]}...")
    else:
        print(f"\n✗ Login failed: {response.text}")
        sys.exit(1)
except requests.exceptions.ConnectionError:
    print("✗ Cannot connect to server. Is it running on http://localhost:8000?")
    sys.exit(1)
except Exception as e:
    print(f"✗ Error: {e}")
    sys.exit(1)
