# Save this as decrypt_image.py
def decrypt_jpeg(input_path, output_path, key=42):
    with open(input_path, "rb") as f:
        encoded_data = f.read()
    
    # Reverse the (b + key) % 256 logic
    decoded_data = bytes([(b - key) % 256 for b in encoded_data])
    
    with open(output_path, "wb") as f:
        f.write(decoded_data)

decrypt_jpeg("encoded_output.bin", "recovered_flag.jpg")
print("Image recovered as recovered_flag.jpg")