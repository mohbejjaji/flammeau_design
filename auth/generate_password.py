import hashlib
import json

def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

# Générez vos hashs
passwords = {
    "admin": "admin123",  # Changez ce mot de passe !
    "kamal": "kamal2024",
    "youssef": "youssef2024"
}

print("Hashs générés :")
for user, pwd in passwords.items():
    print(f"{user}: {hash_password(pwd)}")

# Mettre à jour users.json
with open('users.json', 'r') as f:
    users = json.load(f)

for user, pwd in passwords.items():
    if user in users:
        users[user]['password_hash'] = hash_password(pwd)

with open('users.json', 'w') as f:
    json.dump(users, f, indent=4)

print("\n✅ users.json mis à jour !")