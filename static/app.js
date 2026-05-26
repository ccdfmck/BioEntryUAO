// ===============================
// BIOENTRY REALTIME FRONTEND
// ===============================

const state = {
  okCount:    0,
  denyCount:  0,
  recentList: [],
  lastPerson: null,
  adminAuth:  false
};

const THRESHOLD = 60;

// ===============================
// RELOJ
// ===============================

function updateClock() {
  const now    = new Date();
  const days   = ['Sunday','Monday','Tuesday','Wednesday','Thursday','Friday','Saturday'];
  const months = ['January','February','March','April','May','June',
                  'July','August','September','October','November','December'];
  let h    = now.getHours();
  const ap = h >= 12 ? 'PM' : 'AM';
  h        = h % 12 || 12;
  const mm = String(now.getMinutes()).padStart(2,'0');
  const ss = String(now.getSeconds()).padStart(2,'0');
  document.getElementById('cam-clock').innerHTML =
    `${days[now.getDay()]}, ${months[now.getMonth()]} ${now.getDate()}, ${now.getFullYear()}<br>${h}:${mm}:${ss} ${ap}`;
}

updateClock();
setInterval(updateClock, 1000);

function nowTime() {
  const now = new Date();
  let h     = now.getHours();
  const ap  = h >= 12 ? 'PM' : 'AM';
  h         = h % 12 || 12;
  return `${h}:${String(now.getMinutes()).padStart(2,'0')}:${String(now.getSeconds()).padStart(2,'0')} ${ap}`;
}

// ===============================
// ACCURACY BAR
// ===============================

function setAccuracy(pct, approved) {
  const val  = document.getElementById('acc-val');
  const fill = document.getElementById('acc-fill');
  val.textContent = pct + '%';
  val.className   = 'acc-value ' + (approved ? 'ok' : 'deny');
  fill.style.width      = pct + '%';
  fill.style.background = approved
    ? 'linear-gradient(90deg, #1a7a4a, #27ae60)'
    : 'linear-gradient(90deg, #922b21, #c0392b)';
}

// ===============================
// RESET PANEL
// ===============================

function resetPanel() {
  document.getElementById('p-name').textContent    = 'Esperando identificación...';
  document.getElementById('p-role').textContent    = '—';
  document.getElementById('p-code').textContent    = '—';
  document.getElementById('p-program').textContent = '—';
  document.getElementById('avatar').textContent    = '--';
  document.getElementById('a-time').textContent    = '--:--:-- --';
  const st = document.getElementById('a-status');
  st.textContent = 'En espera';
  st.className   = 'status-tag waiting';
  const accVal  = document.getElementById('acc-val');
  const accFill = document.getElementById('acc-fill');
  accVal.textContent       = '--%';
  accVal.className         = 'acc-value waiting';
  accFill.style.width      = '0%';
  accFill.style.background = '#555';
  document.getElementById('bb-overlay').classList.add('hidden');
  document.getElementById('no-face-msg').classList.remove('hidden');
  state.lastPerson = null;
}

// ===============================
// FLASH
// ===============================

function showFlash(approved) {
  const flash = document.getElementById('flash');
  const label = document.getElementById('flash-label');
  flash.className   = 'status-flash ' + (approved ? 'ok-flash' : 'deny-flash');
  label.textContent = approved ? '✓ APROBADO' : '✕ DENEGADO';
  flash.classList.add('show');
  setTimeout(() => flash.classList.remove('show'), 1400);
}

// ===============================
// RECIENTES
// ===============================

