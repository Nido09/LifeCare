from django.db import migrations, models

class Migration(migrations.Migration):
    dependencies = [
        ('notifications', '0001_initial'),  # Use your latest migration name
    ]

    operations = [
        # The title column already exists in the database
        # We just need to make Django aware of it
        migrations.AddField(
            model_name='notification',
            name='title',
            field=models.CharField(max_length=200, default=''),
            preserve_default=False,
        ),
    ]