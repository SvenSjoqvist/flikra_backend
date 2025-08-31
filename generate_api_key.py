#!/usr/bin/env python3
"""
Script to generate a secure API key for the FastAPI backend.
Run this script to generate a new API key and add it to your environment.
"""

import secrets
import string
import os

def generate_api_key(length: int = 64) -> str:
    """Generate a secure API key"""
    # Use a combination of letters, digits, and special characters
    alphabet = string.ascii_letters + string.digits + "-_"
    
    # Generate a secure random string
    api_key = ''.join(secrets.choice(alphabet) for _ in range(length))
    
    return api_key

def main():
    print("🔑 Generating secure API key...")
    
    # Generate the API key
    api_key = generate_api_key()
    
    print(f"\n✅ Generated API key: {api_key}")
    print("\n📝 Add this to your environment variables:")
    print(f"export API_KEY='{api_key}'")
    
    # Check if .env file exists
    env_file = ".env"
    if os.path.exists(env_file):
        print(f"\n📁 Found existing {env_file} file")
        with open(env_file, 'r') as f:
            content = f.read()
        
        if "API_KEY=" in content:
            print("⚠️  API_KEY already exists in .env file")
            print("   You may want to update it with the new key above")
        else:
            print("✅ Adding API_KEY to .env file...")
            with open(env_file, 'a') as f:
                f.write(f"\n# API Key for FastAPI authentication\nAPI_KEY={api_key}\n")
            print("✅ API_KEY added to .env file")
    else:
        print(f"\n📁 Creating {env_file} file...")
        with open(env_file, 'w') as f:
            f.write(f"# API Key for FastAPI authentication\nAPI_KEY={api_key}\n")
        print("✅ Created .env file with API_KEY")
    
    print("\n🔒 Security notes:")
    print("- Keep this API key secret and secure")
    print("- Never commit the API key to version control")
    print("- Use different API keys for development and production")
    print("- Rotate the API key periodically for better security")
    
    print("\n🚀 Next steps:")
    print("1. Restart your FastAPI server to load the new API key")
    print("2. Update your NextJS .env.local with:")
    print(f"   NEXT_PUBLIC_API_KEY='{api_key}'")

if __name__ == "__main__":
    main() 