from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('contact', '0019_contact_notes'),
        ('actual', '0017_django_4'),
    ]

    operations = [
        migrations.AlterField(
            model_name='actual',
            name='contact',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='tagged_actuals', to='contact.contact'),
        ),
    ]
