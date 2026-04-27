// Profile management

async function loadProfile() {
    try {
        const me = await api.getMe();
        localStorage.setItem('user', JSON.stringify(me));

        // Avatar con iniciales
        const initials = (me.first_name?.[0] || '') + (me.last_name?.[0] || '');
        document.getElementById('avatar-initials').textContent = initials.toUpperCase() || 'NR';
        document.getElementById('user-fullname').textContent = `${me.first_name} ${me.last_name}`;
        document.getElementById('user-org').textContent = me.organization;

        document.getElementById('p-firstname').value = me.first_name;
        document.getElementById('p-lastname').value = me.last_name;
        document.getElementById('p-email').value = me.email;
        document.getElementById('p-org').value = me.organization;

        // Roles
        const rolesList = document.getElementById('roles-list');
        rolesList.innerHTML = (me.roles || []).map(r =>
            `<span class="badge bg-dark me-1 mb-1">${r.name}</span>`
        ).join('') || '<span class="text-muted small">Sin roles asignados</span>';
    } catch (err) {
        console.error(err);
    }
}

async function saveProfile() {
    const me = JSON.parse(localStorage.getItem('user'));
    const data = {
        first_name: document.getElementById('p-firstname').value,
        last_name: document.getElementById('p-lastname').value,
        organization: document.getElementById('p-org').value
    };
    const msg = document.getElementById('profile-msg');
    msg.classList.add('d-none');
    try {
        await api.updateUser(me.id, data);
        msg.className = 'alert alert-success';
        msg.textContent = 'Perfil actualizado correctamente';
        msg.classList.remove('d-none');
        loadProfile();
    } catch (err) {
        msg.className = 'alert alert-danger';
        msg.textContent = 'Error: ' + err.message;
        msg.classList.remove('d-none');
    }
}

function openPasswordModal() {
    const newPw = prompt('Nueva contraseña (mínimo 6 caracteres):');
    if (!newPw || newPw.length < 6) {
        alert('Contraseña inválida');
        return;
    }
    const me = JSON.parse(localStorage.getItem('user'));
    api.updateUser(me.id, { password: newPw }).then(() => {
        alert('Contraseña actualizada');
    }).catch(err => alert('Error: ' + err.message));
}

document.addEventListener('DOMContentLoaded', loadProfile);
