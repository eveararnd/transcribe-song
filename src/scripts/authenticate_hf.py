#!/usr/bin/env python3
# Copyright © 2025 David Gornshtein @Eveara Ltd. All rights reserved.
"""
Authenticate with Hugging Face
"""
import os
import sys
from huggingface_hub import login, HfApi, HfFolder
import getpass

def authenticate_huggingface():
    """Interactive Hugging Face authentication"""
    print("🤗 Hugging Face Authentication")
    print("="*50)
    
    # Check if already authenticated
    try:
        api = HfApi()
        user_info = api.whoami()
        print(f"✓ Already authenticated as: {user_info['name']}")
        return True
    except:
        pass
    
    print("\nYou need to authenticate with Hugging Face.")
    print("\nSteps:")
    print("1. Go to: https://huggingface.co/settings/tokens")
    print("2. Log in with your account (daiditenax@gmail.com)")
    print("3. Click 'New token'")
    print("4. Name it 'parakeet-music' (or any name)")
    print("5. Select 'read' permissions")
    print("6. Create the token and copy it")
    print("\nOnce you have the token, you can:")
    print("\nOption 1: Set environment variable (recommended)")
    print("export HF_TOKEN='your_token_here'")
    print("\nOption 2: Use huggingface-cli")
    print("huggingface-cli login")
    print("\nOption 3: Create a .env file with:")
    print("HF_TOKEN=your_token_here")
    
    # Try to authenticate if token is provided
    token = input("\nPaste your token here (or press Enter to skip): ").strip()
    
    if token:
        try:
            login(token=token, add_to_git_credential=False)
            print("\n✓ Authentication successful!")
            
            # Verify
            api = HfApi()
            user_info = api.whoami()
            print(f"Logged in as: {user_info['name']}")
            
            # Save to .env file
            save_to_env = input("\nSave token to .env file? (y/n): ").lower().strip()
            if save_to_env == 'y':
                env_path = "/home/davegornshtein/parakeet-tdt-deployment/.env"
                
                # Read existing .env
                env_content = ""
                if os.path.exists(env_path):
                    with open(env_path, 'r') as f:
                        env_content = f.read()
                
                # Add or update HF_TOKEN
                if "HF_TOKEN=" in env_content:
                    lines = env_content.split('\n')
                    for i, line in enumerate(lines):
                        if line.startswith("HF_TOKEN="):
                            lines[i] = f"HF_TOKEN={token}"
                    env_content = '\n'.join(lines)
                else:
                    env_content += f"\n# Hugging Face\nHF_TOKEN={token}\n"
                
                # Write back
                with open(env_path, 'w') as f:
                    f.write(env_content)
                
                print(f"✓ Token saved to {env_path}")
            
            return True
            
        except Exception as e:
            print(f"\n✗ Authentication failed: {e}")
            return False
    else:
        print("\nNo token provided. Please authenticate manually.")
        return False

if __name__ == "__main__":
    success = authenticate_huggingface()
    
    if success:
        print("\n" + "="*50)
        print("Next steps:")
        print("1. Make sure you have access to Gemma:")
        print("   https://huggingface.co/google/gemma-2b")
        print("2. Click 'Agree and access repository' if needed")
        print("3. You can now use Gemma in your code!")
        print("="*50)
    
    sys.exit(0 if success else 1)