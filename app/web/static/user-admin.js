// Administracion de usuarios compartida por ResearchHUB y ResearchOS.
// Ambas paginas exponen el mismo marcado (#users-table-body, #user-form, ...).
// El backend aplica permisos y accesos; esta vista solo refleja lo permitido.

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

const applicationNames = {
  research_hub: "ResearchHUB",
  research_os: "ResearchOS",
};

function userHasPermission(user, permission) {
  return user?.permissions?.includes(permission) || user?.role === "Super administrador";
}

const userAdmin = (() => {
  const el = {
    tableBody: document.querySelector("#users-table-body"),
    form: document.querySelector("#user-form"),
    formTitle: document.querySelector("#user-form-title"),
    id: document.querySelector("#user-id"),
    name: document.querySelector("#user-name"),
    email: document.querySelector("#user-email"),
    role: document.querySelector("#user-role"),
    status: document.querySelector("#user-status"),
    password: document.querySelector("#user-password"),
    newButton: document.querySelector("#new-user-button"),
    cancelButton: document.querySelector("#cancel-user-button"),
    message: document.querySelector("#user-admin-status"),
  };

  let cachedUsers = [];
  let options = null;

  function setMessage(text, kind = "info") {
    if (!el.message) return;
    el.message.textContent = text;
    el.message.dataset.kind = kind;
  }

  async function readErrorMessage(response, fallback) {
    try {
      const payload = await response.json();
      return payload.error?.message || fallback;
    } catch (error) {
      return fallback;
    }
  }

  function selectedValues(name) {
    return Array.from(document.querySelectorAll(`input[name="${name}"]:checked`)).map(
      (checkbox) => checkbox.value,
    );
  }

  function cell(content) {
    const td = document.createElement("td");
    if (content instanceof Node) {
      td.append(content);
    } else {
      td.textContent = content;
    }
    return td;
  }

  function pill(className, text) {
    const span = document.createElement("span");
    span.className = className;
    span.textContent = text;
    return span;
  }

  function actionButton(label, className, dataset, disabled) {
    const button = document.createElement("button");
    button.className = className;
    button.type = "button";
    button.disabled = disabled;
    button.textContent = label;
    Object.assign(button.dataset, dataset);
    return button;
  }

  function renderRows(users, currentUser) {
    const canUpdate = userHasPermission(currentUser, "users:update");
    const canDelete = userHasPermission(currentUser, "users:delete");
    el.tableBody.replaceChildren();

    if (!users.length) {
      const row = document.createElement("tr");
      const empty = cell("Aún no hay usuarios registrados.");
      empty.colSpan = 7;
      row.append(empty);
      el.tableBody.append(row);
      return;
    }

    users.forEach((item) => {
      const permissionCount = item.permissions?.length || 0;
      const name = document.createElement("strong");
      name.textContent = item.name;
      const actions = document.createElement("div");
      actions.className = "action-buttons";
      actions.append(
        actionButton("Editar", "table-button", { edit: item.id }, !canUpdate),
        actionButton(
          "Eliminar",
          "table-button danger",
          { delete: item.id },
          !canDelete || item.role === "Super administrador",
        ),
      );

      const row = document.createElement("tr");
      row.append(
        cell(name),
        cell(item.email),
        cell(pill("role-pill", item.role)),
        cell(pill(`status-pill ${item.status === "Inactivo" ? "inactive" : ""}`, item.status)),
        cell(
          (item.applications || [])
            .map((code) => applicationNames[code] || code)
            .join(", ") || "Sin acceso",
        ),
        cell(
          permissionCount === allPermissions.length ? "Todos" : `${permissionCount} permisos`,
        ),
        cell(actions),
      );
      el.tableBody.append(row);
    });
  }

  async function render() {
    el.tableBody.innerHTML = '<tr><td colspan="7">Cargando usuarios…</td></tr>';
    try {
      const [currentUser, response] = await Promise.all([
        options.getCurrentUser(),
        options.apiFetch("/api/v1/usuarios"),
      ]);
      if (!response.ok) {
        throw new Error(await readErrorMessage(response, "No fue posible consultar los usuarios."));
      }
      cachedUsers = await response.json();
      renderRows(cachedUsers, currentUser);
    } catch (error) {
      el.tableBody.innerHTML = "";
      const row = document.createElement("tr");
      const failed = cell(error.message || "No fue posible consultar los usuarios.");
      failed.colSpan = 7;
      row.append(failed);
      el.tableBody.append(row);
    }
  }

  function reset() {
    el.form.reset();
    el.id.value = "";
    el.formTitle.textContent = "Nuevo usuario";
  }

  function fill(user) {
    el.id.value = user.id;
    el.name.value = user.name;
    el.email.value = user.email;
    el.role.value = user.role;
    el.status.value = user.status;
    el.password.value = "";
    document.querySelectorAll('input[name="permission"]').forEach((checkbox) => {
      checkbox.checked = user.permissions.includes(checkbox.value);
    });
    document.querySelectorAll('input[name="application"]').forEach((checkbox) => {
      checkbox.checked = (user.applications || []).includes(checkbox.value);
    });
    el.formTitle.textContent = "Editar usuario";
    setMessage("");
    el.name.focus();
  }

  async function save(event) {
    event.preventDefault();
    const editingId = el.id.value;
    const role = el.role.value;
    const payload = {
      name: el.name.value.trim(),
      email: el.email.value.trim().toLowerCase(),
      role,
      status: el.status.value,
      password: el.password.value || null,
      permissions:
        role === "Super administrador" ? [...allPermissions] : selectedValues("permission"),
      applications: selectedValues("application"),
    };

    if (!editingId && !payload.password) {
      setMessage("Define una contraseña inicial para crear el usuario.", "error");
      el.password.focus();
      return;
    }

    try {
      const response = await options.apiFetch(
        editingId ? `/api/v1/usuarios/${editingId}` : "/api/v1/usuarios",
        {
          method: editingId ? "PUT" : "POST",
          body: JSON.stringify(payload),
        },
      );
      if (!response.ok) {
        setMessage(
          await readErrorMessage(response, "No fue posible guardar el usuario."),
          "error",
        );
        return;
      }
      setMessage(editingId ? "Usuario actualizado." : "Usuario creado.", "success");
      reset();
      await render();
    } catch (error) {
      setMessage("No fue posible conectar con el servidor.", "error");
    }
  }

  async function remove(user) {
    const confirmed = window.confirm(
      `¿Eliminar a ${user.name} (${user.email})? Esta acción no se puede deshacer.`,
    );
    if (!confirmed) return;
    try {
      const response = await options.apiFetch(`/api/v1/usuarios/${user.id}`, {
        method: "DELETE",
      });
      if (!response.ok) {
        setMessage(
          await readErrorMessage(response, "No fue posible eliminar el usuario."),
          "error",
        );
        return;
      }
      setMessage("Usuario eliminado.", "success");
      if (el.id.value === user.id) reset();
      await render();
    } catch (error) {
      setMessage("No fue posible conectar con el servidor.", "error");
    }
  }

  function init(config) {
    options = config;
    el.newButton.addEventListener("click", () => {
      reset();
      setMessage("");
      el.name.focus();
    });
    el.cancelButton.addEventListener("click", () => {
      reset();
      setMessage("");
    });
    el.form.addEventListener("submit", save);
    el.role.addEventListener("change", () => {
      if (el.role.value === "Super administrador") {
        document.querySelectorAll('input[name="permission"]').forEach((checkbox) => {
          checkbox.checked = true;
        });
      }
    });
    el.tableBody.addEventListener("click", (event) => {
      const button = event.target.closest("button");
      if (!button) return;
      const user = cachedUsers.find(
        (item) => item.id === (button.dataset.edit || button.dataset.delete),
      );
      if (!user) return;
      if (button.dataset.edit) fill(user);
      if (button.dataset.delete) remove(user);
    });
  }

  return { init, render, reset };
})();
