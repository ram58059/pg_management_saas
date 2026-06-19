function loadRoomsForProperty(propertySelect, roomSelect, loadRoomsUrl, selectedRoomId) {
    if (!propertySelect || !roomSelect || !loadRoomsUrl) {
        return;
    }

    const propertyId = propertySelect.value;
    roomSelect.innerHTML = '<option value="">---------</option>';
    roomSelect.disabled = true;

    if (!propertyId) {
        roomSelect.disabled = false;
        return;
    }

    const loadingOption = document.createElement('option');
    loadingOption.value = '';
    loadingOption.textContent = 'Loading rooms...';
    roomSelect.innerHTML = '';
    roomSelect.appendChild(loadingOption);

    fetch(`${loadRoomsUrl}?property_id=${encodeURIComponent(propertyId)}`, { stayiLoader: false })
        .then((response) => {
            if (!response.ok) {
                throw new Error(`Failed to load rooms (${response.status})`);
            }
            return response.json();
        })
        .then((data) => {
            roomSelect.innerHTML = '<option value="">---------</option>';

            if (!Array.isArray(data) || data.length === 0) {
                const emptyOption = document.createElement('option');
                emptyOption.value = '';
                emptyOption.textContent = 'No rooms available';
                roomSelect.appendChild(emptyOption);
                roomSelect.disabled = false;
                return;
            }

            data.forEach((room) => {
                const option = document.createElement('option');
                option.value = room.id;
                option.textContent = room.name;
                if (selectedRoomId && String(room.id) === String(selectedRoomId)) {
                    option.selected = true;
                }
                roomSelect.appendChild(option);
            });
            roomSelect.disabled = false;
        })
        .catch((error) => {
            console.error('Error loading rooms:', error);
            roomSelect.innerHTML = '<option value="">Unable to load rooms</option>';
            roomSelect.disabled = false;
        });
}

async function copyTextToClipboard(text) {
    if (navigator.clipboard && window.isSecureContext) {
        await navigator.clipboard.writeText(text);
        return;
    }

    const textarea = document.createElement('textarea');
    textarea.value = text;
    textarea.setAttribute('readonly', '');
    textarea.style.position = 'absolute';
    textarea.style.left = '-9999px';
    document.body.appendChild(textarea);
    textarea.select();
    document.execCommand('copy');
    document.body.removeChild(textarea);
}

function showCopyFeedback(message) {
    const feedback = document.getElementById('copy-feedback');
    if (!feedback) {
        return;
    }
    feedback.textContent = message;
    feedback.classList.remove('hidden');
    window.setTimeout(() => {
        feedback.classList.add('hidden');
    }, 2200);
}

function initTenantSuccessModal() {
    const modal = document.getElementById('tenant-success-modal');
    if (!modal) {
        return;
    }

    if (modal.parentElement !== document.body) {
        document.body.appendChild(modal);
    }

    const username = modal.dataset.username || '';
    const password = modal.dataset.password || '';
    const closeButton = document.getElementById('close-success-modal-btn');
    const backdrop = document.getElementById('tenant-success-modal-backdrop');
    const copyUsernameBtn = document.getElementById('copy-username-btn');
    const copyPasswordBtn = document.getElementById('copy-password-btn');
    const copyAllBtn = document.getElementById('copy-all-credentials-btn');
    let credentialsCleared = false;

    function clearSensitiveCredentials() {
        if (credentialsCleared) {
            return;
        }
        credentialsCleared = true;
        modal.dataset.username = '';
        modal.dataset.password = '';
        const usernameEl = document.getElementById('tenant-success-username');
        const passwordEl = document.getElementById('tenant-success-password');
        if (usernameEl) {
            usernameEl.textContent = '********';
        }
        if (passwordEl) {
            passwordEl.textContent = '********';
        }
    }

    function closeModal() {
        clearSensitiveCredentials();
        modal.classList.add('hidden');
        document.body.classList.remove('overflow-hidden');
    }

    modal.classList.remove('hidden');
    document.body.classList.add('overflow-hidden');

    if (window.history.replaceState) {
        window.history.replaceState(null, '', window.location.pathname);
    }

    closeButton?.addEventListener('click', closeModal);
    backdrop?.addEventListener('click', closeModal);

    document.addEventListener('keydown', function handleEscape(event) {
        if (event.key === 'Escape' && !modal.classList.contains('hidden')) {
            closeModal();
            document.removeEventListener('keydown', handleEscape);
        }
    });

    copyUsernameBtn?.addEventListener('click', async function () {
        try {
            await copyTextToClipboard(username);
            showCopyFeedback('Username copied to clipboard.');
        } catch (error) {
            showCopyFeedback('Unable to copy username.');
        }
    });

    copyPasswordBtn?.addEventListener('click', async function () {
        try {
            await copyTextToClipboard(password);
            showCopyFeedback('Password copied to clipboard.');
        } catch (error) {
            showCopyFeedback('Unable to copy password.');
        }
    });

    copyAllBtn?.addEventListener('click', async function () {
        const allCredentials = `Username: ${username}\nPassword: ${password}`;
        try {
            await copyTextToClipboard(allCredentials);
            showCopyFeedback('All credentials copied to clipboard.');
        } catch (error) {
            showCopyFeedback('Unable to copy credentials.');
        }
    });

    closeButton?.focus();
}

