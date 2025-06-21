#!/usr/bin/env python3
# Copyright © 2025 David Gornshtein @Eveara Ltd. All rights reserved.
"""
Download Gemma model for local use
"""
import os
import sys
from huggingface_hub import snapshot_download, login
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def download_gemma_model():
    """Download Gemma model to local directory"""
    model_name = "google/gemma-3n-E4B-it-litert-lm-preview"
    local_dir = Path("/home/davegornshtein/parakeet-tdt-deployment/models/gemma-3n-E4B")
    
    print(f"🤖 Downloading {model_name}")
    print(f"📁 To: {local_dir}")
    print("="*70)
    
    # Authenticate with HF token
    hf_token = os.getenv('HF_TOKEN')
    if hf_token:
        try:
            login(token=hf_token, add_to_git_credential=False)
            print("✓ Authenticated with Hugging Face")
        except Exception as e:
            print(f"⚠️ Authentication warning: {e}")
    else:
        print("⚠️ No HF_TOKEN found in environment")
    
    # Create directory
    local_dir.mkdir(parents=True, exist_ok=True)
    
    try:
        # Download the model
        print(f"\nDownloading model files...")
        downloaded_path = snapshot_download(
            repo_id=model_name,
            local_dir=str(local_dir),
            local_dir_use_symlinks=False,
            resume_download=True,
            token=hf_token
        )
        
        print(f"\n✓ Model downloaded to: {downloaded_path}")
        
        # List downloaded files
        print("\nDownloaded files:")
        for file in local_dir.rglob("*"):
            if file.is_file():
                size_mb = file.stat().st_size / (1024**2)
                print(f"  - {file.name} ({size_mb:.1f} MB)")
        
        # Update .env with local model path
        env_path = Path("/home/davegornshtein/parakeet-tdt-deployment/.env")
        with open(env_path, 'a') as f:
            f.write(f"\n# Gemma model path\n")
            f.write(f"GEMMA_MODEL_PATH={local_dir}\n")
        
        print(f"\n✓ Added GEMMA_MODEL_PATH to .env")
        
        return str(local_dir)
        
    except Exception as e:
        print(f"\n❌ Error downloading model: {e}")
        return None

if __name__ == "__main__":
    model_path = download_gemma_model()
    
    if model_path:
        print("\n" + "="*70)
        print("✅ Model download complete!")
        print(f"Path: {model_path}")
        print("\nTo use the model, update your code to use the local path:")
        print(f'model_name = "{model_path}"')
        print("="*70)
    else:
        print("\n❌ Model download failed")
        sys.exit(1)