function renderRecent(list) {
  if (!list || list.length === 0) {
    document.getElementById('recent-list').innerHTML =
      '<div style="font-size:11.5px;color:#bbb;padding:6px 0;font-style:italic;">Sin registros aún...</div>';
    return;
  }
  document.getElementById('recent-list').innerHTML = list.map(r => {
    const initials = r.nombre.split(' ').map(n => n[0]).join('').substring(0,2).toUpperCase();
    const approved = r.resultado === 'aprobado';
    const pct      = Math.round(r.confianza);
    const ts       = new Date(r.timestamp);
    let h          = ts.getHours();
    const ap       = h >= 12 ? 'PM' : 'AM';
    h              = h % 12 || 12;
    const hms      = `${h}:${String(ts.getMinutes()).padStart(2,'0')} ${ap}`;
    return `
      <div class="recent-item">
        <div class="ri-left">
          <div class="ri-avatar">${initials}</div>
          <div>
            <div class="ri-name">${r.nombre}</div>
            <div class="ri-role">${pct}% · ${hms}</div>
          </div>
        </div>
        <span class="ri-badge ${approved ? 'ok' : 'deny'}">${approved ? 'Aprobado' : 'Denegado'}</span>
      </div>`;
  }).join('');
}

// ===============================
// POLL METRICS
// ===============================

let lastHistorySignature = ''; // FIX: firma para detectar cambios en la lista

async function pollMetrics() {
  try {
    const res  = await fetch('/metrics');
    const data = await res.json();
    document.getElementById('stat-registered').textContent = data.registered;
    document.getElementById('stat-ok').textContent         = data.total_ok;
    document.getElementById('stat-deny').textContent       = data.total_deny;

    // FIX: solo re-renderiza si la lista cambió
    const signature = data.history.map(r => r.timestamp + r.nombre).join('|');
    if (signature !== lastHistorySignature) {
      lastHistorySignature = signature;
      renderRecent(data.history);
    }
  } catch(e) { console.error('metrics:', e); }
}

// ===============================
// POLL FACE DATA
// ===============================

async function pollRecognition() {
  try {
    const response = await fetch('/face_data');
    const data     = await response.json();

    if (!data.detected) { resetPanel(); return; }

    document.getElementById('no-face-msg').classList.add('hidden');

    const person = {
      name:    data.name,
      initials: data.name.split(' ').map(n => n[0]).join('').substring(0,2),
      role:    data.rol,
      code:    data.codigo,
      program: data.programa
    };

    const pct      = parseInt(data.confidence);
    const approved = data.approved;

    document.getElementById('avatar').textContent    = person.initials;
    document.getElementById('p-name').textContent    = person.name;
    document.getElementById('p-role').textContent    = 'Rol: '    + person.role;
    document.getElementById('p-code').textContent    = 'Código: ' + person.code;
    document.getElementById('p-program').textContent = person.program;
    document.getElementById('a-time').textContent    = nowTime();

    const st      = document.getElementById('a-status');
    st.textContent = approved ? 'Aprobado' : 'Denegado';
    st.className   = 'status-tag ' + (approved ? 'ok' : 'deny');

    setAccuracy(pct, approved);

    const videoEl = document.getElementById('video-feed');
    const scaleX  = videoEl.clientWidth  / 640;
    const scaleY  = videoEl.clientHeight / 480;
    const bbox    = document.getElementById('bbox');
    bbox.style.left        = (data.x * scaleX) + 'px';
    bbox.style.top         = (data.y * scaleY) + 'px';
    bbox.style.width       = (data.w * scaleX) + 'px';
    bbox.style.height      = (data.h * scaleY) + 'px';
    bbox.style.borderColor = approved ? '#00e676' : '#ff4444';
    document.getElementById('bb-label').textContent = person.name;
    document.getElementById('bb-conf').textContent  = pct + '% confianza';
    document.getElementById('bb-overlay').classList.remove('hidden');

    if (state.lastPerson !== person.name) {
      showFlash(approved);
      state.lastPerson = person.name;
    }
  } catch(e) { console.error(e); }
}

// ===============================
// LOOP PRINCIPAL
// ===============================

resetPanel();
setInterval(pollRecognition, 1000);
setInterval(pollMetrics,     3000);

// ═══════════════════════════════════════════════════════════
//  ADMIN — LOGIN
// ═══════════════════════════════════════════════════════════

