from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('user', '0008_user_approval'),
    ]

    operations = [
        migrations.AddField(
            model_name='user',
            name='stripe_id',
            field=models.CharField(blank=True, max_length=128, null=True),
        ),
    ]
