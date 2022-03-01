from polymorphic.models import PolymorphicManager

from django.db import models, transaction, IntegrityError

from greenbudget.lib.django_utils.models import error_is_unique_constraint
from greenbudget.lib.django_utils.query import PolymorphicQuerySet

from .query import (
    RowQuerySet, RowPolymorphicQuerySet, RowQuerier, OrderedRowQuerier,
    OrderedRowQuerySet, OrderedRowPolymorphicQuerySet)
from .utils import order_after


# The maximum number of times a bulk create should be reattempted in the case
# that the transaction fails due to a unique constraint regarding the `order`
# field.  Due to the careful implementation of nested atomic blocks and row
# locking, this is an edge case - and only occurs if two concurrent requests
# execute at almost exactly the same time.  As such, it should only be
# re-attempted 1 time.
MAX_UNIQUE_CONSTRAINT_RECURSIONS = 1


class RowManagerMixin(RowQuerier):
    def get_queryset(self):
        return self.queryset_class(self.model)


class OrderedRowManagerMixin(OrderedRowQuerier, RowManagerMixin):
    def establish_ordering(self, instances, table, reordering=False):
        """
        Establishes the ordering of new rows not yet created such that they
        are ordered at the bottom of the table subset, in the order that they
        are being created in.

        Before an instance is created, unless it's order is already specified,
        the order must be defaulted such that the instance represents the last
        row in the table subset it belongs to.  We do not, and should not,
        allow the order to be explicitly specified before hand when bulk
        creating.

        The only time that we allow the order to be explicitly provided is when
        when we are inserting a single row into the middle of the table - which
        does not leverage the bulk create endpoint behavior.  As such, we enforce
        that the instances being added do not already specify an order, because
        doing so has the potential of causing database deadlocks or race
        conditions related to unique constraints.

        Parameters:
        ----------
        instances: :obj:`django.db.models.QuerySet`, :obj:`list` or :obj:`tuple`
            The new instances being created.  The instances being created must
            not already have an order defined and must not have already been
            saved.

        table: :obj:`django.db.models.QuerySet`, :obj:`list` or :obj:`tuple`
            The instances belonging to the same table subset that are already
            in the database.  These instances must all have an ordering defined
            and the orderings must be unique.  These instances are used to
            determine what the ordering should start at for the new instances
            being created.
        """
        assert isinstance(table, (models.QuerySet, list, tuple, set))

        # There are cases in the recursion where we will have defined the orders
        # before running into a unique constraint error, and we need to redefine
        # the orders afterwards.
        if not reordering:
            assert not any([
                getattr(obj, 'order') is not None for obj in instances]), \
                "Detected instances with ordering already defined. " \
                "Explicitly ordering instances before a bulk create operation " \
                "is prohibited."

        assert not any([
            getattr(obj, 'pk') is not None for obj in instances]), \
            "Detected instances that are already saved.  Explicitly " \
            "ordering instances during a bulk update operation is prohibited."

        # When determining what order each element should have, we have to
        # look in the database for the latest order of the instances in the
        # table subset.
        last_order = None

        if isinstance(table, models.QuerySet):
            try:
                last_in_table = table.latest()
            except self.model.DoesNotExist:
                pass
            else:
                last_order = last_in_table.order

        elif len(table) != 0:
            # These assertions are guaranteed via database constraints in the
            # case that the table is an instance of
            # :obj:`django.db.models.QuerySet`.
            assert not any([obj.order is None for obj in table]), \
                "Detected rows in the current table without an ordering " \
                "defined."
            assert len(set([obj.order for obj in table])) == len(table), \
                "Detected rows in the current table with duplicate ordering " \
                "defined."
            last_order = max([obj.order for obj in table])

        # Order the instances that do not have a defined order in the order
        # that they are being created in.
        ordering = order_after(len(instances), last_order=last_order)
        for i, instance in enumerate(instances):
            instance.order = ordering[i]

    @transaction.atomic()
    def _bulk_create_table_key(self, instances, attempt=0, **kwargs):
        """
        Performs the bulk create operation for instances that belong to the
        same table subset, identified by the table key.  The method is meant
        to be recursive, such that in the case of unique constraint integrity
        errors around the `order` field (which will be an edge case because of
        the row locks) the bulk create can be reperformed a second time with an
        updated set of instances and orders from the database.

        Note:
        ----
        When we try to catch an instance of :obj:`django.db.DatabaseError`
        (which is the base class for :obj:`django.db.IntegrityError`) we have
        to wrap the inner part of the try in it's own atomic transaction block,
        otherwise we will get a :obj:`django.db.TransactionManagementError`.

        This is because we have to reperform the database query for the instances
        in the table subset after the failed transaction.  when exiting an
        atomic block, Django looks at whether its exited normally or with an
        exception to determine whether to commit or roll back the transaction
        within the block. If you catch and handle exceptions inside an atomic
        block, you may hide from Django the fact that a problem has happened.
        This can result in unexpected behavior.

        This is mostly a concern for DatabaseError and its subclasses such as
        IntegrityError. After such an error, the transaction is broken and
        Django will perform a rollback at the end of the atomic block. If you
        attempt to run database queries before the rollback happens, Django will
        raise a TransactionManagementError. The solution is to wrap the inner
        part of the try in it's own atomic transaction.

        See https://docs.djangoproject.com/en/4.0/topics/db/transactions/
            #controlling-transactions-explicitly
        """
        return_created_objects = kwargs.pop('return_created_objects', True)

        tks = set([obj.table_key for obj in instances])
        assert len(tks) == 1, \
            "Detected instances that belong to multiple different table " \
            "subsets when the method only supports a single table subset."

        tk = list(tks)[0]

        # Fetch the current table subset from the database so the ordering of
        # the new rows can be determined.  Lock the rows such that other
        # concurrent requests do not use stale data to determine the row ordering
        # of other new rows.
        current_table = self.get_table(tk).select_for_update()

        # Establish the ordering of the new rows being created.
        self.establish_ordering(
            instances, current_table, reordering=attempt > 0)

        try:
            # See note in docstring about additional atomic transaction block.
            with transaction.atomic():
                # For the Polymorphic case, we need to include the argument
                # to return the created objects.  In the non-polymorphic case,
                # it is the default behavior by Django.
                if issubclass(self.queryset_class, PolymorphicQuerySet):
                    kwargs['return_created_objects'] = return_created_objects
                return super().bulk_create(instances, **kwargs)
        except IntegrityError as e:
            # This is an edge case.  The usage of row locking and nested atomic
            # transaction blocks prevent this the majority of the time, but it
            # can still happen due to race conditions when concurrent requests
            # to bulk create instances execute at nearly identical times because
            # of the timing around the row locking.  When it occurs, we simply
            # reperform the bulk create with a fresh query of the table subset
            # and orders from the database.
            if error_is_unique_constraint(e, "order") \
                    and attempt < MAX_UNIQUE_CONSTRAINT_RECURSIONS:
                return self._bulk_create_table_key(
                    instances, attempt=attempt + 1, **kwargs)
            else:
                raise

    def bulk_create(self, instances, **kwargs):
        """
        Extends traditional bulk create behavior by first establishing the order
        for each instance being bulk created based on the order of the instances
        already persisted to the DB.

        Since we are reading from the instances already in the DB, and making
        the determination of order for new instances being created based on the
        instances already in the DB, we have to carefully incorporate row locking
        and atomic transaction blocks such that we do not introduce unique
        constraint errors around the `order` field in the presence of multiple
        concurrent requests. Furthermore, we have to perform the bulk creation
        one table at a time.
        """
        return_created_objects = kwargs.get('return_created_objects', True)

        # The unique set of table keys that identify which table subset each
        # instance being created belongs to.
        tks = set([obj.table_key for obj in instances])

        # Since we are going to create the instances for each table subset in
        # batches, we need to add an attirbute to denote the original order the
        # instances were provided in, such that they can be returned in the
        # same order.
        for i, obj in enumerate(instances):
            setattr(obj, '__provided_order__', i)

        def table_key_sorter(tk):
            """
            Sort the table keys by the earliest provided instance in the
            table subset identified by that key.  This helps keep the order
            of creation, and thus PKs, of the created objects relatively
            consistent in some cases:

            >>> instances = [
            >>>     Object (Table = A),
            >>>     Object (Table = B),
            >>>     Object (Table = B)
            >>> ]
            >>> created = bulk_create(instances)
            >>> [obj.pk for obj in created]
            >>> [1, 2, 3]

            However, it begins to fall apart if the order of the table subsets
            for each instance in the provided instances begins to fall out of
            order:

            >>> instances = [
            >>>     Object (Table = A),
            >>>     Object (Table = B),
            >>>     Object (Table = A),
            >>>     Object (Table = B)
            >>> ]
            >>> created = bulk_create(instances)
            >>> [obj.pk for obj in created]
            >>> [1, 3, 2, 4]
            """
            objs = [obj for obj in instances if obj.table_key == tk]
            assert len(objs) != 0, \
                "Unexpectedly encountered table-key outside the scope of the " \
                "provided instances."
            return min([getattr(obj, '__provided_order__') for obj in objs])

        # Wrap in an atomic transaction block because if adding rows to any of
        # the individual tables fails, we don't want to add rows to any of the
        # tables.
        created = []
        with transaction.atomic():
            for tk in sorted(tks, key=table_key_sorter):
                new_rows = [i for i in instances if i.table_key == tk]
                table_created = self._bulk_create_table_key(new_rows, **kwargs)
                if return_created_objects:
                    # Associated the new created instances with the order the
                    # unsaved instance was provided in.
                    for i, obj in enumerate(table_created):
                        setattr(obj, '__provided_order__',
                            new_rows[i].__provided_order__)
                    created += table_created

        if return_created_objects:
            return sorted(created, key=lambda obj: getattr(
                obj, '__provided_order__'))
        return None


class RowManager(RowManagerMixin, models.Manager):
    queryset_class = RowQuerySet


class OrderedRowManager(OrderedRowManagerMixin, models.Manager):
    queryset_class = OrderedRowQuerySet


class RowPolymorphicManager(RowManagerMixin, PolymorphicManager):
    queryset_class = RowPolymorphicQuerySet


class OrderedRowPolymorphicManager(OrderedRowManagerMixin, PolymorphicManager):
    queryset_class = OrderedRowPolymorphicQuerySet
