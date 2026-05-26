// ===============================
// BIOENTRY REALTIME FRONTEND
// ===============================

const state = {
  okCount:    0,
  denyCount:  0,
  recentList: [],
  lastPerson: null
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

// ===============================
// HORA
// ===============================

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
  accVal.textContent  = '--%';
  accVal.className    = 'acc-value waiting';
  accFill.style.width = '0%';
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
// RECIENTES (datos en tiempo real
// sincronizados con la BD)
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
      .substring(0, 2)
      .toUpperCase();

    const approved = r.resultado === 'aprobado';
    const pct      = Math.round(r.confianza);

    // hora bonita desde timestamp ISO
    const ts  = new Date(r.timestamp);
    let h     = ts.getHours();
    const ap  = h >= 12 ? 'PM' : 'AM';
    h         = h % 12 || 12;
    const hms = `${h}:${String(ts.getMinutes()).padStart(2,'0')} ${ap}`;

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
      </div>`;
  }).join('');
}

// ===============================
// CONSULTAR /metrics (BD real)
// ===============================

async function pollMetrics() {

  try {

    const res  = await fetch('/metrics');
    const data = await res.json();

    document.getElementById('stat-registered').textContent = data.registered;
    document.getElementById('stat-ok').textContent         = data.total_ok;
    document.getElementById('stat-deny').textContent       = data.total_deny;
    document.getElementById('stat-deny').style.color       =
      data.total_deny > 0 ? 'var(--deny)' : '';

    renderRecent(data.history);

  } catch (err) {
    console.error('metrics error:', err);
  }
}

// ===============================
// CONSULTAR /face_data
// ===============================

async function pollRecognition() {

  try {

    const response = await fetch('/face_data');
    const data     = await response.json();

    // ── NO HAY ROSTRO ──────────────────────────────────────
    if (!data.detected) {
      resetPanel();
      return;
    }

    document.getElementById('no-face-msg').classList.add('hidden');

    const person = {
      name:     data.name,
      initials: data.name.split(' ').map(n => n[0]).join('').substring(0,2),
      role:     data.rol,
      code:     data.codigo,
      program:  data.programa
    };

    const pct      = parseInt(data.confidence);
    const approved = data.approved;

    // ── PERFIL ─────────────────────────────────────────────
    document.getElementById('avatar').textContent    = person.initials;
    document.getElementById('p-name').textContent    = person.name;
    document.getElementById('p-role').textContent    = 'Rol: '    + person.role;
    document.getElementById('p-code').textContent    = 'Código: ' + person.code;
    document.getElementById('p-program').textContent = person.program;
    document.getElementById('a-time').textContent    = nowTime();

    // ── STATUS ─────────────────────────────────────────────
    const st      = document.getElementById('a-status');
    st.textContent = approved ? 'Aprobado' : 'Denegado';
    st.className   = 'status-tag ' + (approved ? 'ok' : 'deny');

    // ── ACCURACY ───────────────────────────────────────────
    setAccuracy(pct, approved);

    // ── BOUNDING BOX ───────────────────────────────────────
    const overlay = document.getElementById('bb-overlay');
    const bbox    = document.getElementById('bbox');
    const bbLabel = document.getElementById('bb-label');
    const bbConf  = document.getElementById('bb-conf');

    const videoEl = document.getElementById('video-feed');
    const scaleX  = videoEl.clientWidth  / 640;
    const scaleY  = videoEl.clientHeight / 480;

    bbox.style.left   = (data.x * scaleX) + 'px';
    bbox.style.top    = (data.y * scaleY) + 'px';
    bbox.style.width  = (data.w * scaleX) + 'px';
    bbox.style.height = (data.h * scaleY) + 'px';
    bbox.style.borderColor = approved ? '#27ae60' : '#c0392b';

    bbLabel.textContent = person.name;
    bbConf.textContent  = pct + '% confianza';

    overlay.classList.remove('hidden');

    // ── FLASH solo cuando cambia persona ───────────────────
    if (state.lastPerson !== person.name) {
      showFlash(approved);
      state.lastPerson = person.name;
    }

  } catch (err) {
    console.error(err);
  }
}

// ===============================
// LOOP
// ===============================

resetPanel();

setInterval(pollRecognition, 1000);
setInterval(pollMetrics,     3000);   // sincroniza con BD cada 3 s