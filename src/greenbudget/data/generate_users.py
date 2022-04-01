import copy

from django.conf import settings
from django.core.files import File

from greenbudget.lib.utils import humanize_list
from greenbudget.app.user.models import User


class UserData:
    defaults = {
        'is_superuser': False,
        'is_active': True,
        'is_verified': True,
        'is_staff': False,
        'is_first_time': False
    }
    img_extensions = ['jpeg', 'jpg', 'png']

    def __init__(self, first_name, last_name, **kwargs):
        self._first_name = first_name
        self._last_name = last_name
        self._email = kwargs.pop('email', None)
        self._email_domain = kwargs.pop('email_domain', None)
        self._kwargs = kwargs

    @property
    def first_name(self):
        return self._first_name.title()

    @property
    def last_name(self):
        return self._last_name.title()

    def __str__(self):
        return f"{self.first_name} {self.last_name}"

    def __repr__(self):
        return f"{self.first_name} {self.last_name}"

    @property
    def email_domain(self):
        return self._email_domain or "gmail.com"

    @property
    def email(self):
        if self._email is not None:
            return self._email
        return (
            f"{self.first_name.lower()}{self.last_name.lower()}"
            f"@{self.email_domain}"
        )

    @property
    def possible_profile_image_file_names(self):
        base = f"{self.first_name.lower()}-{self.last_name.lower()}"
        return [f"{base}.{ext}" for ext in self.img_extensions]

    def get_profile_image_path(self, cmd):
        existing_paths = [pt for pt in [
            settings.BASE_DIR / "data" / "user_images" / filename
            for filename in self.possible_profile_image_file_names
        ] if pt.exists()]
        if len(existing_paths) > 1:
            humanized = humanize_list(["%s" % pt for pt in existing_paths])
            cmd.warning(
                "Multiple valid profile images found for same user at %s."
                % humanized
            )
        if existing_paths:
            return existing_paths[0]
        return None

    def load_profile_image(self, cmd):
        path = self.get_profile_image_path(cmd)
        if path is not None:
            return File(file=open(str(path), 'rb'), name=path.name)
        cmd.info("No profile image found for user %s." % self)
        return None

    def _create(self, cmd, **overrides):
        base_kwargs = copy.deepcopy(self.defaults)
        base_kwargs.update(**self._kwargs)
        base_kwargs.update(**overrides)

        profile_image = self.load_profile_image(cmd)
        return User.objects.create(
            first_name=self.first_name,
            last_name=self.last_name,
            email=self.email.lower(),
            profile_image=profile_image,
            password='test_user_password1234',
            **base_kwargs
        )

    def create(self, cmd, **overrides):
        force = overrides.pop('force', False)
        try:
            user = User.objects.get(email=self.email.lower())
        except User.DoesNotExist:
            return self._create(cmd, **overrides)
        else:
            if force:
                cmd.info(f"Deleting user {self} so it can be recreated.")
                user.delete()
                return self._create(cmd, **overrides)
            cmd.info(f"Skipping user {self} as it already exists.")
            return None


USER_DATA = [
    UserData(first_name='Steve', last_name='Aoki'),
    UserData(first_name='Homer', last_name='Simpson'),
    UserData(first_name='Peter', last_name='Griffin'),
    UserData(first_name='Jerry', last_name='Springer'),
    UserData(first_name='Pablo', last_name='Escobar'),
    UserData(first_name='Ronald', last_name='Regan'),
    UserData(first_name='Fidel', last_name='Castro'),
    UserData(
        first_name='George',
        last_name='Washington',
        email="george@whitehouse.gov"
    ),
    UserData(
        first_name='Elizabeth',
        last_name='Holmes',
        email="fraud@theranos.io"
    ),
    UserData(first_name='Joe', last_name='Biden', email_domain='whitehouse.gov'),
    UserData(
        first_name='Osama',
        last_name='BinLaden',
        email_domain='alquaida.ai'
    )
]


class UserGenerator:
    def __init__(self, cmd):
        self.cmd = cmd

    def __call__(self, **kwargs):
        for datum in USER_DATA:
            datum.create(self.cmd, **kwargs)
