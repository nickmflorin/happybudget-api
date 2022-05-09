class AssociatedObjectNotFound(KeyError):
    def __init__(self, model_cls, pk):
        self.model_cls = model_cls
        self.pk = pk

    def __str__(self):
        return (
            "Could not find associated %s instance for PK %s."
            % (self.model_cls.__name__, self.pk)
        )
