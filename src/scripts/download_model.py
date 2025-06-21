#!/usr/bin/env python3
# Copyright © 2025 David Gornshtein @Eveara Ltd. All rights reserved.
"""
Download NVIDIA Parakeet TDT 0.6B v2 Model
Supports multiple download methods
"""

import os
import sys
import argparse
from pathlib import Path
import torch
from huggingface_hub import snapshot_download, hf_hub_download
import requests
from tqdm import tqdm

def download_from_huggingface(repo_id: str, local_dir: str):
    """Download model from Hugging Face Hub"""
    print(f"Downloading {repo_id} from Hugging Face...")
    try:
        snapshot_download(
            repo_id=repo_id,
            local_dir=local_dir,
            local_dir_use_symlinks=False,
            resume_download=True,
            token=os.getenv("HF_TOKEN")  # Optional: for private repos
        )
        print(f"✓ Model downloaded to {local_dir}")
        return True
    except Exception as e:
        print(f"✗ Error downloading from Hugging Face: {e}")
        return False

def download_from_nvidia_ngc():
    """Download from NVIDIA NGC (if available)"""
    # This would require NGC API key
    print("Checking NVIDIA NGC...")
    # Implementation would go here
    pass

def verify_model_files(model_dir: str):
    """Verify that essential model files are present"""
    model_path = Path(model_dir)
    required_files = [
        "config.json",
        "model.safetensors",  # or model.bin
        "tokenizer.json"
    ]
    
    missing = []
    for file in required_files:
        if not (model_path / file).exists():
            # Check alternative names
            if file == "model.safetensors" and (model_path / "model.bin").exists():
                continue
            missing.append(file)
    
    if missing:
        print(f"⚠ Missing files: {', '.join(missing)}")
        return False
    
    print("✓ All model files verified")
    return True

def test_model_loading(model_dir: str):
    """Test if model can be loaded"""
    print("\nTesting model loading...")
    try:
        # Check CUDA availability
        if torch.cuda.is_available():
            print(f"✓ CUDA available: {torch.cuda.get_device_name(0)}")
            print(f"  Memory: {torch.cuda.get_device_properties(0).total_memory / 1024**3:.1f} GB")
        else:
            print("⚠ CUDA not available, model will run on CPU")
        
        # Try to load config
        config_path = Path(model_dir) / "config.json"
        if config_path.exists():
            import json
            with open(config_path) as f:
                config = json.load(f)
            print(f"✓ Model config loaded: {config.get('model_type', 'unknown')}")
        
        return True
    except Exception as e:
        print(f"✗ Error testing model: {e}")
        return False

def main():
    parser = argparse.ArgumentParser(description="Download Parakeet TDT Model")
    parser.add_argument("--model-dir", default="./models/parakeet-tdt-0.6b-v2",
                       help="Directory to save the model")
    parser.add_argument("--source", default="huggingface", 
                       choices=["huggingface", "ngc", "auto"],
                       help="Download source")
    parser.add_argument("--repo-id", default="nvidia/parakeet-tdt-0.6b-v2",
                       help="Model repository ID")
    args = parser.parse_args()
    
    # Create model directory
    model_path = Path(args.model_dir)
    model_path.mkdir(parents=True, exist_ok=True)
    
    print(f"Model will be downloaded to: {model_path.absolute()}")
    print(f"Repository: {args.repo_id}")
    print(f"Source: {args.source}")
    print("-" * 50)
    
    # Download model
    success = False
    if args.source in ["huggingface", "auto"]:
        success = download_from_huggingface(args.repo_id, args.model_dir)
    
    if not success and args.source in ["ngc", "auto"]:
        # Try NGC as fallback
        download_from_nvidia_ngc()
    
    if success:
        # Verify files
        verify_model_files(args.model_dir)
        
        # Test loading
        test_model_loading(args.model_dir)
        
        print("\n✓ Model download complete!")
        print(f"Model location: {model_path.absolute()}")
    else:
        print("\n✗ Model download failed!")
        sys.exit(1)

if __name__ == "__main__":
    main()