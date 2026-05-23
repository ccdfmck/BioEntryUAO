//  app.js — Lógica de BioEntry
//  Cuando tengan el backend Flask, ver comentarios "CONEXIÓN CON FLASK"

// Base de datos simulada
// CONEXIÓN CON FLASK: este array se elimina y los datos
// vienen de fetch('/api/recognition')
const DB = [
  { name: 'Luisa María Restrepo V.', initials: 'LM', role: 'Estudiante', code: '2235541', program: 'Ing. Mecatrónica'  },
  { name: 'Carlos Andrés Muñoz',     initials: 'CA', role: 'Estudiante', code: '2241189', program: 'Ing. de Sistemas'  },
  { name: 'Valentina Ríos Salcedo',  initials: 'VR', role: 'Docente',    code: 'D-0082',  program: 'Matemáticas'       },
  { name: 'Samuel Ospina Giraldo',   initials: 'SO', role: 'Estudiante', code: '2238867', program: 'Ing. Industrial'   },
  { name: 'Mariana Cárdenas P.',     initials: 'MC', role: 'Estudiante', code: '2250011', program: 'Diseño de Medios'  },
  { name: 'Jorge Esteban Pinto',     initials: 'JP', role: 'Docente',    code: 'D-0041',  program: 'Física'            },
  { name: 'Ana Sofía Guerrero',      initials: 'AG', role: 'Estudiante', code: '2244320', program: 'Ing. Biomédica'    },
  { name: 'Felipe Vargas Torres',    initials: 'FV', role: 'Estudiante', code: '2239504', program: 'Ing. Mecatrónica'  },
];

//Estado global
const state = {
  okCount:    0,
  denyCount:  0,
  recentList: [],
};

const THRESHOLD = 75; // % mínimo de confianza para aprobar

//Reloj en tiempo real
function updateClock() {
  const now    = new Date();
  const days   = ['Sunday','Monday','Tuesday','Wednesday','Thursday','Friday','Saturday'];
  const months = ['January','February','March','April','May','June',
                  'July','August','September','October','November','December'];
  let h = now.getHours();
  const ampm = h >= 12 ? 'PM' : 'AM';
  h = h % 12 || 12;
  const mm = String(now.getMinutes()).padStart(2, '0');
  const ss = String(now.getSeconds()).padStart(2, '0');
  document.getElementById('cam-clock').innerHTML =
    `${days[now.getDay()]}, ${months[now.getMonth()]} ${now.getDate()}, ${now.getFullYear()}<br>${h}:${mm}:${ss} ${ampm}`;
}
updateClock();
setInterval(updateClock, 1000);

//Hora formateada para el registro
function nowTime() {
  const now = new Date();
  let h = now.getHours();
  const ampm = h >= 12 ? 'PM' : 'AM';
  h = h % 12 || 12;
  return `${h}:${String(now.getMinutes()).padStart(2,'0')}:${String(now.getSeconds()).padStart(2,'0')} ${ampm}`;
}

//Barra de accuracy
function setAccuracy(pct, approved) {
  const val  = document.getElementById('acc-val');
  const fill = document.getElementById('acc-fill');
  val.textContent  = pct + '%';
  val.className    = 'acc-value ' + (approved ? 'ok' : 'deny');
  fill.style.width = pct + '%';
  fill.style.background = approved
    ? 'linear-gradient(90deg, #1a7a4a, #27ae60)'
    : 'linear-gradient(90deg, #922b21, #c0392b)';
}

//Resetear panel a "en espera"
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

  document.getElementById('acc-val').textContent      = '--%';
  document.getElementById('acc-val').className        = 'acc-value waiting';
  document.getElementById('acc-fill').style.width     = '0%';
  document.getElementById('acc-fill').style.background = '#ddd';

  document.getElementById('bb-overlay').classList.add('hidden');
  document.getElementById('no-face-msg').classList.remove('hidden');
}

//Flash APROBADO / DENEGADO
function showFlash(approved) {
  const flash = document.getElementById('flash');
  const label = document.getElementById('flash-label');
  flash.className   = 'status-flash ' + (approved ? 'ok-flash' : 'deny-flash');
  label.textContent = approved ? '✓ APROBADO' : '✕ DENEGADO';
  flash.classList.add('show');
  setTimeout(() => flash.classList.remove('show'), 1400);
}

