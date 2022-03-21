from tqdm import tqdm

from greenbudget.management import CustomCommand, debug_only, Query

from greenbudget.app import cache
from greenbudget.data import generate


@debug_only
class Command(CustomCommand):
    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Instantiate the models but do not persist them to database.',
        )

    @cache.disable()
    @Query.Integer.include(
        param='num_budgets',
        default=1,
        max_value=5,
        prompt='Enter the number of budgets you would like to generate.',
        prefix='No. Budgets'
    )
    @Query.Integer.include(
        param='num_accounts',
        default=10,
        max_value=20,
        prompt=(
            'Enter the number of accounts per budget you would like to '
            'generate.'
        ),
        prefix='No. Accounts'
    )
    @Query.Integer.include(
        param='num_subaccounts',
        default=10,
        max_value=20,
        prompt=(
            'Enter the number of subaccounts per account you would like to '
            'generate.'
        ),
        prefix='No. Sub Accounts'
    )
    @Query.Integer.include(
        param='num_details',
        default=10,
        max_value=20,
        prompt=(
            'Enter the number of subaccounts per subaccount you would like to '
            'generate.'
        ),
        prefix='No. Sub Accounts'
    )
    @Query.Boolean.include(
        param="include_fringes",
        default=False,
        prompt='Would you like to generate fringes?',
        query_on_confirm=Query.Integer.include(
            param='num_fringes',
            default=10,
            max_value=20,
            prompt=(
                'Enter the number of fringes per budget you would like to '
                'generate.'
            ),
            prefix='No. Fringes'
        )
    )
    @Query.Boolean.include(
        param="include_contacts",
        default=False,
        prompt='Would you like to generate contacts?',
        query_on_confirm=Query.Integer.include(
            param='num_contacts',
            default=10,
            max_value=50,
            prompt='Enter the number of contacts you would like to generate.',
            prefix='No. Contacts'
        )
    )
    @Query.Boolean.include(
        param="include_groups",
        default=False,
        prompt='Would you like to generate groups?',
        query_on_confirm=Query.Integer.include(
            param='num_groups',
            default=3,
            max_value=8,
            unconfirmed_value=None,
            prompt='Enter the number of groups per table you would like to generate.'  # noqa
        )
    )
    @Query.User.include(
        prompt="Provide the user the data should be generated for.",
        validators=[
            Query.User.Validator(
                lambda user: user.is_superuser,
                message="User must be a superuser."
            ),
            Query.User.Validator(
                lambda user: user.is_staff,
                message="User must be a staff user."
            )
        ]
    )
    def handle(self, user, **options):
        config = generate.ApplicationDataGeneratorConfig(
            user=user,
            cmd=self,
            **options
        )
        with tqdm(total=config.num_instances) as pbar:
            generator = generate.ApplicationDataGenerator(
                pbar=pbar,
                config=config
            )
            generator()
