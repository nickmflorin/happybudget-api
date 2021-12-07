from django.db import migrations, models
import greenbudget.app.user.managers


class Migration(migrations.Migration):

    dependencies = [
        ('user', '0007_date_joined_auto_now_add'),
    ]

    operations = [
        migrations.CreateModel(
            name='UnapprovedUser',
            fields=[
            ],
            options={
                'verbose_name': 'Unapproved User',
                'verbose_name_plural': 'Unapproved Users',
                'proxy': True,
                'indexes': [],
                'constraints': [],
            },
            bases=('user.user',),
            managers=[
                ('objects', greenbudget.app.user.managers.UnapprovedUserManager()),
            ],
        ),
        migrations.AddField(
            model_name='user',
            name='is_approved',
            field=models.BooleanField(default=True, help_text='Designates whether this user has been approved for access.', verbose_name='approved'),
        ),
    ]
