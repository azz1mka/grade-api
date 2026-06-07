import bcrypt

password = b"admin123"
hashed = bcrypt.hashpw(password, bcrypt.gensalt()).decode()
print(hashed)