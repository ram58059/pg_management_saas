from django.db import transaction

from apps.accounts.models import CustomUser
from apps.properties.models import Property, Room
from apps.tenants.forms import TenantProfileForm, TenantUserForm
from apps.tenants.models import TenantDocument
from apps.tenants.services.room_options import get_available_rooms_queryset


def setup_tenant_onboarding_forms(owner=None, post_data=None, files=None):
    if post_data is not None:
        user_form = TenantUserForm(post_data)
        profile_form = TenantProfileForm(post_data, files)
    else:
        user_form = TenantUserForm()
        profile_form = TenantProfileForm()

    if owner:
        properties = Property.objects.filter(owner=owner)
    else:
        properties = Property.objects.all().order_by('name')

    profile_form.fields['pg_property'].queryset = properties

    property_id = post_data.get('pg_property') if post_data else None
    profile_form.fields['room'].queryset = get_available_rooms_queryset(property_id)
    return user_form, profile_form


def create_tenant_from_forms(user_form, profile_form):
    with transaction.atomic():
        user = user_form.save(commit=False)
        password = user_form.cleaned_data['password']
        user.set_password(password)
        user.role = CustomUser.Role.TENANT
        user.save()

        tenant = profile_form.save(commit=False)
        tenant.user = user
        tenant.save()

        id_proof_file = profile_form.cleaned_data.get('id_proof_file')
        if id_proof_file:
            TenantDocument.objects.create(
                tenant=tenant,
                document_type=tenant.id_proof_type or 'ID_PROOF',
                file=id_proof_file,
            )

    return user, tenant, password
