document.addEventListener('DOMContentLoaded', function () {
    if (document.getElementById('tenant-onboard-form')) {
        return;
    }

    const propertySelect = document.getElementById('id_pg_property');
    const roomSelect = document.getElementById('id_room');

    if (propertySelect && roomSelect) {
        propertySelect.addEventListener('change', function () {
            const propertyId = this.value;
            roomSelect.innerHTML = '<option value="">-- Select a Room --</option>';

            if (propertyId) {
                fetch(`/ajax/load-rooms/?property_id=${encodeURIComponent(propertyId)}`, { stayiLoader: false })
                    .then((response) => response.json())
                    .then((data) => {
                        data.forEach((room) => {
                            const option = document.createElement('option');
                            option.value = room.id;
                            option.textContent = room.name;
                            roomSelect.appendChild(option);
                        });
                    })
                    .catch((error) => console.error('Error fetching rooms:', error));
            }
        });
    }
});
