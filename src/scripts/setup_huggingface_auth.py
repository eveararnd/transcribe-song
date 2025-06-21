#!/usr/bin/env python3
# Copyright © 2025 David Gornshtein @Eveara Ltd. All rights reserved.
"""
Set up Hugging Face authentication
"""
import os
from huggingface_hub import login, HfApi, HfFolder

def setup_huggingface_auth():
    """Set up Hugging Face authentication"""
    print("Setting up Hugging Face authentication...")
    
    # Method 1: Using environment variable
    print("\nMethod 1: Setting HF_TOKEN environment variable")
    # You'll need to get your token from https://huggingface.co/settings/tokens
    # Create a token with 'read' permissions
    
    # Method 2: Using huggingface-cli login
    print("\nMethod 2: Using huggingface-cli")
    print("Run this command in terminal:")
    print("huggingface-cli login")
    print("Then paste your token when prompted")
    
    # Method 3: Using login() function
    print("\nMethod 3: Using Python login()")
    print("Get your token from: https://huggingface.co/settings/tokens")
    print("Then run:")
    print("from huggingface_hub import login")
    print("login(token='your_token_here')")
    
    # Check current authentication status
    try:
        api = HfApi()
        user_info = api.whoami()
        print(f"\n✓ Currently authenticated as: {user_info['name']}")
        return True
    except Exception as e:
        print(f"\n✗ Not authenticated: {str(e)}")
        print("\nTo authenticate:")
        print("1. Go to https://huggingface.co/settings/tokens")
        print("2. Create a new token with 'read' permissions")
        print("3. Run: huggingface-cli login")
        print("4. Paste your token when prompted")
        return False

if __name__ == "__main__":
    setup_huggingface_auth()
    
    # Additional instructions for Gemma access
    print("\n" + "="*50)
    print("For Gemma model access:")
    print("1. Go to https://huggingface.co/google/gemma-2b")
    print("2. Click 'Agree and access repository' if you haven't already")
    print("3. Make sure you're logged in with your account")
    print("="*50)