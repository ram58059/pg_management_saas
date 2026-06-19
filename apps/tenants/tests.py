from datetime import date
from decimal import Decimal

from django.test import TestCase, Client
from django.urls import reverse

from apps.accounts.models import CustomUser, PGOwner
from apps.properties.models import Property, Room
from apps.tenants.models import Tenant, TenantDue
from apps.tenants.services.rent_dues import (
    ensure_monthly_rent_due,
    ensure_monthly_rent_dues,
    sync_standard_due_dates,
)
from apps.tenants.services.tenant_creation import create_tenant_from_forms, setup_tenant_onboarding_forms
from utils.billing import monthly_due_date


class TenantCreationServiceTests(TestCase):
    def setUp(self):
        owner_user = CustomUser.objects.create_user(
            username='owner',
            password='owner123',
            email='owner@example.com',
            role='OWNER',
        )
        owner = PGOwner.objects.create(user=owner_user, company_name='Stayi PG')
        self.property = Property.objects.create(
            owner=owner,
            name='Thoraipakkam',
            address='Chennai',
            pg_type='FEMALE',
        )
        self.room = Room.objects.create(
            pg_property=self.property,
            room_number='1',
            capacity=2,
            base_rent=Decimal('6500.00'),
        )

    def _valid_form_data(self):
        return {
            'first_name': 'Riya',
            'last_name': 'Sharma',
            'username': 'riya_tenant',
            'email': 'riya@example.com',
            'phone_number': '9876543210',
            'password': 'riya@1',
            'pg_property': str(self.property.id),
            'room': str(self.room.id),
            'emergency_contact_name': 'Parent',
            'emergency_contact_number': '9123456789',
            'id_proof_type': 'AADHAAR',
            'id_proof_number': '123456789012',
            'date_of_joining': '2026-05-25',
            'deposit_amount': '3000.00',
        }

    def test_create_tenant_from_forms(self):
        user_form, profile_form = setup_tenant_onboarding_forms(post_data=self._valid_form_data())
        self.assertTrue(user_form.is_valid(), user_form.errors)
        self.assertTrue(profile_form.is_valid(), profile_form.errors)

        user, tenant, password = create_tenant_from_forms(user_form, profile_form)

        self.assertEqual(user.username, 'riya_tenant')
        self.assertEqual(password, 'riya@1')
        self.assertTrue(user.check_password('riya@1'))
        self.assertEqual(tenant.room, self.room)
        self.assertEqual(Tenant.objects.count(), 1)


class PublicTenantOnboardTests(TestCase):
    def setUp(self):
        owner_user = CustomUser.objects.create_user(
            username='owner',
            password='owner123',
            email='owner@example.com',
            role='OWNER',
        )
        owner = PGOwner.objects.create(user=owner_user, company_name='Stayi PG')
        self.property = Property.objects.create(
            owner=owner,
            name='Thoraipakkam',
            address='Chennai',
            pg_type='FEMALE',
        )
        self.room = Room.objects.create(
            pg_property=self.property,
            room_number='1',
            capacity=2,
            base_rent=Decimal('6500.00'),
        )
        self.client = Client()

    def _valid_form_data(self):
        return {
            'first_name': 'Riya',
            'last_name': 'Sharma',
            'username': 'riya_public',
            'email': 'riya@example.com',
            'phone_number': '9876543210',
            'password': 'riya@1',
            'pg_property': str(self.property.id),
            'room': str(self.room.id),
            'emergency_contact_name': 'Parent',
            'emergency_contact_number': '9123456789',
            'id_proof_type': 'AADHAAR',
            'id_proof_number': '123456789012',
            'date_of_joining': '2026-05-25',
            'deposit_amount': '3000.00',
        }

    def test_public_onboard_creates_tenant_and_shows_success_modal(self):
        response = self.client.post(reverse('tenant_onboarding'), self._valid_form_data())
        self.assertEqual(response.status_code, 200)
        self.assertEqual(Tenant.objects.count(), 1)
        self.assertContains(response, 'Tenant Created Successfully')
        self.assertContains(response, 'riya_public')
        self.assertContains(response, 'riya@1')
        self.assertContains(response, 'tenant-success-modal')
        self.assertContains(response, 'Copy All Credentials')

    def test_onboarding_page_is_accessible(self):
        response = self.client.get(reverse('tenant_onboarding'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Onboard as a new tenant')
        self.assertContains(response, 'tenant-onboard-form')

    def test_landing_has_no_onboarding_form(self):
        response = self.client.get(reverse('landing'))
        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, 'tenant-onboard-form')

    def test_landing_has_no_owner_login(self):
        response = self.client.get(reverse('landing'))
        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, 'Owner Login')
        self.assertNotContains(response, 'Owner Portal')
        self.assertContains(response, 'Onboard Tenant')
        self.assertContains(response, 'Tenant Login')

    def test_owner_portal_entry_redirects_to_login(self):
        response = self.client.get(reverse('owner_portal'))
        self.assertRedirects(response, reverse('owner_login'))

    def test_load_rooms_is_public(self):
        response = self.client.get(
            reverse('ajax_load_rooms'),
            {'property_id': self.property.id},
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.json()), 1)


