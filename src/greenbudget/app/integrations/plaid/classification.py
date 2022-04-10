from greenbudget.lib.utils.abstract import ImmutableSequence
from greenbudget.app.actual.models import ActualType

from .constants import (
    PlaidAccountType, PlaidAccountSubType, PlaidCategoryGroup,
    PlaidHierarchy1, PlaidHierarchy2, PlaidHierarchy3)


class PlaidCategorization:
    def __init__(self, group, hierarchy):
        self.group = group
        self.hierarchy = hierarchy

    @property
    def native(self):
        return self.hierarchy

    def extend(self, hierarchy):
        return self.__class__(self.group, self.hierarchy + list(hierarchy))

    def __eq__(self, other):
        assert isinstance(other, (list, tuple, self.__class__)), \
            "The comparison hierarchy must be an iterable or instance of " \
            f"{self.__class__}."

        if isinstance(other, self.__class__):
            return other.hierarchy == self.hierarchy
        return list(self.hierarchy) == list(other)

    def is_equal_or_parent_of(self, other):
        assert isinstance(other, (list, tuple, self.__class__)), \
            "The comparison hierarchy must be an iterable or instance of " \
            f"{self.__class__}."
        comparison = other
        if isinstance(other, self.__class__):
            comparison = other.hierarchy
        if len(comparison) < len(self.hierarchy):
            return False
        return comparison[:len(self.hierarchy)] == self.hierarchy

    def is_equal_or_subset_of(self, other):
        assert isinstance(other, (list, tuple, self.__class__)), \
            "The comparison hierarchy must be an iterable or instance of " \
            f"{self.__class__}."
        comparison = other
        if isinstance(other, self.__class__):
            comparison = other.hierarchy
        if len(comparison) > len(self.hierarchy):
            return False
        return self.hierarchy == comparison[:len(self.hierarchy)]


class PlaidCategory:
    BANK_FEES = PlaidCategorization(
        group=PlaidCategoryGroup.SPECIAL,
        hierarchy=[PlaidHierarchy1.BANK_FEES]
    )
    INSUFFICIENT_FUNDS_FEES = BANK_FEES.extend(
        [PlaidHierarchy2.INSUFFICIENT_FUNDS])
    ATM_FEES = BANK_FEES.extend([PlaidHierarchy2.ATM])
    LATE_PAYMENT = BANK_FEES.extend([PlaidHierarchy2.LATE_PAYMENT])
    WIRE_TRANSFER_FEES = BANK_FEES.extend([PlaidHierarchy2.WIRE_TRANSFER])
    OVERDRAFT_FEES = BANK_FEES.extend([PlaidHierarchy2.OVERDRAFT])

    PAYMENT = PlaidCategorization(
        group=PlaidCategoryGroup.SPECIAL,
        hierarchy=[PlaidHierarchy1.PAYMENT]
    )
    CREDIT_CARD_PAYMENT = PAYMENT.extend([PlaidHierarchy2.CREDIT_CARD])
    RENT_PAYMENT = PAYMENT.extend([PlaidHierarchy2.RENT])
    LOAN_PAYMENT = PAYMENT.extend([PlaidHierarchy2.LOAN])

    TRANSFER = PlaidCategorization(
        group=PlaidCategoryGroup.SPECIAL,
        hierarchy=[PlaidHierarchy1.TRANSFER]
    )
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
    evaluations = [
        'transaction_check', 'account_check', 'account_type',
        'account_subtype'
    ]

    def __init__(self, classification, **kwargs):
        self._classification = classification
        assert any([x in kwargs for x in self.evaluations]), \
            "At least one evaluation criteria must be provided."

        self._account_check = kwargs.pop('account_check', None)
        self._transaction_check = kwargs.pop('transaction_check', None)
        self._account_type = kwargs.pop('account_type', None)
        self._account_subtype = kwargs.pop('account_subtype', None)

    def __call__(self, obj):
        if any([
            getattr(self, evaluation)(obj) is False
            for evaluation in self.evaluations
        ]):
            return None
        return self._classification

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


class PlaidClassifications(ImmutableSequence):
    def __init__(self, *args, **kwargs):
        self._default = kwargs.pop('default', None)
        super().__init__(*args, **kwargs)

    def classify(self, obj):
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
        transaction_check=lambda t: t.is_category_or_subset_of(
            PlaidCategory.CHECK_DEPOSIT,
            PlaidCategory.CHECK_WITHDRAWAL,
            PlaidCategory.CHECK_TRANSFER
        ),
        classification=ActualType.PLAID_TRANSACTION_TYPES.check
    ),
    PlaidClassification(
        transaction_check=lambda t: t.is_category(
            PlaidCategory.CREDIT_CARD_PAYMENT,
        ),
        classification=ActualType.PLAID_TRANSACTION_TYPES.credit_card
    ),
    PlaidClassification(
        transaction_check=lambda t: t.is_category(PlaidCategory.ACH_TRANSFER),
        classification=ActualType.PLAID_TRANSACTION_TYPES.ach
    ),
    PlaidClassification(
        transaction_check=lambda t: t.is_category(PlaidCategory.WIRE_TRANSFER),
        classification=ActualType.PLAID_TRANSACTION_TYPES.wire
    )
])

TRANSACTION_IGNORE_CLASSIFICATIONS = PlaidClassifications([
    PlaidClassification(
        transaction_check=lambda t: t.is_category_or_subset_of(
            PlaidCategory.BANK_FEES),
        classification=True
    ),
], default=False)
