"""
Helper script to generate Zerodha access token
Run this once to get your access token
"""

from kiteconnect import KiteConnect
import webbrowser

def generate_access_token():
    """Interactive script to generate access token"""

    print("=" * 60)
    print("Zerodha Access Token Generator")
    print("=" * 60)

    # Step 1: Get API credentials
    api_key = input("\nEnter your API Key: ").strip()
    api_secret = input("Enter your API Secret: ").strip()

    if not api_key or not api_secret:
        print("❌ API Key and Secret are required!")
        return

    # Step 2: Generate login URL
    kite = KiteConnect(api_key=api_key)
    login_url = kite.login_url()

    print("\n" + "=" * 60)
    print("STEP 1: Login to Zerodha")
    print("=" * 60)
    print(f"\nOpening browser to: {login_url}")
    print("\nPlease login with your Zerodha credentials.")
    print("After login, you'll be redirected to a URL.")

    # Open browser
    try:
        webbrowser.open(login_url)
    except:
        print("Could not open browser automatically.")
        print(f"Please manually open: {login_url}")

    # Step 3: Get request token from redirect URL
    print("\n" + "=" * 60)
    print("STEP 2: Get Request Token")
    print("=" * 60)
    print("\nAfter logging in, you'll be redirected to a URL like:")
    print("http://127.0.0.1/?request_token=XXXXX&action=login&status=success")
    print("\n⚠️  IMPORTANT: The browser will show 'Unable to connect' - THIS IS NORMAL!")
    print("The request_token is still in the URL bar - just copy it from there.")
    print("\nCopy ONLY the 'request_token' value from that URL (the part after request_token=)")
    print("Example: If URL shows 'request_token=abc123xyz', enter: abc123xyz")

    request_token = input("\nEnter the request_token: ").strip()

    if not request_token:
        print("❌ Request token is required!")
        return

    # Step 4: Generate access token
    print("\n" + "=" * 60)
    print("STEP 3: Generating Access Token...")
    print("=" * 60)

    try:
        data = kite.generate_session(request_token, api_secret=api_secret)
        access_token = data["access_token"]

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
            with open('zerodha_credentials.txt', 'w') as f:
                f.write(f"API_KEY={api_key}\n")
                f.write(f"ACCESS_TOKEN={access_token}\n")
                f.write(f"# Generated on: {data.get('login_time', 'N/A')}\n")
                f.write(f"# Valid until: 6 AM IST next day\n")

            print("\n✅ Credentials saved to 'zerodha_credentials.txt'")
            print("⚠️  Add this file to .gitignore to keep credentials secure!")

        # Export commands
        print("\n" + "=" * 60)
        print("To use with the script, run:")
        print("=" * 60)
        print(f"\nexport ZERODHA_API_KEY='{api_key}'")
        print(f"export ZERODHA_ACCESS_TOKEN='{access_token}'")
        print("\nOr add to your ~/.bashrc or ~/.zshrc for persistence")

    except Exception as e:
        print(f"\n❌ Error generating access token: {e}")
        print("\nPossible issues:")
        print("- Invalid request token")
        print("- Request token already used")
        print("- Invalid API secret")
        print("- Network connectivity issues")


if __name__ == '__main__':
    try:
        generate_access_token()
    except KeyboardInterrupt:
        print("\n\n❌ Cancelled by user")
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
