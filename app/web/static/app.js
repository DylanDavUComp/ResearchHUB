const storageKeys = {
  token: "researchhub.access_token",
};

const allPermissions = [
  "users:create",
  "users:read",
  "users:update",
  "users:delete",
  "settings:manage",
  "degree_work:self:create",
  "degree_work:self:read",
  "degree_work:self:submit",
  "degree_work:assigned:read",
  "degree_work:assigned:review",
  "degree_work:assigned:evaluate",
  "degree_work:program:read",
  "degree_work:program:decide",
  "degree_work:program:assign",
  "degree_work:program:report",
  "degree_work:any:read",
  "degree_work:any:support",
  "modalities:read",
  "modalities:create",
  "modalities:update",
  "modalities:delete",
  "modalities:publish",
  "modalities:retire",
  "audit:any:read",
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
  appLauncher: document.querySelector("#app-launcher"),
  openResearchHub: document.querySelector("#open-researchhub"),
  openResearchOs: document.querySelector("#open-researchos"),
  researchOsActionLabel: document.querySelector("#researchos-action-label"),
  openCris: document.querySelector("#open-cris"),
  crisActionLabel: document.querySelector("#cris-action-label"),
  openCrai: document.querySelector("#open-crai"),
  craiActionLabel: document.querySelector("#crai-action-label"),
  opportunityCarousel: document.querySelector("#opportunity-carousel"),
  opportunitySlides: document.querySelectorAll("[data-opportunity-slide]"),
  opportunityDots: document.querySelectorAll("[data-opportunity-index]"),
  opportunityPrev: document.querySelector("#opportunity-prev"),
  opportunityNext: document.querySelector("#opportunity-next"),
  opportunityCount: document.querySelector(".opportunity-count"),
  opportunityStatus: document.querySelector("#opportunity-status"),
  researchBlogLinks: document.querySelectorAll(".js-research-blog-link"),
  launcherBack: document.querySelector("#back-to-apps"),
  loginView: document.querySelector("#login-view"),
  appView: document.querySelector("#app-view"),
  loginForm: document.querySelector("#login-form"),
  loginEmail: document.querySelector("#login-email"),
  loginPassword: document.querySelector("#login-password"),
  loginError: document.querySelector("#login-error"),
  togglePassword: document.querySelector("#toggle-password"),
  logoutButtons: document.querySelectorAll(".js-logout"),
  sidebar: document.querySelector("#main-sidebar"),
  mobileMenuButton: document.querySelector("#mobile-menu-button"),
  sidebarBackdrop: document.querySelector("#sidebar-backdrop"),

  registerForm: document.querySelector("#register-form"),
  registerName: document.querySelector("#register-name"),
  registerEmail: document.querySelector("#register-email"),
  registerPassword: document.querySelector("#register-password"),
  registerPasswordConfirm: document.querySelector("#register-password-confirm"),
  registerError: document.querySelector("#register-error"),
  showRegister: document.querySelector("#show-register"),
  registerAccess: document.querySelector("#register-access"),
  showLogin: document.querySelector("#show-login"),

  navItems: document.querySelectorAll("[data-view]"),
  homeSection: document.querySelector("#home-section"),
  degreeWorkSection: document.querySelector("#degree-work-section"),
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

function setNavigationOpen(isOpen) {
  document.body.classList.toggle("nav-open", isOpen);
  elements.sidebar.classList.toggle("is-open", isOpen);
  elements.mobileMenuButton.setAttribute("aria-expanded", String(isOpen));
  elements.mobileMenuButton.setAttribute(
    "aria-label",
    isOpen ? "Cerrar menu de navegacion" : "Abrir menu de navegacion"
  );
}

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
  document.querySelectorAll(".student-only").forEach((item) => {
    item.classList.toggle("is-hidden", user?.role !== "Estudiante");
  });
}

function showAuthenticatedApp(user) {
  elements.appLauncher.classList.add("is-hidden");
  elements.loginView.classList.add("is-hidden");
  elements.appView.classList.remove("is-hidden");
  elements.profileName.textContent = user.name;
  elements.profileRole.textContent = user.role;
  elements.welcomeText.textContent = `Bienvenida, ${user.name}`;
  setNavigationOpen(false);

  syncRoleVisibility(user);
  showView("home");
}

function showLogin() {
  stopOpportunityRotation();
  setNavigationOpen(false);
  elements.appLauncher.classList.add("is-hidden");
  elements.appView.classList.add("is-hidden");
  elements.loginView.classList.remove("is-hidden");
}

