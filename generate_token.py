import uuid
import json

def generate_admin_token(nickname):
    token = str(uuid.uuid4())
    try:
        with open('admin_tokens.json', 'r') as f:
            tokens = json.load(f)
    except FileNotFoundError:
        tokens = {}

    tokens[nickname] = token

    with open('admin_tokens.json', 'w') as f:
        json.dump(tokens, f, indent=4)

    print(f'Токен для администратора {nickname}: {token}')

if __name__ == '__main__':
    nickname = input('Введите никнейм администратора: ')
    generate_admin_token(nickname)
