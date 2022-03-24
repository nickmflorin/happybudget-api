from greenbudget.lib.utils import humanize_list


class InvalidAction(ValueError):
    def __init__(self, provided):
        self._provided = provided

    def __str__(self):
        valid = humanize_list(ActionName.__all__, conjunction="or")
        return f"Invalid action {self._provided}.  Must be one of {valid}."


class ActionName:
    CREATE = "create"
    DELETE = "delete"
    UPDATE = "update"
    __all__ = (CREATE, DELETE, UPDATE)
    Invalid = InvalidAction

    @classmethod
    def validate(cls, value):
        if value not in cls.__all__:
            raise InvalidAction(value)
