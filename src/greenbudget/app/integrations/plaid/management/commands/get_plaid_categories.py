import csv

from django.core import management

from happybudget.management import CustomCommand, debug_only
from happybudget.app.integrations.plaid.api import client


@debug_only
class Command(CustomCommand):
    def add_arguments(self, parser):
        parser.add_argument('-p')

    def download(self, categories, path):
        csv_data = [
            ['ID', 'Group', 'Hierarchy 1', 'Hierarchy 2', 'Hierarchy 3']]
        for category in categories:
            csv_row = [category.category_id, category.group]
            for i in range(3):
                try:
                    csv_row.append(category.hierarchy[i])
                except IndexError:
                    csv_row.append("")
            csv_data.append(csv_row)
        with open(path, 'w', newline='') as csvfile:
            writer = csv.writer(csvfile, delimiter=',')
            writer.writerows(csv_data)

    @management.base.no_translations
    def handle(self, *args, **options):
        response = client.categories_get({})
        if options['p'] is not None:
            self.download(response.categories, options['p'])
        else:
            self.stdout.write(response.categories)
