import re

email = input("Enter your email address: ").strip()

if re.search(r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$", email):
    print("Valid email address.")
else:
    print("Invalid email address.")