const btnAdmin    = document.getElementById('btn-admin');
const modalLogin  = document.getElementById('modal-login');
const loginClose  = document.getElementById('login-close');
const loginCancel = document.getElementById('login-cancel');
const loginSubmit = document.getElementById('login-submit');
const loginPwd    = document.getElementById('login-password');
const loginError  = document.getElementById('login-error');

function openLogin() {
  loginPwd.value = '';
  loginError.classList.add('hidden');
  modalLogin.classList.remove('hidden');
  setTimeout(() => loginPwd.focus(), 100);
}

function closeLogin() { modalLogin.classList.add('hidden'); }

btnAdmin.addEventListener('click', openLogin);
loginClose.addEventListener('click',  closeLogin);
loginCancel.addEventListener('click', closeLogin);

loginPwd.addEventListener('keydown', e => {
  if (e.key === 'Enter') loginSubmit.click();
});

loginSubmit.addEventListener('click', async () => {
  const pwd = loginPwd.value.trim();
  if (!pwd) return;

  loginSubmit.disabled = true;
  loginSubmit.textContent = 'Verificando...';

  try {
    const res = await fetch('/admin/login', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ password: pwd })
    });

    if (res.ok) {
      state.adminAuth = true;
      closeLogin();
      openAdmin();
    } else {
      loginError.classList.remove('hidden');
      loginPwd.value = '';
      loginPwd.focus();
    }
  } catch(e) {
    loginError.textContent = 'Error de conexión';
    loginError.classList.remove('hidden');
  } finally {
    loginSubmit.disabled    = false;
    loginSubmit.textContent = 'Ingresar';
  }
});

// ═══════════════════════════════════════════════════════════
//  ADMIN — PANEL
// ═══════════════════════════════════════════════════════════

const modalAdmin  = document.getElementById('modal-admin');
const adminClose  = document.getElementById('admin-close');
const adminTabs   = document.querySelectorAll('.admin-tab');
const tabContents = document.querySelectorAll('.tab-content');

function openAdmin() {
  modalAdmin.classList.remove('hidden');
  switchTab('agregar');
}

function closeAdmin() { modalAdmin.classList.add('hidden'); }

adminClose.addEventListener('click', closeAdmin);

// Tabs
adminTabs.forEach(tab => {
  tab.addEventListener('click', () => switchTab(tab.dataset.tab));
});

function switchTab(name) {
  adminTabs.forEach(t => t.classList.toggle('active', t.dataset.tab === name));
  tabContents.forEach(c => c.classList.toggle('hidden', c.id !== 'tab-' + name));
  if (name === 'lista') loadUserList();
}

// ── Foto upload ──────────────────────────────────────────

const photoDrop    = document.getElementById('photo-drop');
const fotoInput    = document.getElementById('foto-input');
const photoPreview = document.getElementById('photo-preview');
const previewImg   = document.getElementById('preview-img');
const photoPlaceholder = document.getElementById('photo-placeholder');

let selectedFile = null;

photoDrop.addEventListener('click', () => fotoInput.click());

photoDrop.addEventListener('dragover', e => {
  e.preventDefault();
  photoDrop.classList.add('drag-over');
});
photoDrop.addEventListener('dragleave', () => photoDrop.classList.remove('drag-over'));
photoDrop.addEventListener('drop', e => {
  e.preventDefault();
  photoDrop.classList.remove('drag-over');
  const file = e.dataTransfer.files[0];
  if (file) setPhoto(file);
});

fotoInput.addEventListener('change', () => {
  if (fotoInput.files[0]) setPhoto(fotoInput.files[0]);
});

function setPhoto(file) {
  selectedFile = file;
  const url = URL.createObjectURL(file);
  previewImg.src = url;
  photoPreview.classList.remove('hidden');
  photoPlaceholder.classList.add('hidden');
}

// ── Guardar usuario ──────────────────────────────────────

const agregarSubmit = document.getElementById('agregar-submit');
const agregarReset  = document.getElementById('agregar-reset');
const agregarError  = document.getElementById('agregar-error');
const agregarOk     = document.getElementById('agregar-ok');
const agregarBtnTxt = document.getElementById('agregar-btn-text');
const agregarSpinner= document.getElementById('agregar-spinner');

