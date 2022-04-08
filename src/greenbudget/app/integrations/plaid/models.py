class PlaidTransaction:
    def __init__(self, user, *args, **kwargs):
        data = dict(*args, **kwargs)
        self._user = user
        self._id = data['transaction_id']
        self._datetime = data['datetime']
        self._date = data['date']
        self._categories = data['category']
        self._name = data['name']
        self._merchant_name = data['merchant_name']
        self._amount = data['amount']
        self._iso_currency_code = data['iso_currency_code']

    @property
    def id(self):
        return self._id

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

    @classmethod
    def from_data(cls, user, *args, **kwargs):
        return cls(user, *args, **kwargs)
