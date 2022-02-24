import datetime, jwt
from os import getenv
from dotenv import load_dotenv

load_dotenv()

# Get config
jwt_secret_key = getenv('JWT_SECRET_KEY', 'my_precious')
jwt_expiry_duration = int(getenv('JWT_EXPIRY_DURATION', '1000'))

def encode_auth_token(user_id):
    try:
        payload = {
            'exp': datetime.datetime.utcnow() + datetime.timedelta(days=0, seconds=jwt_expiry_duration),
            'iat': datetime.datetime.utcnow(),
            'sub': user_id
        }
        return jwt.encode(
            payload,
            jwt_secret_key,
            algorithm='HS256'
        )
    except Exception as e:
        return e

def decode_auth_token(auth_token):
    try:
        payload = jwt.decode(auth_token, jwt_secret_key, algorithms='HS256')
        return payload['sub']
    except jwt.ExpiredSignatureError:
        return 'expired'
    except jwt.InvalidTokenError:
        return 'invalid'