function resetForm() {
  document.getElementById('f-nombre').value  = '';
  document.getElementById('f-codigo').value  = '';
  document.getElementById('f-rol').value     = '';
  document.getElementById('f-programa').value= '';
  selectedFile    = null;
  fotoInput.value = '';
  previewImg.src  = '';
  photoPreview.classList.add('hidden');
  photoPlaceholder.classList.remove('hidden');
  agregarError.classList.add('hidden');
  agregarOk.classList.add('hidden');
}

agregarReset.addEventListener('click', resetForm);

agregarSubmit.addEventListener('click', async () => {
  const nombre   = document.getElementById('f-nombre').value.trim();
  const codigo   = document.getElementById('f-codigo').value.trim();
  const rol      = document.getElementById('f-rol').value;
  const programa = document.getElementById('f-programa').value.trim();

  agregarError.classList.add('hidden');
  agregarOk.classList.add('hidden');

  if (!nombre || !codigo || !rol || !programa || !selectedFile) {
    agregarError.textContent = 'Completa todos los campos e incluye una foto.';
    agregarError.classList.remove('hidden');
    return;
  }

  // Loading
  agregarSubmit.disabled = true;
  agregarBtnTxt.textContent = 'Guardando...';
  agregarSpinner.classList.remove('hidden');

  try {
    const fd = new FormData();
    fd.append('nombre',   nombre);
    fd.append('codigo',   codigo);
    fd.append('rol',      rol);
    fd.append('programa', programa);
    fd.append('foto',     selectedFile);

    const res  = await fetch('/admin/agregar', { method: 'POST', body: fd });
    const data = await res.json();

    if (res.ok) {
      agregarOk.classList.remove('hidden');
      resetForm();
      pollMetrics(); // actualizar contador
    } else {
      agregarError.textContent = data.error || 'Error al guardar.';
      agregarError.classList.remove('hidden');
    }
  } catch(e) {
    agregarError.textContent = 'Error de conexión con el servidor.';
    agregarError.classList.remove('hidden');
  } finally {
    agregarSubmit.disabled = false;
    agregarBtnTxt.textContent = 'Guardar usuario';
    agregarSpinner.classList.add('hidden');
  }
});

// ── Lista de usuarios ────────────────────────────────────

async function loadUserList() {
  const list = document.getElementById('user-list');
  list.innerHTML = '<div class="list-loading">Cargando...</div>';

  try {
    const res   = await fetch('/admin/usuarios');
    const users = await res.json();

    if (!users.length) {
      list.innerHTML = '<div class="list-loading">No hay usuarios registrados.</div>';
      return;
    }

    list.innerHTML = users.map(u => {
      const initials = u.nombre.split(' ').map(n => n[0]).join('').substring(0,2).toUpperCase();
      return `
        <div class="user-item" id="ui-${u.id}">
          <div class="user-item-info">
            <div class="user-item-avatar">${initials}</div>
            <div>
              <div class="user-item-name">${u.nombre}</div>
              <div class="user-item-meta">${u.rol} · ${u.codigo} · ${u.programa}</div>
            </div>
          </div>
          <button class="btn-delete" onclick="deleteUser(${u.id}, '${u.nombre}')">Eliminar</button>
        </div>`;
    }).join('');

  } catch(e) {
    list.innerHTML = '<div class="list-loading">Error al cargar usuarios.</div>';
  }
}

async function deleteUser(id, nombre) {
  if (!confirm(`¿Eliminar a ${nombre}? Se borrará su foto y sus datos.`)) return;

  try {
    const res = await fetch(`/admin/eliminar/${id}`, { method: 'DELETE' });
    if (res.ok) {
      document.getElementById(`ui-${id}`)?.remove();
      pollMetrics();
    } else {
      alert('No se pudo eliminar el usuario.');
    }
  } catch(e) {
    alert('Error de conexión.');
  }
}