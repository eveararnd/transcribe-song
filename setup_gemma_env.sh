#!/bin/bash

# Setup script for Gemma environment
echo "Setting up Gemma environment..."

# Check if we have the necessary Python packages
echo "Checking Python environment..."

# Try to find a working Python with the required packages
for python_cmd in python3 python python3.10 python3.11; do
    if command -v $python_cmd &> /dev/null; then
        echo "Testing $python_cmd..."
        if $python_cmd -c "import torch, transformers" 2>/dev/null; then
            echo "Found working Python: $python_cmd"
            echo "PyTorch version:" $($python_cmd -c "import torch; print(torch.__version__)")
            echo "Transformers version:" $($python_cmd -c "import transformers; print(transformers.__version__)")
            echo "CUDA available:" $($python_cmd -c "import torch; print(torch.cuda.is_available())")
            
            echo ""
            echo "To run Gemma tests, use: $python_cmd test_gemma_fixed.py"
            exit 0
        fi
    fi
done

echo "No Python installation found with PyTorch and Transformers installed."
echo ""
echo "To set up the environment, you need to:"
echo "1. Create a virtual environment: python3 -m venv gemma_env"
echo "2. Activate it: source gemma_env/bin/activate"
echo "3. Install requirements:"
echo "   pip install torch transformers accelerate bitsandbytes"
echo ""
echo "Or if you have conda:"
echo "   conda create -n gemma python=3.10"
echo "   conda activate gemma"
echo "   pip install torch transformers accelerate bitsandbytes"