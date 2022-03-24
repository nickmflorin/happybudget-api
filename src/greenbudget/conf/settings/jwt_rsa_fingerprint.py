import os
from pathlib import Path

from greenbudget.conf import Environments, config, ConfigInvalidError


BASE_DIR = Path(os.path.abspath(__file__)).parents[2]

JWT_RSA_FINGERPRINT_FILENAME = config(
    name='JWT_RSA_FINGERPRINT_FILENAME',
    required=[Environments.PROD, Environments.DEV]
)

# In local or test environments, we allow the RSA private/public key pairs to
# be defaulted below.
if JWT_RSA_FINGERPRINT_FILENAME:
    JWT_RSA_FINGERPRINT_PATH = BASE_DIR / JWT_RSA_FINGERPRINT_FILENAME

    try:
        # Use double underscores to prevent Django from storing the value in
        # settings for security reasons.
        __JWT_VERIFYING_KEY = open("%s.pub" % JWT_RSA_FINGERPRINT_PATH).read()
    except FileNotFoundError as e:
        raise ConfigInvalidError(
            config_name='JWT_RSA_FINGERPRINT_FILENAME',
            message=(
                "The provided RSA public key %s.pub does not exist."
                % JWT_RSA_FINGERPRINT_PATH
            )
        ) from e
    else:
        if not __JWT_VERIFYING_KEY.startswith('ssh-rsa'):
            raise ConfigInvalidError(
                config_name='JWT_RSA_FINGERPRINT_FILENAME',
                message=(
                    "The provided RSA fingerprint at %s.pub is not a "
                    "valid public RSA key." % JWT_RSA_FINGERPRINT_PATH
                )
            )
    try:
        # Use double underscores to prevent Django from storing the value in
        # settings for security reasons.
        __JWT_SIGNING_KEY = open(str(JWT_RSA_FINGERPRINT_PATH)).read()
    except FileNotFoundError as e:
        raise ConfigInvalidError(
            config_name='JWT_RSA_FINGERPRINT_FILENAME',
            message=(
                "The provided RSA private key %s does not exist."
                % JWT_RSA_FINGERPRINT_PATH
            )
        ) from e
    else:
        # We cannot validate every aspect of the private key, but this is a
        # simple catch to prevent us from starting the application and hitting
        # a live bug when the key is used to encrypt a JWT token.
        if not __JWT_SIGNING_KEY.startswith('-----BEGIN RSA PRIVATE KEY-----'):
            raise ConfigInvalidError(
                config_name='JWT_RSA_FINGERPRINT_FILENAME',
                message=(
                    "The provided RSA fingerprint at %s is not a "
                    "valid private RSA key." % JWT_RSA_FINGERPRINT_PATH
                )
            )
else:
    __JWT_SIGNING_KEY = b'\n'.join([
        b'-----BEGIN RSA PRIVATE KEY-----',
        b'MIIBOwIBAAJBAJttTMyo2bRC5nJZ6tR8DqJiWa4NntaNfWCntw1nif0zFDFW0DcJ',
        b'PI1buHCf8XymwnkT35oW48v8JzPWQVYaM6cCAwEAAQJAHO0hnvFJ2x+cTenoJ3WT',
        b'L6uILzl/t0SL8gIkskzzxHiDkL9PNS8Ax0US+onurVj+wVRV7W278D98BvS7WTSa',
        b'OQIhANuk0Twne3G67nk5zVXFo9DsxTO4frJiFLBjXZ9rR+WjAiEAtSdbymlMI+SA',
        b'TK0TRSa92KtpJ2JTYlbA5uf2dCm/Mi0CIQC4AEzgbdr2HblliMzBi/5+KbvSZj6N',
        b'Rak7UyK9SGxErQIgI8HJFIMETHFmAbyH+TZUctgiwWtfGiIVoX5X30X+P2ECIQDG',
        b'+d6FMgY+Tne95/2/gV76/1MNJhjQaSpDUEJdRmpUpQ==',
        b'-----END RSA PRIVATE KEY-----',
    ])
    __JWT_VERIFYING_KEY = b'\n'.join([
        b'-----BEGIN PUBLIC KEY-----',
        b'MFwwDQYJKoZIhvcNAQEBBQADSwAwSAJBAJttTMyo2bRC5nJZ6tR8DqJiWa4NntaN',
        b'fWCntw1nif0zFDFW0DcJPI1buHCf8XymwnkT35oW48v8JzPWQVYaM6cCAwEAAQ==',
        b'-----END PUBLIC KEY-----',
    ])
