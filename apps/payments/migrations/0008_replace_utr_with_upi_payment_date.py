from django.db import migrations, models


def set_upi_payment_date_from_uploaded_at(apps, schema_editor):
    PaymentProof = apps.get_model('payments', 'PaymentProof')
    for proof in PaymentProof.objects.all().iterator():
        if proof.uploaded_at:
            proof.upi_payment_date = proof.uploaded_at.date()
            proof.save(update_fields=['upi_payment_date'])


class Migration(migrations.Migration):

    dependencies = [
        ('payments', '0007_alter_generatedinvoice_pdf_file_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='paymentproof',
            name='upi_payment_date',
            field=models.DateField(blank=True, help_text='Date when the UPI payment was completed', null=True),
        ),
        migrations.RunPython(set_upi_payment_date_from_uploaded_at, migrations.RunPython.noop),
        migrations.RemoveField(
            model_name='paymentproof',
            name='utr_number',
        ),
        migrations.AlterField(
            model_name='paymentproof',
            name='upi_payment_date',
            field=models.DateField(help_text='Date when the UPI payment was completed'),
        ),
    ]
