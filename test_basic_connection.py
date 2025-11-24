"""
Basic connection test to diagnose the issue
"""

from kiteconnect import KiteConnect

API_KEY = 'mmfof9xckmsvdyyk'
ACCESS_TOKEN = 'NdCCam6BMNMYUlMuZ6pTzGmdpYqvcfiq'

print("Testing basic connection...")
print(f"API Key: {API_KEY}")
print(f"Access Token: {ACCESS_TOKEN[:20]}...")

kite = KiteConnect(api_key=API_KEY)
kite.set_access_token(ACCESS_TOKEN)

# Try to get profile (simplest API call)
try:
    profile = kite.profile()
    print("\n✅ SUCCESS! Connection works!")
    print(f"User: {profile['user_name']}")
    print(f"Email: {profile['email']}")
    print(f"Broker: {profile['broker']}")
except Exception as e:
    print(f"\n❌ Connection failed: {e}")
    print("\nPossible issues:")
    print("1. API subscription not active in Zerodha account")
    print("2. API app needs to be enabled in Kite Connect console")
    print("3. Credentials mismatch")
