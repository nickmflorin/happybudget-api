from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('user', '0009_user_stripe_id'),
    ]

    operations = [
        migrations.DeleteModel(
            name='UnapprovedUser',
        ),
        migrations.RemoveField(
            model_name='user',
            name='is_approved',
        ),
    ]
