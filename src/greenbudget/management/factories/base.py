from factory.django import DjangoModelFactory


class CustomModelFactory(DjangoModelFactory):
    @classmethod
    def create(cls, *args, **kwargs):
        created = super(CustomModelFactory, cls).create(*args, **kwargs)
        return cls.post_create(created, **kwargs)

    @classmethod
    def post_create(cls, model, **kwargs):
        return model
