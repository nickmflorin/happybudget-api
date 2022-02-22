from greenbudget.management import (
    CustomCommand, debug_only, query_and_include_user,
    query_and_include_integer, Validator)

from greenbudget.app import cache
from greenbudget.data import generate


@debug_only
class Command(CustomCommand):
    @cache.disable()
    @query_and_include_integer(
        param='num_budgets',
        default=1,
        max_value=5,
        prompt='Enter the number of budgets you would like to generate.',
        prefix='No. Budgets'
    )
    @query_and_include_integer(
        param='num_accounts',
        default=10,
        max_value=20,
        prompt=(
            'Enter the number of accounts per budget you would like to '
            'generate.'
        ),
        prefix='No. Accounts'
    )
    @query_and_include_integer(
        param='num_subaccounts',
        default=10,
        max_value=20,
        prompt=(
            'Enter the number of subaccounts per account you would like to '
            'generate.'
        ),
        prefix='No. Sub Accounts'
    )
    @query_and_include_integer(
        param='num_details',
        default=10,
        max_value=20,
        prompt=(
            'Enter the number of subaccounts per subaccount you would like to '
            'generate.'
        ),
        prefix='No. Sub Accounts'
    )
    @query_and_include_user(
        prompt="Provide the user the data should be generated for.",
        validators=[
            Validator(
                lambda user: user.is_superuser,
                message="User must be a superuser."
            ),
            Validator(
                lambda user: user.is_staff,
                message="User must be a staff user."
            )
        ]
    )
    def handle(self, user, **options):
        gen = generate.ApplicationDataGenerator(user, **options)
        gen()