document.addEventListener('DOMContentLoaded', function () {
    const form = document.getElementById('tenant-onboard-form');
    const propertySelect = document.getElementById('id_pg_property');
    const roomSelect = document.getElementById('id_room');
    const generateBtn = document.getElementById('generate-password-btn');
    const passwordInput = document.getElementById('id_password');
    const firstNameInput = document.getElementById('id_first_name');
    const submitButton = document.getElementById('tenant-onboard-submit');
    const submitText = document.getElementById('tenant-onboard-submit-text');
    const spinner = document.getElementById('tenant-onboard-spinner');
    const loadRoomsUrl = form?.dataset.loadRoomsUrl || '/ajax/load-rooms/';
    const initialRoomId = roomSelect?.value || '';
    let isSubmitting = false;

    if (propertySelect && roomSelect) {
        propertySelect.addEventListener('change', function () {
            loadRoomsForProperty(propertySelect, roomSelect, loadRoomsUrl);
        });

        if (propertySelect.value) {
            loadRoomsForProperty(propertySelect, roomSelect, loadRoomsUrl, initialRoomId);
        }
    }

    if (generateBtn && passwordInput) {
        generateBtn.addEventListener('click', function () {
            const firstName = firstNameInput ? firstNameInput.value.trim().toLowerCase() : '';
            let password = '';

            if (firstName) {
                const selectedRoom =
                    roomSelect && roomSelect.options[roomSelect.selectedIndex]
                        ? roomSelect.options[roomSelect.selectedIndex].text
                        : '';
                const roomNumber = selectedRoom.replace(/[^0-9]/g, '');
                password = roomNumber ? `${firstName}@${roomNumber}` : `${firstName}@123`;
            } else {
                password = `tenant@${Math.floor(1000 + Math.random() * 9000)}`;
            }

            passwordInput.value = password;
            passwordInput.type = 'text';

            const originalText = generateBtn.textContent;
            generateBtn.textContent = 'Generated!';
            window.setTimeout(() => {
                generateBtn.textContent = originalText;
            }, 1500);
        });
    }

    const photoInput = document.getElementById('id_profile_photo');
    if (photoInput) {
        photoInput.addEventListener('change', function (event) {
            const file = event.target.files[0];
            const preview = document.getElementById('photo-preview');
            const placeholder = document.getElementById('photo-placeholder');

            if (file && preview && placeholder) {
                const reader = new FileReader();
                reader.onload = function (loadEvent) {
                    preview.src = loadEvent.target.result;
                    preview.classList.remove('hidden');
                    placeholder.classList.add('hidden');
                };
                reader.readAsDataURL(file);
            } else if (preview && placeholder) {
                preview.classList.add('hidden');
                placeholder.classList.remove('hidden');
            }
        });
    }

    if (form && submitButton) {
        form.addEventListener('submit', function (event) {
            if (isSubmitting) {
                event.preventDefault();
                return;
            }
            isSubmitting = true;
        });
    }

    initTenantSuccessModal();
});
