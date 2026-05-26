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

  let h = now.getHours();

  const ap = h >= 12 ? 'PM' : 'AM';

  h = h % 12 || 12;

  return `${h}:${String(now.getMinutes()).padStart(2,'0')}:${String(now.getSeconds()).padStart(2,'0')} ${ap}`;
}

// ===============================
// ACCURACY BAR
// ===============================

function setAccuracy(pct, approved) {

  const val  = document.getElementById('acc-val');
  const fill = document.getElementById('acc-fill');

  val.textContent = pct + '%';

  val.className = 'acc-value ' + (approved ? 'ok' : 'deny');

  fill.style.width = pct + '%';

  fill.style.background = approved
    ? 'linear-gradient(90deg, #1a7a4a, #27ae60)'
    : 'linear-gradient(90deg, #922b21, #c0392b)';
}

// ===============================
// RESET PANEL
// ===============================

function resetPanel() {

  document.getElementById('p-name').textContent =
    'Esperando identificación...';

  document.getElementById('p-role').textContent = '—';

  document.getElementById('p-code').textContent = '—';

  document.getElementById('p-program').textContent = '—';

  document.getElementById('avatar').textContent = '--';

  document.getElementById('a-time').textContent = '--:--:-- --';

  const st = document.getElementById('a-status');

  st.textContent = 'En espera';

  st.className = 'status-tag waiting';

  const accVal  = document.getElementById('acc-val');
  const accFill = document.getElementById('acc-fill');

  accVal.textContent = '--%';

  accVal.className = 'acc-value waiting';

  accFill.style.width = '0%';

  accFill.style.background = '#555';

  document.getElementById('bb-overlay')
    .classList.add('hidden');

  document.getElementById('no-face-msg')
    .classList.remove('hidden');

  state.lastPerson = null;
}

// ===============================
// FLASH
// ===============================

function showFlash(approved) {

  const flash = document.getElementById('flash');

  const label = document.getElementById('flash-label');

  flash.className =
    'status-flash ' + (approved ? 'ok-flash' : 'deny-flash');

  label.textContent =
    approved ? '✓ APROBADO' : '✕ DENEGADO';

  flash.classList.add('show');

  setTimeout(() => {
    flash.classList.remove('show');
  }, 1400);
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

    const initials = r.nombre
      .split(' ')
      .map(n => n[0])
      .join('')
      .substring(0,2)
      .toUpperCase();

    const approved = r.resultado === 'aprobado';

    const pct = Math.round(r.confianza);

    const ts = new Date(r.timestamp);

    let h = ts.getHours();

    const ap = h >= 12 ? 'PM' : 'AM';

    h = h % 12 || 12;

    const hms =
      `${h}:${String(ts.getMinutes()).padStart(2,'0')} ${ap}`;

    return `
      <div class="recent-item">

        <div class="ri-left">

          <div class="ri-avatar">${initials}</div>

          <div>
            <div class="ri-name">${r.nombre}</div>
            <div class="ri-role">${pct}% · ${hms}</div>
          </div>

        </div>

        <span class="ri-badge ${approved ? 'ok' : 'deny'}">
          ${approved ? 'Aprobado' : 'Denegado'}
        </span>

      </div>
    `;
  }).join('');
}

// ===============================
// POLL METRICS
// ===============================

let lastHistorySignature = '';

async function pollMetrics() {

  try {

    const res = await fetch('/metrics');

    const data = await res.json();

    document.getElementById('stat-registered').textContent =
      data.registered;

    document.getElementById('stat-ok').textContent =
      data.total_ok;

    document.getElementById('stat-deny').textContent =
      data.total_deny;

    const signature =
      data.history.map(r => r.timestamp + r.nombre).join('|');

    if (signature !== lastHistorySignature) {

      lastHistorySignature = signature;

      renderRecent(data.history);
    }

  } catch(e) {

    console.error('metrics:', e);
  }
}

// ===============================
// POLL FACE DATA
// ===============================

async function pollRecognition() {

  try {

    const response = await fetch('/face_data');

    const data = await response.json();

    if (!data.detected) {

      resetPanel();

      return;
    }

    document.getElementById('no-face-msg')
      .classList.add('hidden');

    const person = {

      name: data.name,

      initials: data.name
        .split(' ')
        .map(n => n[0])
        .join('')
        .substring(0,2),

      role: data.rol,
      code: data.codigo,
      program: data.programa
    };

    const pct = parseInt(data.confidence);

    const approved = data.approved;

    document.getElementById('avatar').textContent =
      person.initials;

    document.getElementById('p-name').textContent =
      person.name;

    document.getElementById('p-role').textContent =
      'Rol: ' + person.role;

    document.getElementById('p-code').textContent =
      'Código: ' + person.code;

    document.getElementById('p-program').textContent =
      person.program;

    document.getElementById('a-time').textContent =
      nowTime();

    const st = document.getElementById('a-status');

    st.textContent =
      approved ? 'Aprobado' : 'Denegado';

    st.className =
      'status-tag ' + (approved ? 'ok' : 'deny');

    setAccuracy(pct, approved);

    // =========================================
    // OCULTAR BOUNDING BOX HTML
    // =========================================

    document.getElementById('bb-overlay')
      .classList.add('hidden');

    if (state.lastPerson !== person.name) {

      showFlash(approved);

      state.lastPerson = person.name;
    }

  } catch(e) {

    console.error(e);
  }
}

// ===============================
// LOOP PRINCIPAL
// ===============================

resetPanel();

setInterval(pollRecognition, 1000);

setInterval(pollMetrics, 3000);