from apps.properties.models import Room


def get_available_rooms_for_property(property_id):
    if not property_id:
        return []

    rooms = Room.objects.filter(
        pg_property_id=property_id,
        is_active=True,
    ).order_by('room_number')

    return [
        {
            'id': room.id,
            'name': f"Room {room.room_number} ({room.available_beds} beds left)",
        }
        for room in rooms
        if room.available_beds > 0
    ]


def get_available_rooms_queryset(property_id):
    available_ids = [
        room['id'] for room in get_available_rooms_for_property(property_id)
    ]
    if not available_ids:
        return Room.objects.none()
    return Room.objects.filter(id__in=available_ids).order_by('room_number')
