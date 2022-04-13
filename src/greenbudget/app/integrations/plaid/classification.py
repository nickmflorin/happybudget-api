from greenbudget.lib.utils.abstract import ImmutableSequence
from greenbudget.app.actual.models import ActualType

from .constants import (
    PlaidAccountType, PlaidAccountSubType, PlaidCategoryGroup,
    PlaidHierarchy1, PlaidHierarchy2, PlaidHierarchy3)


class PlaidCategory(ImmutableSequence):
    """
    An object that represents a category object in Plaid.  Each category
    object has a group, the options for which are defined on the
    :obj:`PlaidCategoryGroup` class, and up to 3 categorization values which
    we refer to as the hierarchy.

    The category hierarchies are nested, such that every categorization with
    3 hierarchy values will have a parent with just the first two hierarchy
    values:

    >>> ["Transfer"]
    >>> ["Transfer", "Deposit"]
    >>> ["Transfer", "Deposit", "Check"]
    """

    def __init__(self, group, *args):
        super().__init__(*args)
        self.group = group

    @classmethod
    def special(cls, *hierarchy):
        return cls(PlaidCategoryGroup.SPECIAL, *hierarchy)

    @classmethod
    def place(cls, *hierarchy):
        return cls(PlaidCategoryGroup.PLACE, *hierarchy)

    def extend(self, hierarchy):
        return self.__class__(self.group, self.data + list(hierarchy))

    def __eq__(self, other):
        assert isinstance(other, (list, tuple, self.__class__)), \
            f"The value must be an iterable or instance of {self.__class__}."
        if isinstance(other, self.__class__):
            return other.data == self.data
        return list(self.data) == list(other)

    def is_equal_or_parent_of(self, other):
        assert isinstance(other, (list, tuple, self.__class__)), \
            f"The value must be an iterable or instance of {self.__class__}."
        comparison = other
        if isinstance(other, self.__class__):
            comparison = other.data
        if len(comparison) < len(self.data):
            return False
        return comparison[:len(self.data)] == self.data

    def is_equal_or_subset_of(self, other):
        assert isinstance(other, (list, tuple, self.__class__)), \
            f"The value must be an iterable or instance of {self.__class__}."
        comparison = other
        if isinstance(other, self.__class__):
            comparison = other.data
        if len(comparison) > len(self.data):
            return False
        return self.data == comparison[:len(self.data)]


class PlaidCategories:
    """
    A class that defines the possible Plaid category combinatations based on
    the category group and the category hierarchy.

    This class does not represent all of the possible category combinations
    that Plaid may return, but just those for which we are interested.

    In order to get a downloadable CSV file, or simply stdout all of the
    category combinations that Plaid offers, the `get_plaid_categories`
    management command can be used.
    """
    BANK_FEES = PlaidCategory.special([PlaidHierarchy1.BANK_FEES])
    INSUFFICIENT_FUNDS_FEES = BANK_FEES.extend(
        [PlaidHierarchy2.INSUFFICIENT_FUNDS])
    ATM_FEES = BANK_FEES.extend([PlaidHierarchy2.ATM])
    LATE_PAYMENT = BANK_FEES.extend([PlaidHierarchy2.LATE_PAYMENT])
    WIRE_TRANSFER_FEES = BANK_FEES.extend([PlaidHierarchy2.WIRE_TRANSFER])
    OVERDRAFT_FEES = BANK_FEES.extend([PlaidHierarchy2.OVERDRAFT])

    PAYMENT = PlaidCategory.special([PlaidHierarchy1.PAYMENT])
    CREDIT_CARD_PAYMENT = PAYMENT.extend([PlaidHierarchy2.CREDIT_CARD])
    RENT_PAYMENT = PAYMENT.extend([PlaidHierarchy2.RENT])
    LOAN_PAYMENT = PAYMENT.extend([PlaidHierarchy2.LOAN])

    TRANSFER = PlaidCategory.special([PlaidHierarchy1.TRANSFER])
    ACH_TRANSFER = TRANSFER.extend([PlaidHierarchy2.ACH])
    CREDIT_TRANSFER = TRANSFER.extend([PlaidHierarchy2.CREDIT])
    DEBIT_TRANSFER = TRANSFER.extend([PlaidHierarchy2.DEBIT])
    CHECK_TRANSFER = TRANSFER.extend([PlaidHierarchy2.CHECK])
    WIRE_TRANSFER = TRANSFER.extend([PlaidHierarchy2.WIRE])

    DEPOSIT = TRANSFER.extend([PlaidHierarchy2.DEPOSIT])
    CHECK_DEPOSIT = DEPOSIT.extend([PlaidHierarchy3.CHECK])
    ATM_DEPOSIT = DEPOSIT.extend([PlaidHierarchy3.ATM])

    WITHDRAWAL = TRANSFER.extend([PlaidHierarchy2.WITHDRAWAL])
    CHECK_WITHDRAWAL = WITHDRAWAL.extend([PlaidHierarchy3.CHECK])
    ATM_WITHDRAWAL = WITHDRAWAL.extend([PlaidHierarchy3.ATM])