//Lista de recientes
function addRecent(person, approved, pct) {
  state.recentList.unshift({ person, approved, pct });
  if (state.recentList.length > 6) state.recentList.pop();

  document.getElementById('recent-list').innerHTML = state.recentList.map(r => `
    <div class="recent-item">
      <div class="ri-left">
        <div class="ri-avatar">${r.person.initials}</div>
        <div>
          <div class="ri-name">${r.person.name.split(' ').slice(0, 2).join(' ')}</div>
          <div class="ri-role">${r.person.role} · ${r.pct}%</div>
        </div>
      </div>
      <span class="ri-badge ${r.approved ? 'ok' : 'deny'}">${r.approved ? 'Aprobado' : 'Denegado'}</span>
    </div>
  `).join('');
}

// Ciclo de reconocimiento simulado 
// CONEXIÓN CON FLASK: reemplazar esta función por pollRecognition()
// que hace fetch('/api/recognition') cada 500ms
function simulateRecognition() {
  const searching = document.getElementById('searching');

  // Fase 1: mostrar "Analizando..." (1.5 s)
  searching.classList.add('show');
  document.getElementById('no-face-msg').classList.add('hidden');

  setTimeout(() => {
    searching.classList.remove('show');

    // Elegir persona aleatoria de la DB
    const person = DB[Math.floor(Math.random() * DB.length)];

    // Generar accuracy: 70% aprobado, 30% denegado
    const forceApprove = Math.random() < 0.70;
    const pct      = forceApprove
      ? Math.floor(Math.random() * 20) + 78   // 78–97 %
      : Math.floor(Math.random() * 22) + 48;  // 48–69 %
    const approved = pct >= THRESHOLD;
    const time     = nowTime();

    // Actualizar perfil
    document.getElementById('avatar').textContent    = person.initials;
    document.getElementById('p-name').textContent    = person.name;
    document.getElementById('p-role').textContent    = 'Rol: ' + person.role;
    document.getElementById('p-code').textContent    = 'Código: ' + person.code;
    document.getElementById('p-program').textContent = person.program;
    document.getElementById('a-time').textContent    = time;

    // Estado acceso
    const st = document.getElementById('a-status');
    st.textContent = approved ? 'Aprobado' : 'Denegado';
    st.className   = 'status-tag ' + (approved ? 'ok' : 'deny');

    // Accuracy bar
    setAccuracy(pct, approved);

    // Bounding box
    const overlay = document.getElementById('bb-overlay');
    const bbox    = document.getElementById('bbox');
    const bbLabel = document.getElementById('bb-label');
    const bbConf  = document.getElementById('bb-conf');

    overlay.classList.remove('hidden');

    // Posición simulada con variación realista
    // CONEXIÓN CON FLASK: usar d.x, d.y, d.w, d.h del JSON de OpenCV
    bbox.style.top    = (12 + Math.random() * 10) + '%';
    bbox.style.left   = (30 + Math.random() * 18) + '%';
    bbox.style.width  = (28 + Math.random() * 8)  + '%';
    bbox.style.height = (55 + Math.random() * 12) + '%';

    bbox.className    = 'bounding-box animating' + (approved ? '' : ' deny-box');
    bbLabel.textContent = person.name.split(' ').slice(0, 2).join(' ');
    bbLabel.className   = 'bb-label' + (approved ? '' : ' deny-label');
    bbConf.textContent  = 'confianza: ' + pct + '%';
    bbConf.className    = 'bb-conf'  + (approved ? '' : ' deny-conf');

    // Flash
    showFlash(approved);

    // Contadores
    if (approved) {
      state.okCount++;
      document.getElementById('stat-ok').textContent = state.okCount;
    } else {
      state.denyCount++;
      document.getElementById('stat-deny').textContent = state.denyCount;
    }

    // Recientes
    addRecent(person, approved, pct);

    // Fase 2: mostrar resultado 4 s, luego resetear y volver a ciclar
    setTimeout(() => {
      resetPanel();
      setTimeout(simulateRecognition, 3000 + Math.random() * 3000);
    }, 4000);

  }, 1500);
}

//Arrancar
setTimeout(simulateRecognition, 2000);