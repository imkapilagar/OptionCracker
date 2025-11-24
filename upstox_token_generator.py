"""
Upstox Access Token Generator
Run this once daily to generate your access token
"""

import webbrowser
import requests
from datetime import datetime

def generate_upstox_token():
    """Interactive script to generate Upstox access token"""

    print("=" * 60)
    print("Upstox Access Token Generator")
    print("=" * 60)

    # Step 1: Get API credentials
    api_key = input("\nEnter your Upstox API Key: ").strip()
    api_secret = input("Enter your Upstox API Secret: ").strip()

    if not api_key or not api_secret:
        print("❌ API Key and Secret are required!")
        return

    # Redirect URL (must match what you set in Upstox app settings)
    redirect_uri = "http://127.0.0.1:5000/callback"

    # Step 2: Generate authorization URL
    auth_url = (
        f"https://api.upstox.com/v2/login/authorization/dialog?"
        f"response_type=code&"
        f"client_id={api_key}&"
        f"redirect_uri={redirect_uri}"
    )

    print("\n" + "=" * 60)
    print("STEP 1: Authorize the Application")
    print("=" * 60)
    print(f"\nOpening browser to: {auth_url[:80]}...")
    print("\nPlease login with your Upstox credentials.")
    print("After login, you'll be redirected to a URL.")

    # Open browser
    try:
        webbrowser.open(auth_url)
    except:
        print("Could not open browser automatically.")
        print(f"Please manually open: {auth_url}")

    # Step 3: Get authorization code from redirect URL
    print("\n" + "=" * 60)
    print("STEP 2: Get Authorization Code")
    print("=" * 60)
    print("\nAfter logging in, you'll be redirected to a URL like:")
    print("http://127.0.0.1:5000/callback?code=XXXXX")
    print("\n⚠️  IMPORTANT: The browser will show 'Unable to connect' - THIS IS NORMAL!")
    print("The authorization code is still in the URL bar - just copy it from there.")
    print("\nCopy ONLY the 'code' value from that URL (the part after code=)")
    print("Example: If URL shows 'code=abc123xyz', enter: abc123xyz")

    auth_code = input("\nEnter the authorization code: ").strip()

    if not auth_code:
        print("❌ Authorization code is required!")
        return

    # Step 4: Exchange authorization code for access token
    print("\n" + "=" * 60)
    print("STEP 3: Generating Access Token...")
    print("=" * 60)

    token_url = "https://api.upstox.com/v2/login/authorization/token"

    headers = {
        'accept': 'application/json',
        'Content-Type': 'application/x-www-form-urlencoded',
    }

    data = {
        'code': auth_code,
        'client_id': api_key,
        'client_secret': api_secret,
        'redirect_uri': redirect_uri,
        'grant_type': 'authorization_code',
    }

    try:
        response = requests.post(token_url, headers=headers, data=data)

        if response.status_code == 200:
            result = response.json()
            access_token = result.get('access_token')

            print("\n✅ Success! Your access token has been generated.\n")
            print("=" * 60)
            print("Save these credentials:")
            print("=" * 60)
            print(f"\nAPI Key:      {api_key}")
            print(f"Access Token: {access_token}")
            print("\n" + "=" * 60)
            print("\nIMPORTANT:")
            print("- Access tokens expire at 6 AM IST daily")
            print("- You'll need to regenerate the token each day")
            print("- Keep these credentials secure")
            print("=" * 60)

            # Save to file
            save = input("\nDo you want to save these to a file? (y/n): ").strip().lower()
            if save == 'y':
                with open('upstox_credentials.txt', 'w') as f:
                    f.write(f"API_KEY={api_key}\n")
                    f.write(f"ACCESS_TOKEN={access_token}\n")
                    f.write(f"# Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                    f.write(f"# Valid until: 6 AM IST next day\n")

                print("\n✅ Credentials saved to 'upstox_credentials.txt'")
                print("⚠️  Add this file to .gitignore to keep credentials secure!")

            # Export commands
            print("\n" + "=" * 60)
            print("To use with the script, run:")
            print("=" * 60)
            print(f"\nexport UPSTOX_API_KEY='{api_key}'")
            print(f"export UPSTOX_ACCESS_TOKEN='{access_token}'")
            print("\nOr add to your ~/.bashrc or ~/.zshrc for persistence")

        else:
            print(f"\n❌ Error: {response.status_code}")
            print(f"Response: {response.text}")
            print("\nPossible issues:")
            print("- Invalid authorization code")
            print("- Authorization code already used")
            print("- Invalid API credentials")
            print("- Redirect URI mismatch (must be exactly: http://127.0.0.1:5000/callback)")

    except Exception as e:
        print(f"\n❌ Error generating access token: {e}")
        print("\nPossible issues:")
        print("- Network connectivity issues")
        print("- Invalid API credentials")
        print("- Server error")


if __name__ == '__main__':
    try:
        generate_upstox_token()
    except KeyboardInterrupt:
        print("\n\n❌ Cancelled by user")
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
