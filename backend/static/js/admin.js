// ⚡ Recuperar org_id del login
const ORG_ID = localStorage.getItem("org_id");

if (!ORG_ID) {
  alert("No se encontró organización. Inicia sesión de nuevo.");
  window.location.href = "/login";
}

async function cargarPacientes() {
  const res = await fetch(`/admin/${ORG_ID}/pacientes`);
  const data = await res.json();
  const tbody = document.querySelector('#tabla-pacientes tbody');
  tbody.innerHTML = '';
  data.forEach(p => {
    const tr = document.createElement('tr');
    tr.innerHTML = `
      <td>${p.id}</td>
      <td>${p.nombre}</td>
      <td>${p.edad}</td>
      <td>${p.sexo}</td>
      <td>${p.altura}</td>
      <td>${p.peso}</td>
      <td>${p.username}</td>
      <td>
        <button class="btn btn-edit" onclick="editar(${p.id})">Editar</button>
        <button class="btn btn-delete" onclick="eliminar(${p.id})">Eliminar</button>
      </td>
    `;
    tbody.appendChild(tr);
  });
}

document.getElementById('alta-form').addEventListener('submit', async (e) => {
  e.preventDefault();
  const data = {
    nombre: document.getElementById('nombre').value,
    edad: parseInt(document.getElementById('edad').value),
    sexo: document.getElementById('sexo').value,
    altura_cm: parseFloat(document.getElementById('altura').value),
    peso_kg: parseFloat(document.getElementById('peso').value),
    username: document.getElementById('username').value,
    password: document.getElementById('password').value
  };

  await fetch(`/admin/${ORG_ID}/pacientes`, {
    method: 'POST',
    headers: {'Content-Type': 'application/json'},
    body: JSON.stringify(data)
  });
  cargarPacientes();
  e.target.reset();
});

async function eliminar(id) {
  await fetch(`/admin/${ORG_ID}/pacientes/` + id, { method: 'DELETE' });
  cargarPacientes();
}

async function editar(id) {
  const nuevoNombre = prompt("Nuevo nombre (deja vacío para no cambiar):");
  const nuevaEdad = prompt("Nueva edad (deja vacío para no cambiar):");
  const nuevoSexo = prompt("Nuevo sexo (M/F, vacío para no cambiar):");
  const nuevaAltura = prompt("Nueva altura (vacío para no cambiar):");
  const nuevoPeso = prompt("Nuevo peso (vacío para no cambiar):");
  const nuevoUsuario = prompt("Nuevo username (vacío para no cambiar):");
  const nuevaPassword = prompt("Nueva contraseña (vacío para no cambiar):");

  // Armamos solo los campos que el admin llenó
  const data = {};
  if (nuevoNombre) data.nombre = nuevoNombre;
  if (nuevaEdad) data.edad = parseInt(nuevaEdad);
  if (nuevoSexo) data.sexo = nuevoSexo;
  if (nuevaAltura) data.altura_cm = parseFloat(nuevaAltura);
  if (nuevoPeso) data.peso_kg = parseFloat(nuevoPeso);
  if (nuevoUsuario) data.username = nuevoUsuario;
  if (nuevaPassword) data.password = nuevaPassword;

  if (Object.keys(data).length === 0) {
    alert("No se hizo ningún cambio.");
    return;
  }

  await fetch(`/admin/${ORG_ID}/pacientes/` + id, {
    method: 'PUT',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(data)
  });
  cargarPacientes();
}


cargarPacientes();

document.getElementById("logout-btn").addEventListener("click", () => {
  localStorage.removeItem("org_id");
  localStorage.removeItem("role");
  localStorage.removeItem("username");

  window.location.href = "/login";
});
