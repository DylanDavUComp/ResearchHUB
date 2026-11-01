// Consola de configuracion general del ecosistema. Usa la misma sesion institucional
// de ResearchHUB y ResearchOS (cookie HttpOnly en PostgreSQL), pero solo entra un
// superadministrador: el login lo exige y cada API lo vuelve a comprobar.
const csrfHeader = { name: "X-Requested-With", value: "ResearchHUB" };
const superadminRole = "Super administrador";

const consoleViews = {
  announcements: { hash: "#comunicados", load: () => loadAnnouncementSettings() },
  modalities: { hash: "#modalidades", load: (user) => loadModalitySettings(user) },
  users: {
    hash: "#usuarios",
    load: async () => {
      userAdmin.reset();
      await userAdmin.render();
    },
  },
  database: { hash: "#base-de-datos", load: () => loadDatabaseCatalog() },
};

const elements = {
  loading: document.querySelector("#console-loading"),
  loginView: document.querySelector("#login-view"),
  loginForm: document.querySelector("#login-form"),
  loginEmail: document.querySelector("#login-email"),
  loginPassword: document.querySelector("#login-password"),
  loginSubmit: document.querySelector("#login-submit"),
  loginError: document.querySelector("#login-error"),
  togglePassword: document.querySelector("#toggle-password"),
  accessDenied: document.querySelector("#access-denied"),
  deniedUser: document.querySelector("#denied-user"),
  switchAccount: document.querySelector("#switch-account"),
  appView: document.querySelector("#app-view"),
  sidebar: document.querySelector("#main-sidebar"),
  sidebarBackdrop: document.querySelector("#sidebar-backdrop"),
  mobileMenuButton: document.querySelector("#mobile-menu-button"),
  profileName: document.querySelector("#profile-name"),
  profileRole: document.querySelector("#profile-role"),
  navItems: document.querySelectorAll(".nav-item[data-view]"),
  sections: document.querySelectorAll("[data-section]"),
  databaseState: document.querySelector("#database-state"),
  databaseName: document.querySelector("#database-name"),
  databaseEngine: document.querySelector("#database-engine"),
  databaseHost: document.querySelector("#database-host"),
  databasePort: document.querySelector("#database-port"),
  databaseVolume: document.querySelector("#database-volume"),
  databaseDirectory: document.querySelector("#database-directory"),
  databaseTablesBody: document.querySelector("#database-tables-body"),
};

let currentUser = null;

async function apiFetch(url, options = {}) {
  const headers = new Headers(options.headers || {});
  headers.set(csrfHeader.name, csrfHeader.value);
  if (options.body && !headers.has("Content-Type")) {
    headers.set("Content-Type", "application/json");
  }
  const response = await fetch(url, { ...options, credentials: "same-origin", headers });
  if (response.status === 401 && !url.endsWith("/usuarios/login")) {
    showLogin("Tu sesión expiró. Inicia sesión de nuevo.");
  }
  return response;
}

async function endSession() {
  try {
    await apiFetch("/api/v1/usuarios/logout", { method: "POST" });
  } catch (error) {
    // Sin conexion, la sesion expira sola en el servidor.
  }
}

async function readError(response) {
  try {
    const payload = await response.json();
    return payload.error || {};
  } catch (error) {
    return {};
  }
}

function showOnly(view) {
  elements.loading.classList.add("is-hidden");
  elements.loginView.classList.toggle("is-hidden", view === "app");
  elements.appView.classList.toggle("is-hidden", view !== "app");
  elements.loginForm.classList.toggle("is-hidden", view !== "login");
  elements.accessDenied.classList.toggle("is-hidden", view !== "denied");
}

function showLogin(message = "") {
  currentUser = null;
  setNavigationOpen(false);
  showOnly("login");
  elements.loginError.textContent = message;
}

function showDenied(user) {
  showOnly("denied");
  elements.deniedUser.textContent = user?.email || "tu cuenta";
  elements.accessDenied.focus();
}

function setNavigationOpen(isOpen) {
  document.body.classList.toggle("nav-open", isOpen);
  elements.sidebar.classList.toggle("is-open", isOpen);
  elements.mobileMenuButton.setAttribute("aria-expanded", String(isOpen));
  elements.mobileMenuButton.setAttribute(
    "aria-label",
    isOpen ? "Cerrar menú de navegación" : "Abrir menú de navegación",
  );
}

async function fetchCurrentUser() {
  const response = await apiFetch("/api/v1/usuarios/me");
  if (!response.ok) {
    throw new Error("La sesión no es válida.");
  }
  currentUser = await response.json();
  return currentUser;
}

function viewFromHash() {
  const entry = Object.entries(consoleViews).find(([, view]) => view.hash === window.location.hash);
  return entry ? entry[0] : "announcements";
}

async function showView(viewName) {
  if (!consoleViews[viewName]) viewName = "announcements";
  elements.sections.forEach((section) => {
    section.classList.toggle("is-hidden", section.dataset.section !== viewName);
  });
  elements.navItems.forEach((item) => {
    const isSelected = item.dataset.view === viewName;
    item.classList.toggle("active", isSelected);
    if (isSelected) {
      item.setAttribute("aria-current", "page");
    } else {
      item.removeAttribute("aria-current");
    }
  });
  await consoleViews[viewName].load(currentUser);
}

