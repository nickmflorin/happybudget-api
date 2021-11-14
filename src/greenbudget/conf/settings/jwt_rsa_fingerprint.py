from greenbudget.conf import Environments, config, ConfigInvalidError


JWT_RSA_FINGERPRINT = config(
    name='JWT_RSA_FINGERPRINT',
    required=[Environments.PROD, Environments.DEV]
)
# In local or test environments, we allow the RSA private/public key pairs to
# be defaulted below.
if JWT_RSA_FINGERPRINT:
    try:
        # Use double underscores to prevent Django from storing the value in
        # settings for security reasons.
        __JWT_VERIFYING_KEY = open("%s.pub" % JWT_RSA_FINGERPRINT).read()
    except FileNotFoundError:
        raise ConfigInvalidError(
            config_name='JWT_RSA_FINGERPRINT',
            message=(
                "The provided RSA public key %s.pub does not exist."
                % JWT_RSA_FINGERPRINT
            )
        )
    else:
        if not __JWT_VERIFYING_KEY.startswith('ssh-rsa'):
            raise ConfigInvalidError(
                config_name='JWT_RSA_FINGERPRINT',
                message=(
                    "The provided RSA fingerprint at %s.pub is not a "
                    "valid public RSA key." % JWT_RSA_FINGERPRINT
                )
            )
    try:
        # Use double underscores to prevent Django from storing the value in
        # settings for security reasons.
        __JWT_SIGNING_KEY = open(JWT_RSA_FINGERPRINT).read()
    except FileNotFoundError:
        raise ConfigInvalidError(
            config_name='JWT_RSA_FINGERPRINT',
            message=(
                "The provided RSA private key %s does not exist."
                % JWT_RSA_FINGERPRINT
            )
        )
    else:
        # We cannot validate every aspect of the private key, but this is a
        # simple catch to prevent us from starting the application and hitting
        # a live bug when the key is used to encrypt a JWT token.
        if not __JWT_SIGNING_KEY.startswith('-----BEGIN RSA PRIVATE KEY-----'):
            raise ConfigInvalidError(
                config_name='JWT_RSA_FINGERPRINT',
                message=(
                    "The provided RSA fingerprint at %s is not a "
                    "valid private RSA key." % JWT_RSA_FINGERPRINT
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
