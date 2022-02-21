from greenbudget.lib.utils import empty
from greenbudget.lib.utils import cumulative_product

from . import factories


class ConfigurationError(Exception):
    def __init__(self, config):
        self._config = config


class ConfigurationInvalidError(ConfigurationError):
    def __str__(self):
        return f"The configuration for {self._config.attr} is invalid."


class ConfigurationMissingError(ConfigurationError):
    def __str__(self):
        return f"The configuration for {self._config.attr} is required."


class Configuration:
    def __init__(self, attr, required=False, default=empty):
        self._default = default
        self._attr = attr
        self._required = required

    def raise_missing(self):
        raise ConfigurationMissingError(self)

    def raise_invalid(self):
        raise ConfigurationInvalidError(self)

    def pluck(self, **kwargs):
        if self.required and self.attr not in kwargs:
            self.raise_missing()
        return kwargs.pop(self.attr, self.default)

    @property
    def attr(self):
        return self._attr

    @property
    def default(self):
        return self._default

    @property
    def required(self):
        return self._required


ApplicationDataGeneratorConfig = [
    Configuration(
        attr='num_budgets',
        required=False,
        default=1
    ),
    # The number of accounts per budget.
    Configuration(
        attr='num_accounts',
        required=False,
        default=10
    ),
    # The number of subaccounts per account.
    Configuration(
        attr='num_subaccounts',
        required=False,
        default=10
    ),
    # The number of details per subaccount.
    Configuration(
        attr='num_details',
        required=False,
        default=10
    )
]


USER_FIELDS = ['created_by', 'updated_by']


class ApplicationDataGenerator:
    def __init__(self, user, **config):
        self._user = user
        self._progress = 0
        for c in ApplicationDataGeneratorConfig:
            setattr(self, f'_{c.attr}', c.pluck(**config))

    @property
    def num_instances(self):
        return cumulative_product([
            self._num_budgets,
            self._num_accounts,
            self._num_subaccounts,
            self._num_details
        ])

    def create(self, model_cls, **kwargs):
        factory = factories.registry.get(model_cls)
        for user_field in USER_FIELDS:
            if hasattr(model_cls, user_field) and user_field not in kwargs:
                kwargs[user_field] = self._user
        instance = factory(**kwargs)
        self.increment_progress()
        return instance

    def increment_progress(self):
        self._progress += 1

    @property
    def progress(self):
        return [self._progress, self.num_instances]

    def __call__(self):
        self._progress = 0
        raise NotImplementedError()
