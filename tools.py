import secrets

def token_generator(length:int=24):
    return secrets.token_urlsafe(length)
    