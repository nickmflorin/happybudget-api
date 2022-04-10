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


class PlaidCategoryGroup:
    SPECIAL = 'special'
    PLACE = 'place'


class PlaidHierarchy1:
    """
    The first hierarchy level of a Plaid category.  This will be the first
    element in the array of categories attached to a transaction.  This list
    is not exhaustive, but only includes the values we are concerned with.
    """
    PAYMENT = 'Payment'
    TRANSFER = 'Transfer'
    BANK_FEES = 'Bank Fees'


class PlaidHierarchy2:
    """
    The second hierarchy level of a Plaid category.  This will be the second
    element in the array of categories attached to a transaction.  This list
    is not exhaustive, but only includes the values we are concerned with.
    """
    CREDIT_CARD = 'Credit Card'
    ACH = 'ACH'
    CREDIT = 'Credit'
    DEBIT = 'Debit'
    DEPOSIT = 'Deposit'
    CHECK = 'Check'
    WIRE = 'Wire'
    WITHDRAWAL = 'Withdrawal'
    RENT = 'Rent'
    LOAN = 'Loan'
    INSUFFICIENT_FUNDS = 'Insufficient Funds'
    WIRE_TRANSFER = 'Wire Transfer'
    LATE_PAYMENT = 'Late Payment'
    ATM = 'ATM'
    OVERDRAFT = 'Overdraft'


class PlaidHierarchy3:
    """
    The third hierarchy level of a Plaid category.  This will be the last
    element in the array of categories attached to a transaction.  This list
    is not exhaustive, but only includes the values we are concerned with.
    """
    CHECK = 'Check'
    ATM = 'ATM'