class PlaidClassification:
    """
    Represents a set of conditionals that can be used to classify a
    :obj:`PlaidTransaction`.  The conditionals will only be evaluated if
    provided, and if any evaluated to `True`, the classification value will
    be returned.
    """
    evaluations = ['transaction', 'account', 'account_type', 'account_subtype']

    def __init__(self, classification, **kwargs):
        self._classification = classification
        assert any([x in kwargs for x in self.evaluations]), \
            "At least one evaluation criteria must be provided."

        self._account = kwargs.pop('account', None)
        self._transaction = kwargs.pop('transaction', None)
        self._account_type = kwargs.pop('account_type', None)
        self._account_subtype = kwargs.pop('account_subtype', None)

    def __call__(self, obj):
        if any([
            getattr(self, evaluation)(obj) is False
            for evaluation in self.evaluations
        ]):
            return None
        return self._classification

    def transaction(self, t):
        if self._transaction is not None and not self._transaction(t):
            return False
        return True

    def account(self, t):
        if self._account is not None and (
                t.account is None or not self._account(t.account)):
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


class PlaidClassifications(ImmutableSequence):
    """
    Represents a set of :obj:`PlaidClassification`(s) that can be applied to
    a :obj:`PlaidTransaction`.
    """

    def __init__(self, *args, **kwargs):
        self._default = kwargs.pop('default', None)
        super().__init__(*args, **kwargs)

    def classify(self, obj):
        """
        Determines whether or not the given :obj:`PlaidTransaction` meets
        any of the classifications in the set.  If it does, the classification
        value of the first passing classification is returned, otherwise, the
        default value is returned.
        """
        for classification in self:
            result = classification(obj)
            if result is not None:
                return result
        return self._default


TRANSACTION_CLASSIFICATIONS = PlaidClassifications([
    PlaidClassification(
        account_type=PlaidAccountType.CREDIT,
        account_subtype=PlaidAccountSubType.CREDIT_CARD,
        classification=ActualType.PLAID_TRANSACTION_TYPES.credit_card
    ),
    PlaidClassification(
        transaction=lambda t: t.is_category_or_subset_of(
            PlaidCategories.CHECK_DEPOSIT,
            PlaidCategories.CHECK_WITHDRAWAL,
            PlaidCategories.CHECK_TRANSFER
        ),
        classification=ActualType.PLAID_TRANSACTION_TYPES.check
    ),
    PlaidClassification(
        transaction=lambda t: t.is_category(PlaidCategories.CREDIT_CARD_PAYMENT),
        classification=ActualType.PLAID_TRANSACTION_TYPES.credit_card
    ),
    PlaidClassification(
        transaction=lambda t: t.payment_method == "ACH",
        classification=ActualType.PLAID_TRANSACTION_TYPES.ach
    ),
    PlaidClassification(
        transaction=lambda t: t.is_category(PlaidCategories.ACH_TRANSFER),
        classification=ActualType.PLAID_TRANSACTION_TYPES.ach
    ),
    PlaidClassification(
        transaction=lambda t: t.is_category(PlaidCategories.WIRE_TRANSFER),
        classification=ActualType.PLAID_TRANSACTION_TYPES.wire
    )
])

TRANSACTION_IGNORE_CLASSIFICATIONS = PlaidClassifications([
    PlaidClassification(
        transaction=lambda t: t.is_category_or_subset_of(
            PlaidCategories.BANK_FEES),
        classification=True
    ),
], default=False)
