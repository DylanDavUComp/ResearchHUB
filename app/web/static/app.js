const storageKeys = {
  token: "researchhub.access_token",
};

const allPermissions = [
  "users:create",
  "users:read",
  "users:update",
  "users:delete",
  "settings:manage",
];

const seedUsers = [
  {
    id: "super-admin",
    name: "Super Administrador",
    email: "superadmin@researchhub-u.edu.co",
    role: "Super administrador",
    status: "Activo",
    password: "ResearchHubU2026!",
    permissions: [...allPermissions],
  },
  {
    id: "student-1",
    name: "Maria Gonzalez",
    email: "maria.gonzalez@ucompensar.edu.co",
    role: "Estudiante",
    status: "Activo",
    password: "Estudiante2026!",
    permissions: [],
  },
  {
    id: "coordinator-1",
    name: "Carlos Ramirez",
    email: "carlos.ramirez@ucompensar.edu.co",
    role: "Coordinador de programa",
    status: "Activo",
    password: "Coordinador2026!",
    permissions: ["users:read", "users:update"],
  },
];

let cachedUsers = [];
function getAccessToken() {
  return localStorage.getItem(storageKeys.token);
}


function clearSession() {
  localStorage.removeItem(storageKeys.token);
}


async function apiFetch(url, options = {}) {
  const token = getAccessToken();

  const headers = new Headers(
    options.headers || {}
  );

  if (options.body && !headers.has("Content-Type")) {
    headers.set(
      "Content-Type",
      "application/json"
    );
  }

  if (token) {
    headers.set(
      "Authorization",
      `Bearer ${token}`
    );
  }

  const response = await fetch(
    url,
    {
      ...options,
      headers,
    }
  );

  if (response.status === 401) {
    clearSession();
    showLogin();
  }

  return response;
}

const elements = {
  loginView: document.querySelector("#login-view"),
  appView: document.querySelector("#app-view"),
  loginForm: document.querySelector("#login-form"),
  loginEmail: document.querySelector("#login-email"),
  loginPassword: document.querySelector("#login-password"),
  loginError: document.querySelector("#login-error"),
  togglePassword: document.querySelector("#toggle-password"),
  logoutButtons: document.querySelectorAll(".js-logout"),

  registerForm: document.querySelector("#register-form"),
  registerName: document.querySelector("#register-name"),
  registerEmail: document.querySelector("#register-email"),
  registerPassword: document.querySelector("#register-password"),
  registerPasswordConfirm: document.querySelector("#register-password-confirm"),
  registerError: document.querySelector("#register-error"),
  showRegister: document.querySelector("#show-register"),
  showLogin: document.querySelector("#show-login"),

  navItems: document.querySelectorAll("[data-view]"),
  homeSection: document.querySelector("#home-section"),
  settingsSection: document.querySelector("#settings-section"),
  profileName: document.querySelector("#profile-name"),
  profileRole: document.querySelector("#profile-role"),
  welcomeText: document.querySelector("#welcome-text"),
  usersTableBody: document.querySelector("#users-table-body"),
  userForm: document.querySelector("#user-form"),
  userFormTitle: document.querySelector("#user-form-title"),
  userId: document.querySelector("#user-id"),
  userName: document.querySelector("#user-name"),
  userEmail: document.querySelector("#user-email"),
  userRole: document.querySelector("#user-role"),
  userStatus: document.querySelector("#user-status"),
  userPassword: document.querySelector("#user-password"),
  newUserButton: document.querySelector("#new-user-button"),
  cancelUserButton: document.querySelector("#cancel-user-button"),
  superadminOnlyItems: document.querySelectorAll(".superadmin-only"),
  databaseState: document.querySelector("#database-state"),
  databaseName: document.querySelector("#database-name"),
  databaseEngine: document.querySelector("#database-engine"),
  databaseHost: document.querySelector("#database-host"),
  databasePort: document.querySelector("#database-port"),
  databaseVolume: document.querySelector("#database-volume"),
  databaseDirectory: document.querySelector("#database-directory"),
  databaseTablesBody: document.querySelector("#database-tables-body"),
};