function showLauncher() {
  setNavigationOpen(false);
  elements.loginView.classList.add("is-hidden");
  elements.appView.classList.add("is-hidden");
  elements.appLauncher.classList.remove("is-hidden");
  scheduleOpportunityRotation();
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

  elements.degreeWorkSection.classList.toggle(
    "is-hidden",
    viewName !== "degree-work"
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
    if (typeof loadModalitySettings === "function") {
      await loadModalitySettings(user);
    }
  }

  if (viewName === "degree-work" && typeof loadDegreeWork === "function") {
    await loadDegreeWork(user);
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
    elements.usersTableBody.replaceChildren();
    users.forEach((item) => {
      const permissionCount = item.permissions?.length || 0;
      const row = document.createElement("tr");
      const nameCell = document.createElement("td");
      const name = document.createElement("strong");
      name.textContent = item.name;
      nameCell.append(name);

      const emailCell = document.createElement("td");
      emailCell.textContent = item.email;
      const roleCell = document.createElement("td");
      const role = document.createElement("span");
      role.className = "role-pill";
      role.textContent = item.role;
      roleCell.append(role);
      const statusCell = document.createElement("td");
      const userStatus = document.createElement("span");
      userStatus.className = `status-pill ${item.status === "Inactivo" ? "inactive" : ""}`;
      userStatus.textContent = item.status;
      statusCell.append(userStatus);
      const permissionsCell = document.createElement("td");
      permissionsCell.textContent = permissionCount === allPermissions.length
        ? "Todos"
        : `${permissionCount} permisos`;

      const actionsCell = document.createElement("td");
      const actions = document.createElement("div");
      actions.className = "action-buttons";
      const edit = document.createElement("button");
      edit.className = "table-button";
      edit.type = "button";
      edit.dataset.edit = item.id;
      edit.disabled = !canUpdate;
      edit.textContent = "Editar";
      const remove = document.createElement("button");
      remove.className = "table-button danger";
      remove.type = "button";
      remove.dataset.delete = item.id;
      remove.disabled = !canDelete || item.role === "Super administrador";
      remove.textContent = "Eliminar";
      actions.append(edit, remove);
      actionsCell.append(actions);
      row.append(
        nameCell,
        emailCell,
        roleCell,
        statusCell,
        permissionsCell,
        actionsCell,
      );
      elements.usersTableBody.append(row);
    });
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
    alert("Define una contraseña inicial para crear el usuario.");
    elements.userPassword.focus();
    return;
  }

  try {
    const response = await apiFetch(
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
    showLauncher();
  });
});

elements.openResearchHub.addEventListener("click", async () => {
  const currentUser = await getSessionUser();
  if (currentUser) {
    showAuthenticatedApp(currentUser);
    return;
  }
  showLogin();
});

function preventDisabledApplicationNavigation(event) {
  if (event.currentTarget.getAttribute("aria-disabled") === "true") {
    event.preventDefault();
  }
}

elements.openResearchOs.addEventListener(
  "click",
  preventDisabledApplicationNavigation,
);
elements.openCris.addEventListener("click", preventDisabledApplicationNavigation);
elements.openCrai.addEventListener("click", preventDisabledApplicationNavigation);
elements.researchBlogLinks.forEach((link) => {
  link.addEventListener("click", preventDisabledApplicationNavigation);
});

let currentOpportunityIndex = 0;
let opportunityTimer = null;
const opportunityAutoplayMs = Number(
  elements.opportunityCarousel.dataset.autoplayMs,
);
const reducedMotion = window.matchMedia("(prefers-reduced-motion: reduce)");

function renderOpportunity(index, announce = false) {
  const slideCount = elements.opportunitySlides.length;
  currentOpportunityIndex = (index + slideCount) % slideCount;

  elements.opportunitySlides.forEach((slide, slideIndex) => {
    const isActive = slideIndex === currentOpportunityIndex;
    const deferredImage = slide.querySelector("img[data-src]");
    if (isActive && deferredImage) {
      deferredImage.src = deferredImage.dataset.src;
      deferredImage.removeAttribute("data-src");
    }
    slide.classList.toggle("is-active", isActive);
    slide.setAttribute("aria-hidden", String(!isActive));
    slide.querySelectorAll("a, button").forEach((control) => {
      control.tabIndex = isActive ? 0 : -1;
    });
  });
  elements.opportunityDots.forEach((dot, dotIndex) => {
    const isActive = dotIndex === currentOpportunityIndex;
    dot.classList.toggle("is-active", isActive);
    if (isActive) dot.setAttribute("aria-current", "true");
    else dot.removeAttribute("aria-current");
  });

  const visibleNumber = String(currentOpportunityIndex + 1).padStart(2, "0");
  elements.opportunityCount.textContent = `${visibleNumber} / 03`;
  if (announce) {
    const heading = elements.opportunitySlides[
      currentOpportunityIndex
    ].querySelector("h3").textContent;
    elements.opportunityStatus.textContent = `${currentOpportunityIndex + 1} de ${slideCount}: ${heading}`;
  }
}