class MonthlyRentDueTests(TestCase):
    def setUp(self):
        owner_user = CustomUser.objects.create_user(
            username='owner_rent',
            password='owner123',
            email='owner-rent@example.com',
            role='OWNER',
        )
        owner = PGOwner.objects.create(user=owner_user, company_name='Test PG')
        self.property = Property.objects.create(
            owner=owner,
            name='Test Property',
            address='Test Address',
            pg_type='MALE',
        )
        self.room = Room.objects.create(
            pg_property=self.property,
            room_number='101',
            capacity=2,
            base_rent=Decimal('8000.00'),
        )
        tenant_user = CustomUser.objects.create_user(
            username='tenant1',
            password='tenant123',
            email='tenant1@example.com',
            role='TENANT',
            first_name='Test',
            last_name='Tenant',
        )
        self.tenant = Tenant.objects.create(
            user=tenant_user,
            pg_property=self.property,
            room=self.room,
            emergency_contact_name='Contact',
            emergency_contact_number='9999999999',
            id_proof_type='AADHAAR',
            id_proof_number='123456789012',
            date_of_joining=date(2025, 1, 1),
            deposit_amount=Decimal('10000.00'),
            is_active=True,
        )
        self.billing_date = date(2026, 6, 1)

    def test_creates_rent_due_with_seventh_due_date(self):
        due = ensure_monthly_rent_due(self.tenant, billing_date=self.billing_date)

        self.assertIsNotNone(due)
        self.assertEqual(due.amount, Decimal('8000.00'))
        self.assertEqual(due.reason, 'RENT')
        self.assertEqual(due.due_date, monthly_due_date(self.billing_date))
        self.assertEqual(due.status, 'PENDING')
        self.assertEqual(due.description, 'Rent for June 2026')

    def test_corrects_existing_rent_due_date_to_seventh(self):
        due = TenantDue.objects.create(
            tenant=self.tenant,
            amount=Decimal('6500.00'),
            reason='RENT',
            description='Rent for June 2026',
            due_date=date(2026, 6, 1),
            status='PENDING',
        )

        ensure_monthly_rent_due(self.tenant, billing_date=self.billing_date)
        due.refresh_from_db()

        self.assertEqual(due.due_date, date(2026, 6, 7))

    def test_sync_standard_due_dates_fixes_electricity_due(self):
        due = TenantDue.objects.create(
            tenant=self.tenant,
            amount=Decimal('250.00'),
            reason='ELECTRICITY',
            description='EB for June 2026',
            due_date=date(2026, 6, 1),
            status='PENDING',
        )

        sync_standard_due_dates(self.tenant)
        due.refresh_from_db()

        self.assertEqual(due.due_date, date(2026, 6, 7))