async function getUsers() {
  const response = await apiFetch(
    "/api/v1/usuarios"
  );

  if (!response.ok) {
    throw new Error(
      "No fue posible consultar los usuarios."
    );
  }

  cachedUsers = await response.json();

  return cachedUsers;
}

async function getSessionUser() {
  const token = getAccessToken();

  if (!token) {
    return null;
  }

  try {
    const response = await apiFetch(
      "/api/v1/usuarios/me"
    );

    if (!response.ok) {
      return null;
    }

    return await response.json();

  } catch (error) {
    return null;
  }
}

function hasPermission(user, permission) {
  return user?.permissions?.includes(permission) || user?.role === "Super administrador";
}

function isSuperadmin(user) {
  return user?.role?.trim().toLowerCase() === "super administrador";
}

function syncRoleVisibility(user) {
  document.querySelectorAll(".admin-only").forEach((item) => {
    item.classList.toggle("is-hidden", !hasPermission(user, "settings:manage"));
  });
  elements.superadminOnlyItems.forEach((item) => {
    item.classList.toggle("is-hidden", !isSuperadmin(user));
  });
}

function showAuthenticatedApp(user) {
  elements.loginView.classList.add("is-hidden");
  elements.appView.classList.remove("is-hidden");
  elements.profileName.textContent = user.name;
  elements.profileRole.textContent = user.role;
  elements.welcomeText.textContent = `Bienvenida, ${user.name}`;

  syncRoleVisibility(user);
  showView("home");
}

function showLogin() {
  elements.appView.classList.add("is-hidden");
  elements.loginView.classList.remove("is-hidden");
}

function showRegisterForm() {
  elements.loginForm.classList.add("is-hidden");
  elements.registerForm.classList.remove("is-hidden");

  elements.loginError.textContent = "";
  elements.registerError.textContent = "";

  elements.registerForm.reset();
}


function showLoginForm() {
  elements.registerForm.classList.add("is-hidden");
  elements.loginForm.classList.remove("is-hidden");

  elements.loginError.textContent = "";
  elements.registerError.textContent = "";
}

async function showView(viewName, selectedItem = null) {
  const user = await getSessionUser();

  if (!user) {
    showLogin();
    return;
  }

  if (
    viewName === "settings" &&
    !hasPermission(
      user,
      "settings:manage"
    )
  ) {
    return;
  }

  syncRoleVisibility(user);

  elements.homeSection.classList.toggle(
    "is-hidden",
    viewName !== "home"
  );

  elements.settingsSection.classList.toggle(
    "is-hidden",
    viewName !== "settings"
  );

  elements.navItems.forEach((item) => {
    const isSelected = selectedItem
      ? item === selectedItem
      : item.dataset.view === viewName &&
      !item.classList.contains(
        "nav-subitem"
      );

    item.classList.toggle(
      "active",
      isSelected
    );
  });

  selectedItem
    ?.closest(".nav-group")
    ?.setAttribute("open", "");

  if (viewName === "settings") {
    await renderUsers();
    resetUserForm();
    await loadDatabaseCatalog(user);
  }
}

function renderDatabaseTables(tables) {
  if (!tables.length) {
    elements.databaseTablesBody.innerHTML =
      '<tr><td colspan="4">No hay tablas ni vistas creadas en la base de datos.</td></tr>';
    return;
  }

  elements.databaseTablesBody.innerHTML = tables
    .map((table) => {
      const columns = table.columns
        .map((column) => `${column.name} (${column.type})`)
        .join(", ");
      return `
        <tr>
          <td>${table.schema}</td>
          <td><strong>${table.name}</strong></td>
          <td>${table.type}</td>
          <td>${columns || `${table.column_count} columnas`}</td>
        </tr>
      `;
    })
    .join("");
}

