from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('concepts', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='conceptcandidatemodel',
            name='risks',
            field=models.JSONField(default=list),
        ),
    ]
