from django import dispatch
from django.db.models.signals import post_save

from .models import Tag


@dispatch.receiver(post_save)
def reindex_tags(instance, **kwargs):
    """
    Reindexes the order of each :obj:`Tag` extension in the Polymorphic set.
    """
    if isinstance(instance, Tag) and \
            not getattr(instance, '_ignore_reindex', False):
        all_instances = Tag.objects.filter(
            polymorphic_ctype_id=instance.polymorphic_ctype_id).order_by(
                'order', '-updated_at').all()
        for i, tag in enumerate(all_instances):
            tag.order = i + 1
            tag.save(ignore_reindex=True)