async function loadDatabaseCatalog(user) {
  if (!isSuperadmin(user)) return;

  elements.databaseState.textContent = "Consultando tablas en modo lectura...";
  elements.databaseTablesBody.innerHTML = '<tr><td colspan="4">Cargando catalogo...</td></tr>';

  try {
    const response = await apiFetch(
      "/api/v1/admin/databases"
    );

    if (!response.ok) {
      throw new Error("No fue posible consultar el catalogo de bases de datos.");
    }

    const payload = await response.json();
    const database = payload.databases[0];
    elements.databaseName.textContent = database.name;
    elements.databaseEngine.textContent = database.engine;
    elements.databaseHost.textContent = database.host;
    elements.databasePort.textContent = database.port;
    elements.databaseVolume.textContent = database.docker_volume;
    elements.databaseDirectory.textContent = database.internal_directory;
    elements.databaseState.textContent = "Catalogo disponible en modo lectura.";
    renderDatabaseTables(database.tables);
  } catch (error) {
    elements.databaseState.textContent =
      "No se pudo consultar la base de datos. Verifica que PostgreSQL este activo.";
    elements.databaseTablesBody.innerHTML =
      '<tr><td colspan="4">Catalogo no disponible.</td></tr>';
  }
}

async function renderUsers() {
  const user = await getSessionUser();
  const canUpdate = hasPermission(user, "users:update");
  const canDelete = hasPermission(user, "users:delete");

  elements.usersTableBody.innerHTML = '<tr><td colspan="6">Cargando usuarios...</td></tr>';

  try {
    const users = await getUsers();
    elements.usersTableBody.innerHTML = users
      .map((item) => {
        const permissionCount = item.permissions?.length || 0;
        const deleteDisabled = item.role === "Super administrador" ? "disabled" : "";
        return `
        <tr>
          <td><strong>${item.name}</strong></td>
          <td>${item.email}</td>
          <td><span class="role-pill">${item.role}</span></td>
          <td><span class="status-pill ${item.status === "Inactivo" ? "inactive" : ""}">${item.status}</span></td>
          <td>${permissionCount === allPermissions.length ? "Todos" : `${permissionCount} permisos`}</td>
          <td>
            <div class="action-buttons">
              <button class="table-button" type="button" data-edit="${item.id}" ${canUpdate ? "" : "disabled"}>Editar</button>
              <button class="table-button danger" type="button" data-delete="${item.id}" ${canDelete ? deleteDisabled : "disabled"}>Eliminar</button>
            </div>
          </td>
        </tr>
      `;
      })
      .join("");
  } catch (error) {
    elements.usersTableBody.innerHTML =
      '<tr><td colspan="6">No se pudieron consultar los usuarios en PostgreSQL.</td></tr>';
  }
}

function resetUserForm() {
  elements.userForm.reset();
  elements.userId.value = "";
  elements.userFormTitle.textContent = "Nuevo usuario";
}

function fillUserForm(user) {
  elements.userId.value = user.id;
  elements.userName.value = user.name;
  elements.userEmail.value = user.email;
  elements.userRole.value = user.role;
  elements.userStatus.value = user.status;
  elements.userPassword.value = "";
  document.querySelectorAll('input[name="permission"]').forEach((checkbox) => {
    checkbox.checked = user.permissions.includes(checkbox.value);
  });
  elements.userFormTitle.textContent = "Editar usuario";
}

function collectSelectedPermissions() {
  return Array.from(document.querySelectorAll('input[name="permission"]:checked')).map(
    (checkbox) => checkbox.value,
  );
}

