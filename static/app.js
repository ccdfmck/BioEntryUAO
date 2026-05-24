// ===============================
// ESTADO
// ===============================

const state = {
  okCount: 0,
  denyCount: 0,
  recentList: []
};

// ===============================
// RELOJ
// ===============================

function updateClock() {

  const now = new Date();

  document.getElementById("cam-clock").innerHTML =
    now.toLocaleDateString() +
    "<br>" +
    now.toLocaleTimeString();
}

setInterval(updateClock, 1000);

updateClock();

// ===============================
// RESET PANEL
// ===============================

function resetPanel() {

  document.getElementById("p-name").textContent =
    "Esperando identificación...";

  document.getElementById("p-role").textContent = "—";

  document.getElementById("p-code").textContent = "—";

  document.getElementById("p-program").textContent = "—";

  document.getElementById("avatar").textContent = "--";

  document.getElementById("a-status").textContent =
    "En espera";

  document.getElementById("a-status").className =
    "status-tag waiting";

  document.getElementById("acc-val").textContent =
    "--%";

  document.getElementById("acc-fill").style.width =
    "0%";

  document.getElementById("bb-overlay")
    .classList.add("hidden");

  document.getElementById("no-face-msg")
    .classList.remove("hidden");
}

// ===============================
// MOSTRAR ROSTRO
// ===============================

function showFace(data) {

  document.getElementById("no-face-msg")
    .classList.add("hidden");

  // ===============================
  // DATOS PERSONA
  // ===============================

  document.getElementById("p-name").textContent =
    data.name;

  document.getElementById("p-role").textContent =
    "Rol: " + data.rol;

  document.getElementById("p-code").textContent =
    "Código: " + data.codigo;

  document.getElementById("p-program").textContent =
    data.programa;

  // ===============================
  // AVATAR
  // ===============================

  const initials = data.name
    .split(" ")
    .map(n => n[0])
    .join("")
    .substring(0, 2);

  document.getElementById("avatar").textContent =
    initials;

  // ===============================
  // STATUS
  // ===============================

  const approved = data.detected;

  const status = document.getElementById("a-status");

  status.textContent =
    approved ? "Aprobado" : "Denegado";

  status.className =
    approved
      ? "status-tag ok"
      : "status-tag deny";

  // ===============================
  // CONFIDENCE
  // ===============================

  const confidence = parseInt(data.confidence);

  document.getElementById("acc-val").textContent =
    confidence + "%";

  document.getElementById("acc-fill").style.width =
    confidence + "%";

  // ===============================
  // BOUNDING BOX
  // ===============================

  const overlay =
    document.getElementById("bb-overlay");

  const bbox =
    document.getElementById("bbox");

  overlay.classList.remove("hidden");

  bbox.style.left = data.x + "px";
  bbox.style.top = data.y + "px";
  bbox.style.width = data.w + "px";
  bbox.style.height = data.h + "px";

  // ===============================
  // LABEL
  // ===============================

  document.getElementById("bb-label").textContent =
    data.name;

  document.getElementById("bb-conf").textContent =
    confidence + "%";

  // ===============================
  // HORA
  // ===============================

  document.getElementById("a-time").textContent =
    new Date().toLocaleTimeString();

  // ===============================
  // CONTADORES
  // ===============================

  if (approved) {

    state.okCount++;

    document.getElementById("stat-ok").textContent =
      state.okCount;

  } else {

    state.denyCount++;

    document.getElementById("stat-deny").textContent =
      state.denyCount;
  }
}

// ===============================
// CONSULTAR BACKEND
// ===============================

async function pollRecognition() {

  try {

    const response =
      await fetch("/face_data");

    const data =
      await response.json();

    console.log(data);

    if (!data.detected) {

      resetPanel();

      return;
    }

    showFace(data);

  } catch (error) {

    console.error(error);
  }
}

// ===============================
// LOOP
// ===============================

resetPanel();

setInterval(() => {

  pollRecognition();

}, 500);  