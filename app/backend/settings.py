from os import getenv

from dotenv import load_dotenv


class Settings:
    def __init__(self):
        load_dotenv()
        self.db_user = getenv('DB_USER')
        self.db_password = getenv('DB_PASSWORD')
        self.db_name = getenv('DB_NAME')
        self.db_host = getenv('DB_HOST')
        self.db_port = getenv('DB_PORT')
        self.secret_key = getenv('JWT_SECRET_KEY')
        self.algorithm = getenv('JWT_ALGORITHM')
        self.token_expires_seconds = int(
            getenv('JWT_ACCESS_TOKEN_EXPIRES_SECONDS')
        )


settings = Settings()