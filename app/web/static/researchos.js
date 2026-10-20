// ResearchOS comparte con ResearchHUB la sesion institucional, guardada en PostgreSQL
// y enviada en una cookie HttpOnly. La sesion prueba identidad; el acceso a ResearchOS
// lo decide el backend en cada solicitud.
const csrfHeader = { name: "X-Requested-With", value: "ResearchHUB" };

const applicationCode = "research_os";

const applicationLinks = {
  research_hub: { name: "ResearchHUB", url: "/", description: "Investigación formativa y trabajos de grado" },
  research_os: { name: "ResearchOS", url: "/researchos", description: "Investigación aplicada y transferencia" },
};

const elements = {
  loading: document.querySelector("#ros-loading"),
  loginView: document.querySelector("#login-view"),
  loginForm: document.querySelector("#login-form"),
  loginEmail: document.querySelector("#login-email"),
  loginPassword: document.querySelector("#login-password"),
  loginSubmit: document.querySelector("#login-submit"),
  loginError: document.querySelector("#login-error"),
  loginAlternative: document.querySelector("#login-alternative"),
  togglePassword: document.querySelector("#toggle-password"),
  accessDenied: document.querySelector("#access-denied"),
  deniedUser: document.querySelector("#denied-user"),
  deniedHubLink: document.querySelector("#denied-hub-link"),
  switchAccount: document.querySelector("#switch-account"),
  appView: document.querySelector("#app-view"),
  sidebar: document.querySelector("#main-sidebar"),
  sidebarBackdrop: document.querySelector("#sidebar-backdrop"),
  mobileMenuButton: document.querySelector("#mobile-menu-button"),
  profileName: document.querySelector("#profile-name"),
  profileRole: document.querySelector("#profile-role"),
  welcomeText: document.querySelector("#welcome-text"),
  navSections: document.querySelector("#nav-sections"),
  sectionList: document.querySelector("#section-list"),
  appList: document.querySelector("#app-list"),
};

async function apiFetch(url, options = {}) {
  const headers = new Headers(options.headers || {});
  headers.set(csrfHeader.name, csrfHeader.value);
  if (options.body && !headers.has("Content-Type")) {
    headers.set("Content-Type", "application/json");
  }
  return fetch(url, { ...options, credentials: "same-origin", headers });
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

function showLogin(message = "", alternativeApplications = []) {
  setNavigationOpen(false);
  showOnly("login");
  elements.loginError.textContent = message;
  const alternative = alternativeApplications.find((code) => code !== applicationCode);
  elements.loginAlternative.classList.toggle("is-hidden", !alternative);
  if (alternative) {
    const link = elements.loginAlternative.querySelector("a");
    link.href = applicationLinks[alternative].url;
    link.textContent = `Ir a ${applicationLinks[alternative].name}`;
  }
}

function showDenied(user) {
  showOnly("denied");
  elements.deniedUser.textContent = user?.email || "tu cuenta";
  elements.deniedHubLink.classList.toggle(
    "is-hidden",
    !user?.applications?.includes("research_hub"),
  );
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

function createStatus(text) {
  const status = document.createElement("span");
  status.className = "ros-status";
  status.textContent = text;
  return status;
}

function renderSections(sections) {
  elements.navSections.replaceChildren();
  elements.sectionList.replaceChildren();

  sections.forEach((section) => {
    const navItem = document.createElement("li");
    const navLabel = document.createElement("span");
    navLabel.className = "nav-item is-disabled";
    navLabel.setAttribute("aria-disabled", "true");
    navLabel.textContent = section.name;
    if (!section.available) {
      navLabel.append(createStatus("Próximamente"));
    }
    navItem.append(navLabel);
    elements.navSections.append(navItem);

    const item = document.createElement("li");
    const copy = document.createElement("div");
    const title = document.createElement("strong");
    title.textContent = section.name;
    const description = document.createElement("p");
    description.textContent = section.description;
    copy.append(title, description);
    item.append(copy, createStatus(section.available ? "Disponible" : "Próximamente"));
    elements.sectionList.append(item);
  });
}

function renderApplications(user) {
  elements.appList.replaceChildren();
  Object.entries(applicationLinks).forEach(([code, application]) => {
    const hasAccess = user.applications?.includes(code);
    const item = document.createElement("li");
    const copy = document.createElement("div");
    const title = document.createElement("strong");
    title.textContent = application.name;
    const description = document.createElement("p");
    description.textContent = application.description;
    copy.append(title, description);
    item.append(copy);

    if (code === applicationCode) {
      item.append(createStatus("Estás aquí"));
    } else if (hasAccess) {
      const link = document.createElement("a");
      link.className = "button secondary";
      link.href = application.url;
      link.textContent = "Abrir";
      link.setAttribute("aria-label", `Abrir ${application.name}`);
      item.append(link);
    } else {
      item.append(createStatus("Sin acceso"));
    }
    elements.appList.append(item);
  });
}

function showWorkspace(workspace) {
  const { user, sections } = workspace;
  elements.profileName.textContent = user.name;
  elements.profileRole.textContent = user.role;
  elements.welcomeText.textContent = `Hola, ${user.name}. Este es tu espacio de investigación aplicada.`;
  renderSections(sections);
  renderApplications(user);
  showOnly("app");
}

async function loadWorkspace() {
  let response;
  try {
    response = await apiFetch("/api/v1/research-os/workspace");
  } catch (error) {
    showLogin("No fue posible conectar con el servidor. Intenta de nuevo.");
    return;
  }

  if (response.ok) {
    showWorkspace(await response.json());
    return;
  }

  if (response.status === 403) {
    const error = await readError(response);
    if (error.code === "auth.application_forbidden") {
      const meResponse = await apiFetch("/api/v1/usuarios/me").catch(() => null);
      showDenied(meResponse?.ok ? await meResponse.json() : null);
      return;
    }
  }

  // 401 o usuario inactivo: no hay una sesion compartida valida.
  showLogin();
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
      body: JSON.stringify({ email, password, application: applicationCode }),
    });

    if (!response.ok) {
      const error = await readError(response);
      if (response.status === 422) {
        showLogin("Revisa el formato del correo y la contraseña.");
      } else {
        showLogin(
          error.message || "No fue posible iniciar sesión.",
          error.details?.applications || [],
        );
      }
      elements.loginPassword.value = "";
      elements.loginPassword.focus();
      return;
    }

    elements.loginPassword.value = "";
    await loadWorkspace();
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
elements.mobileMenuButton.addEventListener("click", () => {
  setNavigationOpen(!elements.sidebar.classList.contains("is-open"));
});
elements.sidebarBackdrop.addEventListener("click", () => setNavigationOpen(false));
document.addEventListener("keydown", (event) => {
  if (event.key === "Escape") {
    setNavigationOpen(false);
  }
});

loadWorkspace();
