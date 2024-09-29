import tensorflow as tf

# Load the Vivit model
model_path = 'tf_saved_models/vivit-b-16x2-kinetics400'
model = tf.saved_model.load(model_path)

# Check the model's signatures
print("Model Signatures:")
print(model.signatures)

# Access all variables in the model
variables = model.variables  # For trainable variables
# If needed, also access non-trainable variables
# all_variables = model.variables  # Uncomment this if you need all variables

# Print variable names and values
print("\nTrainable Variables:")
for var in variables:
    print(f"Variable Name: {var.name}, Shape: {var.shape}")

print(model.__dict__)