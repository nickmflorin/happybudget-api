from django.core import management

from greenbudget.management import CustomCommand

from greenbudget.app.subaccount.models import SubAccount
from greenbudget.app.subaccount.signals import calculate_subaccount


class Command(CustomCommand):

    @management.base.no_translations
    def handle(self, *args, **options):
        for i, subaccount in enumerate(SubAccount.objects.all()):
            print(
                "Recalculating SubAccount (%s/%s) (id = %s)"
                % (i + 1, SubAccount.objects.count(), subaccount.pk)
            )
            calculate_subaccount(subaccount)

        self.success(
            "Successfully recalculated %s subaccounts."
            % SubAccount.objects.count()
        )
