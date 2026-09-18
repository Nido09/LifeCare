// Registration page: live age calculation from DOB, and DOB max=today.
// (State/District/City cascade and multi-country phone logic have been
// removed — registration is now Mumbai-only via a single area dropdown,
// validated server-side in accounts/forms.py.)
document.addEventListener('DOMContentLoaded', function () {
    const dobInput = document.getElementById('dobInput');
    const ageDisplay = document.getElementById('ageDisplay');
    const phoneInput = document.getElementById('phoneInput');

    if (dobInput) {
        dobInput.max = new Date().toISOString().split('T')[0];
        dobInput.addEventListener('change', function () {
            if (!dobInput.value) { ageDisplay.value = '—'; return; }
            const dob = new Date(dobInput.value);
            const today = new Date();
            let age = today.getFullYear() - dob.getFullYear();
            const m = today.getMonth() - dob.getMonth();
            if (m < 0 || (m === 0 && today.getDate() < dob.getDate())) age--;
            ageDisplay.value = age >= 0 ? age + ' years' : '—';
        });
    }

    if (phoneInput) {
        phoneInput.addEventListener('input', function () {
            phoneInput.value = phoneInput.value.replace(/\D/g, '');
        });
    }
});