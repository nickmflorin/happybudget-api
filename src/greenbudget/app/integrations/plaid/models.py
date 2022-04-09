import logging

from greenbudget.app.actual.models import ActualType


logger = logging.getLogger('greenbudget')


class PlaidAccountType:
    """
    The type of an Account in Plaid.

    This list is exhaustive and encompasses every possible type that an Account
    can have in Plaid.

    Further information can be found here:
    https://plaid.com/docs/api/products/transactions/#transactions-get-response-
    accounts-type
    """
    INVESTMENT = 'investment'
    CREDIT = 'credit'
    DEPOSITORY = 'depository'
    LOAN = 'loan'
    # This value has been deprecated in newer versions of the API.  It's
    # replacement is 'investment'.
    BROKERAGE = 'brokerage'
    OTHER = 'other'


class PlaidAccountSubType:
    """
    The sub-type of an Account in Plaid.

    This list is not exhaustive, there are many, many more sub-types that their
    API can return that are not listed here.  Only the sub-types that we are
    concerned with are attributed to this class.

    The full list of sub-types can be found here:
    https://plaid.com/docs/api/products/transactions/#transactions-get-response
    accounts-subtype
    """
    SAVINGS = 'savings'
    CREDIT_CARD = 'credit card'
    PAYPAL = 'paypal'
    CHECKING = 'checking'
    OVERDRAFT = 'overdraft'
    DEPOSIT = 'deposit'


class PlaidTransactionClassification:
    evaluations = [
        'transaction_check', 'account_check', 'account_type',
        'account_subtype'
    ]

    def __init__(self, transaction_type, **kwargs):
        self._transaction_type = transaction_type

        assert any([x in kwargs for x in self.evaluations]), \
            "At least one evaluation criteria must be provided."

        self._account_check = kwargs.pop('account_check', None)
        self._transaction_check = kwargs.pop('transaction_check', None)
        self._account_type = kwargs.pop('account_type', None)
        self._account_subtype = kwargs.pop('account_subtype', None)

    def __call__(self, transaction):
        if any([
            getattr(self, evaluation)(transaction) is False
            for evaluation in self.evaluations
        ]):
            return None
        return self._transaction_type

    def transaction_check(self, t):
        if self._transaction_check is not None \
                and not self._transaction_check(t):
            return False
        return True

    def account_check(self, t):
        if self._account_check is not None and (
                t.account is None or not self._account_check(t.account)):
            return False
        return True

    def account_type(self, t):
        if self._account_type is not None and (
                t.account is None or self._account_type != t.account.type):
            return False
        return True

    def account_subtype(self, t):
        if self._account_subtype is not None and (
                t.account is None
                or self._account_subtype != t.account.subtype):
            return False
        return True


CLASSIFICATIONS = [
    PlaidTransactionClassification(
        account_type=PlaidAccountType.CREDIT,
        account_subtype=PlaidAccountSubType.CREDIT_CARD,
        transaction_type=ActualType.PLAID_TRANSACTION_TYPES.credit_card
    )
]


class PlaidModel:
    attrs = []

    def __init__(self, *args, **kwargs):
        data = dict(*args, **kwargs)
        for attr in self.attribute_pairs:
            setattr(self, f'_{attr[1]}', data[attr[0]])

    @property
    def id(self):
        return self._id

    def __repr__(self):
        return str({k[1]: getattr(self, k[1]) for k in self.attribute_pairs})

    def __str__(self):
        return self.__repr__()

    @property
    def attribute_pairs(self):
        return [(k, k) if not isinstance(k, tuple) else k for k in self.attrs]

    @classmethod
    def ensure_models(cls, *args, models):
        return [m if isinstance(m, cls) else cls(*args, **m) for m in models]


class PlaidAccount(PlaidModel):
    attrs = (('account_id', 'id'), 'name', 'official_name', 'type', 'subtype')

    @property
    def name(self):
        return self._name

    @property
    def official_name(self):
        return self._official_name

    @property
    def type(self):
        return self._type

    @property
    def subtype(self):
        return self._subtype


class PlaidTransaction(PlaidModel):
    attrs = (
        ('transaction_id', 'id'), 'datetime', 'date', 'name',
        'merchant_name', 'amount', 'iso_currency_code', 'account_id',
        ('category', 'categories')
    )

    def __init__(self, user, accounts, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._accounts = accounts
        self._user = user

    @property
    def accounts(self):
        return PlaidAccount.ensure_models(models=self._accounts)

    @property
    def account(self):
        filtered = [a for a in self.accounts if a.id == self.account_id]
        if not filtered:
            logger.error(
                f"Plaid's API returned {len(self.accounts)} but none of them "
                f"map to the account ID {self.account_id} associated with "
                "transaction {self.id}.", extra={
                    'user_id': self._user.pk,
                    'user_email': self._user.email,
                    'transaction_id': self.id,
                    'account_id': self.account_id,
                    'accounts': ', '.join([a.id for a in self.accounts])
                }
            )
            return None
        elif len(filtered) != 1:
            logger.error(
                f"Plaid's API returned multiple ({len(filtered)}) accounts "
                f"for the same account ID {self.account_id} for transaction "
                f"{self.id}.", extra={
                    'user_id': self._user.pk,
                    'user_email': self._user.email,
                    'transaction_id': self.id,
                    'account_id': self.account_id,
                    'accounts': ', '.join([a.id for a in self.accounts])
                }
            )
        return filtered[0]

    @property
    def transaction_type_classification(self):
        for classification in CLASSIFICATIONS:
            result = classification(self)
            if result is not None:
                return result
        return None

    @property
    def account_id(self):
        return self._account_id

    @property
    def iso_currency_code(self):
        return self._iso_currency_code

    @property
    def datetime(self):
        if self._datetime is not None:
            return self._user.in_timezone(self._datetime)
        elif self._date is not None:
            return self._user.in_timezone(self._date, force_datetime=True)
        return None

    @property
    def date(self):
        if self._date is not None:
            return self._user.in_timezone(self._date)
        # If the datetime is None, the `_date` attribute is guaranteed to be
        # None - so we cannot convert.
        elif self.datetime is not None:
            # Use the timezone aware datetime property instead of the raw date
            # value returned from the API as it is already made timezone aware.
            return self.datetime.date()
        return None

    @property
    def amount(self):
        return self._amount

    @property
    def name(self):
        return self._name

    @property
    def merchant_name(self):
        return self._merchant_name

    @property
    def categories(self):
        return self._categories