function stopOpportunityRotation() {
  window.clearInterval(opportunityTimer);
  opportunityTimer = null;
}

function scheduleOpportunityRotation() {
  stopOpportunityRotation();
  if (
    reducedMotion.matches ||
    document.hidden ||
    elements.appLauncher.classList.contains("is-hidden")
  ) {
    return;
  }
  opportunityTimer = window.setInterval(() => {
    renderOpportunity(currentOpportunityIndex + 1);
  }, opportunityAutoplayMs);
}

function selectOpportunity(index) {
  renderOpportunity(index, true);
  scheduleOpportunityRotation();
}

elements.opportunityPrev.addEventListener("click", () => {
  selectOpportunity(currentOpportunityIndex - 1);
});
elements.opportunityNext.addEventListener("click", () => {
  selectOpportunity(currentOpportunityIndex + 1);
});
elements.opportunityDots.forEach((dot) => {
  dot.addEventListener("click", () => {
    selectOpportunity(Number(dot.dataset.opportunityIndex));
  });
});
elements.opportunityCarousel.addEventListener("mouseenter", stopOpportunityRotation);
elements.opportunityCarousel.addEventListener("mouseleave", scheduleOpportunityRotation);
elements.opportunityCarousel.addEventListener("focusin", stopOpportunityRotation);
elements.opportunityCarousel.addEventListener("focusout", (event) => {
  if (!elements.opportunityCarousel.contains(event.relatedTarget)) {
    scheduleOpportunityRotation();
  }
});
document.addEventListener("visibilitychange", scheduleOpportunityRotation);
reducedMotion.addEventListener("change", scheduleOpportunityRotation);
renderOpportunity(0);

elements.launcherBack.addEventListener("click", showLauncher);
elements.navItems.forEach((item) => {
  item.addEventListener("click", (event) => {
    event.preventDefault();
    showView(item.dataset.view, item);
    if (window.matchMedia("(max-width: 860px)").matches) {
      setNavigationOpen(false);
    }
  });
});
elements.mobileMenuButton.addEventListener("click", () => {
  setNavigationOpen(!elements.sidebar.classList.contains("is-open"));
});
elements.sidebarBackdrop.addEventListener("click", () => {
  setNavigationOpen(false);
});
document.addEventListener("keydown", (event) => {
  if (event.key === "Escape" && elements.sidebar.classList.contains("is-open")) {
    setNavigationOpen(false);
    elements.mobileMenuButton.focus();
  }
});
window.addEventListener("resize", () => {
  if (!window.matchMedia("(max-width: 860px)").matches) {
    setNavigationOpen(false);
  }
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
    apiFetch(`/api/v1/usuarios/${deleteId}`, { method: "DELETE" }).then((response) => {
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

async function initializeApp() {
  try {
    const response = await fetch("/api/v1/meta");
    const metadata = response.ok ? await response.json() : null;
    elements.registerAccess.classList.toggle(
      "is-hidden",
      !metadata?.features?.self_registration,
    );
    configureExternalApplication(
      metadata?.applications?.research_os,
      elements.openResearchOs,
      elements.researchOsActionLabel,
      "Ingresar a ResearchOS",
    );
    configureExternalApplication(
      metadata?.applications?.cris,
      elements.openCris,
      elements.crisActionLabel,
      "Ingresar a CRIS",
    );
    configureExternalApplication(
      metadata?.applications?.crai,
      elements.openCrai,
      elements.craiActionLabel,
      "Ingresar al CRAI",
    );
    elements.researchBlogLinks.forEach((link) => {
      configureExternalApplication(
        metadata?.links?.research_blog,
        link,
        link.querySelector(".opportunity-link-label"),
        "Leer en el blog",
      );
    });
  } catch (error) {
    elements.registerAccess.classList.add("is-hidden");
  }
  showLauncher();
}

function configureExternalApplication(application, link, label, enabledLabel) {
  if (!application?.available || !application.url) return;

  link.href = application.url;
  link.setAttribute("aria-disabled", "false");
  link.classList.remove("is-disabled");
  label.textContent = enabledLabel;
}

initializeApp();
