import secrets

# Generate a secure random string
secret_key = secrets.token_hex(16)  # 16 bytes = 32 hexadecimal characters
print(f"Generated SECRET_KEY: {secret_key}")
