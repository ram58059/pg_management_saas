import os
import django
import random
from decimal import Decimal
from datetime import date, timedelta

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from apps.accounts.models import CustomUser, PGOwner
from apps.properties.models import Property, Room
from apps.tenants.models import Tenant
from apps.payments.models import PropertyPaymentSettings

def get_base_rent(capacity, is_ac):
    pricing = {
        (4, False): 6500, (4, True): 7500,
        (3, False): 7000, (3, True): 8000,
        (2, False): 8000, (2, True): 10000,
        (1, False): 10000, (1, True): 12000,
        (5, False): 6000, (5, True): 7000,
        (6, False): 5500, (6, True): 6500
    }
    return pricing.get((capacity, is_ac), 6500)

def seed():
    print("Clearing DB...")
    CustomUser.objects.all().delete()
    
    # Create Admin
    CustomUser.objects.create_superuser('admin', 'admin@example.com', 'admin123')
    
    # Create Owner
    owner_user = CustomUser.objects.create_user(
        username='owner1', password='owner123', email='owner@example.com',
        first_name='Admin', last_name='Owner', role='OWNER'
    )
    owner = PGOwner.objects.create(user=owner_user, company_name='Real PG Management')
    
    properties_config = [
        {"name": "Thoraipakkam", "type": "FEMALE", "rooms": [
            (4, 1), (3, 2), (2, 2), (5, 2), (6, 1)
        ]},
        {"name": "Padur near Chettinad College", "type": "FEMALE", "rooms": [
            (4, 20), (2, 1)
        ]},
        {"name": "Padur Chettinad Main Road", "type": "FEMALE", "rooms": [
            (2, 11)
        ]},
        {"name": "Padur Ganga Sweets Boys PG", "type": "MALE", "rooms": [
            (3, 10)
        ]},
        {"name": "Padur near Ganga Sweets Boys PG", "type": "MALE", "rooms": [
            (3, 10)
        ]},
        {"name": "Padur near Ganga Sweets Girls PG", "type": "FEMALE", "rooms": [
            (3, 15)
        ]},
    ]
    
    print("Creating Properties and Rooms...")
    created_properties = []
    
    for idx, pc in enumerate(properties_config):
        p = Property.objects.create(
            owner=owner, 
            name=pc["name"], 
            pg_type=pc["type"], 
            address=f"{pc['name']} Area, Chennai"
        )
        created_properties.append(p)
        
        PropertyPaymentSettings.objects.create(
            pg_property=p,
            upi_id='owner@upi',
            account_holder_name='Admin Owner'
        )
        
        print(f"  - Created Property: {p.name}")
        
        room_counter = 101
        for capacity, count in pc["rooms"]:
            for _ in range(count):
                is_ac = random.choice([True, False])
                base_rent = get_base_rent(capacity, is_ac)
                
                r = Room.objects.create(
                    pg_property=p,
                    room_number=str(room_counter),
                    capacity=capacity,
                    is_ac=is_ac,
                    base_rent=base_rent
                )
                room_counter += 1
                
                # Assign some tenants (approx 70% occupancy)
                occupants = random.randint(0, capacity)
                for _ in range(occupants):
                    tu = CustomUser.objects.create_user(
                        username=f'tenant_{p.id}_{r.id}_{random.randint(1000, 9999)}',
                        password='tenant123',
                        first_name=f'Tenant',
                        last_name=f'{(r.room_number)}',
                        role='TENANT'
                    )
                    Tenant.objects.create(
                        user=tu,
                        pg_property=p,
                        room=r,
                        emergency_contact_name='Parent',
                        emergency_contact_number='9876543210',
                        id_proof_type='AADHAAR',
                        id_proof_number=str(random.randint(100000000000, 999999999999)),
                        date_of_joining=date.today() - timedelta(days=random.randint(1, 300)),
                        deposit_amount=3000
                    )

    # Specific test tenant
    p1 = created_properties[0]
    r1 = p1.rooms.first()
    tt = CustomUser.objects.create_user('tenant1', 'tenant1@example.com', 'tenant123', first_name='Riya', last_name='Singh', role='TENANT')
    Tenant.objects.create(
        user=tt, pg_property=p1, room=r1, emergency_contact_name='Father', emergency_contact_number='9876543210',
        id_proof_type='AADHAAR', id_proof_number='123456789012', date_of_joining=date.today(), deposit_amount=3000
    )
    
    print("Done! Login with owner1/owner123 or tenant1/tenant123.")

if __name__ == '__main__':
    seed()