function showConsole(user) {
  currentUser = user;
  elements.profileName.textContent = user.name;
  elements.profileRole.textContent = user.role;
  showOnly("app");
  showView(viewFromHash());
}

async function loadConsole() {
  let user;
  try {
    user = await fetchCurrentUser();
  } catch (error) {
    showLogin();
    return;
  }
  if (user.role !== superadminRole) {
    showDenied(user);
    return;
  }
  showConsole(user);
}

function databaseCell(text, strong = false) {
  const cell = document.createElement("td");
  if (strong) {
    const value = document.createElement("strong");
    value.textContent = text;
    cell.append(value);
  } else {
    cell.textContent = text;
  }
  return cell;
}

function databaseMessageRow(message) {
  const row = document.createElement("tr");
  const cell = databaseCell(message);
  cell.colSpan = 4;
  row.append(cell);
  elements.databaseTablesBody.replaceChildren(row);
}

async function loadDatabaseCatalog() {
  elements.databaseState.textContent = "Consultando tablas en modo lectura...";
  databaseMessageRow("Cargando catálogo...");
  try {
    const response = await apiFetch("/api/v1/admin/databases");
    if (!response.ok) {
      throw new Error("No fue posible consultar el catálogo de bases de datos.");
    }
    const database = (await response.json()).databases[0];
    elements.databaseName.textContent = database.name;
    elements.databaseEngine.textContent = database.engine;
    elements.databaseHost.textContent = database.host;
    elements.databasePort.textContent = database.port;
    elements.databaseVolume.textContent = database.docker_volume;
    elements.databaseDirectory.textContent = database.internal_directory;
    elements.databaseState.textContent = "Catálogo disponible en modo lectura.";
    if (!database.tables.length) {
      databaseMessageRow("No hay tablas ni vistas creadas en la base de datos.");
      return;
    }
    elements.databaseTablesBody.replaceChildren(
      ...database.tables.map((table) => {
        const row = document.createElement("tr");
        const columns = table.columns.map((column) => `${column.name} (${column.type})`).join(", ");
        row.append(
          databaseCell(table.schema),
          databaseCell(table.name, true),
          databaseCell(table.type),
          databaseCell(columns || `${table.column_count} columnas`),
        );
        return row;
      }),
    );
  } catch (error) {
    elements.databaseState.textContent =
      "No se pudo consultar la base de datos. Verifica que PostgreSQL esté activo.";
    databaseMessageRow("Catálogo no disponible.");
  }
}

async function login(event) {
  event.preventDefault();
  const email = elements.loginEmail.value.trim().toLowerCase();
  const password = elements.loginPassword.value;

  if (!email || !password) {
    showLogin("Ingresa tu correo institucional y tu contraseña.");
    (email ? elements.loginPassword : elements.loginEmail).focus();
    return;
  }

  elements.loginSubmit.disabled = true;
  elements.loginSubmit.textContent = "Verificando…";
  try {
    const response = await apiFetch("/api/v1/usuarios/login", {
      method: "POST",
      body: JSON.stringify({ email, password, settings_console: true }),
    });

    if (!response.ok) {
      const error = await readError(response);
      showLogin(
        response.status === 422
          ? "Revisa el formato del correo y la contraseña."
          : error.message || "No fue posible iniciar sesión.",
      );
      elements.loginPassword.value = "";
      elements.loginPassword.focus();
      return;
    }

    elements.loginPassword.value = "";
    await loadConsole();
  } catch (error) {
    showLogin("No fue posible conectar con el servidor. Intenta de nuevo.");
  } finally {
    elements.loginSubmit.disabled = false;
    elements.loginSubmit.textContent = "Iniciar sesión";
  }
}

async function logout() {
  await endSession();
  window.location.assign("/");
}

elements.loginForm.addEventListener("submit", login);
elements.togglePassword.addEventListener("click", () => {
  const isVisible = elements.loginPassword.type === "text";
  elements.loginPassword.type = isVisible ? "password" : "text";
  elements.togglePassword.setAttribute("aria-pressed", String(!isVisible));
  elements.togglePassword.setAttribute(
    "aria-label",
    isVisible ? "Mostrar contraseña" : "Ocultar contraseña",
  );
});
elements.switchAccount.addEventListener("click", async () => {
  await endSession();
  showLogin();
  elements.loginEmail.focus();
});
document.querySelectorAll(".js-logout").forEach((button) => {
  button.addEventListener("click", logout);
});
userAdmin.init({ apiFetch, getCurrentUser: fetchCurrentUser });
elements.navItems.forEach((item) => {
  item.addEventListener("click", () => {
    if (window.matchMedia("(max-width: 860px)").matches) {
      setNavigationOpen(false);
    }
  });
});
window.addEventListener("hashchange", () => {
  if (currentUser) showView(viewFromHash());
});
elements.mobileMenuButton.addEventListener("click", () => {
  setNavigationOpen(!elements.sidebar.classList.contains("is-open"));
});
elements.sidebarBackdrop.addEventListener("click", () => setNavigationOpen(false));
document.addEventListener("keydown", (event) => {
  if (event.key === "Escape") {
    setNavigationOpen(false);
  }
});

loadConsole();
