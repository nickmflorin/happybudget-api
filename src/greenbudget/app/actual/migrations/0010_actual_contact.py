from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('contact', '0009_contact_image'),
        ('actual', '0009_updated_by_non_null'),
    ]

    operations = [
        migrations.AddField(
            model_name='actual',
            name='contact',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='assigned_actuals', to='contact.contact'),
        ),
    ]
