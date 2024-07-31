import torch
import torchvision
from torchvision import transforms

# Load SlowFast model
model = torch.hub.load('facebookresearch/SlowFast', 'slowfast_r50', pretrained=True)
model.eval()

# Dummy input for inference (batch_size=1, channels=3, frames=32, height=224, width=224)
input_tensor = torch.rand(1, 3, 32, 224, 224)

# Perform inference
output = model(input_tensor)
print(output)
