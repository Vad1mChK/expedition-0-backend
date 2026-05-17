import torch

print(f"PyTorch version: {torch.__version__}")
print(f"Is CUDA available: {torch.cuda.is_available()}")

if not torch.cuda.is_available():
    if torch.cuda.device_count() == 0:
        print("Reason: No NVIDIA GPU detected by the system.")
    else:
        print("Reason: Driver/Library mismatch. PyTorch sees the GPU but can't use it.")
else:
    print(f"GPU Name: {torch.cuda.get_device_name(0)}")