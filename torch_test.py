import torch

def test_torch_cuda():
    # Check if CUDA (GPU) is available
    if torch.cuda.is_available():
        print("CUDA is available!")
        # Get the current GPU device name
        print(f"GPU device: {torch.cuda.get_device_name(0)}")

        # Perform a basic tensor operation on the GPU
        tensor = torch.rand(3, 3).to('cuda')  # Create a random tensor and move it to the GPU
        print("Tensor created on GPU:")
        print(tensor)
    else:
        print("CUDA is not available. Running on CPU.")

if __name__ == "__main__":
    test_torch_cuda()