async function upsertUser(event) {
  event.preventDefault();
  const editingId = elements.userId.value;
  const role = elements.userRole.value;
  const permissions =
    role === "Super administrador" ? [...allPermissions] : collectSelectedPermissions();

  const payload = {
    id: editingId || crypto.randomUUID(),
    name: elements.userName.value.trim(),
    email: elements.userEmail.value.trim().toLowerCase(),
    role,
    status: elements.userStatus.value,
    password: elements.userPassword.value || null,
    permissions,
  };

  if (!editingId && !payload.password) {
    payload.password = "ResearchHubTemp2026!";
  }

  try {
    const response = await apifetch(
      editingId ? `/api/v1/usuarios/${editingId}` : "/api/v1/usuarios",
      {
        method: editingId ? "PUT" : "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      },
    );

    if (!response.ok) {
      const errorPayload = await response.json();
      alert(errorPayload.error?.message || "No fue posible guardar el usuario.");
      return;
    }

    renderUsers();
    resetUserForm();
  } catch (error) {
    alert("No fue posible guardar el usuario en PostgreSQL.");
  }
}

async function login(event) {
  event.preventDefault();

  const email = elements.loginEmail.value
    .trim()
    .toLowerCase();

  const password =
    elements.loginPassword.value;

  try {
    const response = await fetch(
      "/api/v1/usuarios/login",
      {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          email,
          password,
        }),
      }
    );

    if (!response.ok) {
      const errorPayload =
        await response.json();

      elements.loginError.textContent =
        errorPayload.error?.message ||
        "Credenciales invalidas.";

      return;
    }

    const payload =
      await response.json();

    localStorage.setItem(
      storageKeys.token,
      payload.access_token
    );

    elements.loginError.textContent = "";

    showAuthenticatedApp(
      payload.user
    );

  } catch (error) {
    elements.loginError.textContent =
      "No fue posible conectar con el servidor.";
  }
}

async function register(event) {
  event.preventDefault();

  const name =
    elements.registerName.value.trim();

  const email =
    elements.registerEmail.value
      .trim()
      .toLowerCase();

  const password =
    elements.registerPassword.value;

  const passwordConfirm =
    elements.registerPasswordConfirm.value;

  elements.registerError.textContent = "";

  if (password !== passwordConfirm) {
    elements.registerError.textContent =
      "Las contraseñas no coinciden.";

    return;
  }

  try {
    const response = await fetch(
      "/api/v1/usuarios/registro",
      {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          name,
          email,
          password,
        }),
      }
    );

    if (!response.ok) {
      const errorPayload =
        await response.json();

      elements.registerError.textContent =
        errorPayload.error?.message ||
        errorPayload.detail?.[0]?.msg ||
        "No fue posible crear la cuenta.";

      return;
    }

    elements.loginEmail.value = email;
    elements.loginPassword.value = "";

    showLoginForm();

  } catch (error) {
    elements.registerError.textContent =
      "No fue posible conectar con el servidor.";
  }
}

elements.loginForm.addEventListener("submit", login);

elements.registerForm.addEventListener(
  "submit",
  register
);

elements.showRegister.addEventListener(
  "click",
  (event) => {
    event.preventDefault();
    showRegisterForm();
  }
);

elements.showLogin.addEventListener(
  "click",
  (event) => {
    event.preventDefault();
    showLoginForm();
  }
);

elements.togglePassword.addEventListener("click", () => {
  const inputType = elements.loginPassword.type === "password" ? "text" : "password";
  elements.loginPassword.type = inputType;
});
elements.logoutButtons.forEach((button) => {
  button.addEventListener("click", (event) => {
    event.preventDefault();
    clearSession();
    showLogin();
  });
});
elements.navItems.forEach((item) => {
  item.addEventListener("click", (event) => {
    event.preventDefault();
    showView(item.dataset.view, item);
  });
});
elements.newUserButton.addEventListener("click", resetUserForm);
elements.cancelUserButton.addEventListener("click", resetUserForm);
elements.userForm.addEventListener("submit", upsertUser);
elements.usersTableBody.addEventListener("click", (event) => {
  const editId = event.target.dataset.edit;
  const deleteId = event.target.dataset.delete;

  if (editId) {
    const user = cachedUsers.find((item) => item.id === editId);
    if (user) fillUserForm(user);
  }

  if (deleteId) {
    apifetch(`/api/v1/usuarios/${deleteId}`, { method: "DELETE" }).then((response) => {
      if (!response.ok) {
        alert("No fue posible eliminar el usuario.");
        return;
      }
      renderUsers();
    });
  }
});
elements.userRole.addEventListener("change", () => {
  if (elements.userRole.value === "Super administrador") {
    document.querySelectorAll('input[name="permission"]').forEach((checkbox) => {
      checkbox.checked = true;
    });
  }
});

const currentUser = getSessionUser(async function initializeApp() {
  const currentUser =
    await getSessionUser();

  if (currentUser) {
    showAuthenticatedApp(
      currentUser
    );
  } else {
    showLogin();
  }
})();