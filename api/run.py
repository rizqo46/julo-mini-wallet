from __init__ import app
from os import getenv
from dotenv import load_dotenv

load_dotenv()

# Get config
PORT = getenv('PORT', '80')
if __name__ == "__main__":
    app.run(port=PORT)