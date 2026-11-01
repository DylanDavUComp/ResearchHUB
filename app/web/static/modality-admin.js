// Catalogo de modalidades y flujos de trabajo de grado. Vive en la consola de
// configuracion general; el backend solo acepta estas operaciones de un
// superadministrador.

const modalityStatusCopy = {
  DRAFT: "Borrador",
  ACTIVE: "Activa",
  INACTIVE: "Inactiva",
  RETIRED: "Retirada",
};

const modalityAdminState = { user: null, items: [] };

const modalityAdminElements = {
  modalitySettingsBody: document.querySelector("#modality-settings-body"),
  newModalityButton: document.querySelector("#new-modality-button"),
  modalityDialog: document.querySelector("#modality-dialog"),
  modalityForm: document.querySelector("#modality-form"),
  modalityFormTitle: document.querySelector("#modality-form-title"),
  modalityId: document.querySelector("#modality-id"),
  modalityCode: document.querySelector("#modality-code"),
  modalityName: document.querySelector("#modality-name"),
  modalityDescription: document.querySelector("#modality-description"),
  modalitySemester: document.querySelector("#modality-semester"),
  modalityDuration: document.querySelector("#modality-duration"),
  modalityMinParticipants: document.querySelector("#modality-min-participants"),
  modalityMaxParticipants: document.querySelector("#modality-max-participants"),
  modalityHomologatable: document.querySelector("#modality-homologatable"),
  workflowStepList: document.querySelector("#workflow-step-list"),
  addWorkflowStep: document.querySelector("#add-workflow-step"),
  modalityFormMessage: document.querySelector("#modality-form-message"),
  cancelModalityForm: document.querySelector("#cancel-modality-form"),
};

function modalityNode(tag, className, text) {
  const node = document.createElement(tag);
  if (className) node.className = className;
  if (text !== undefined) node.textContent = text;
  return node;
}

async function modalityAdminJson(url, options = {}) {
  const response = await apiFetch(url, options);
  if (!response.ok) {
    let message = "No fue posible completar la operación.";
    try {
      const payload = await response.json();
      message = payload.error?.message || payload.detail?.[0]?.msg || message;
    } catch (error) {
      message = "El servidor devolvió una respuesta no válida.";
    }
    throw new Error(message);
  }
  if (response.status === 204) return null;
  return response.json();
}

async function loadModalitySettings(user) {
  if (user?.role !== "Super administrador") return;
  modalityAdminState.user = user;
  try {
    modalityAdminState.items = await modalityAdminJson("/api/v1/degree-work-modalities?include_inactive=true");
    renderModalitySettings();
  } catch (error) {
    modalityAdminElements.modalitySettingsBody.replaceChildren();
    const row = document.createElement("tr");
    const cell = modalityNode("td", "", error.message);
    cell.colSpan = 7;
    row.append(cell);
    modalityAdminElements.modalitySettingsBody.append(row);
  }
}

function renderModalitySettings() {
  modalityAdminElements.modalitySettingsBody.replaceChildren();
  modalityAdminState.items.forEach((modality) => {
    const row = document.createElement("tr");
    const name = modalityNode("td");
    name.append(modalityNode("strong", "", modality.name), modalityNode("small", "table-secondary", modality.code));
    const statusCell = modalityNode("td");
    statusCell.append(modalityNode("span", `status-pill status-${modality.status.toLowerCase()}`, modalityStatusCopy[modality.status] || modality.status));
    const actions = modalityNode("td");
    const actionWrap = modalityNode("div", "action-buttons");
    if (modality.status === "DRAFT") {
      actionWrap.append(modalityActionButton("Editar", () => openModalityDialog(modality)));
      actionWrap.append(modalityActionButton("Eliminar", () => deleteModality(modality), "danger"));
      actionWrap.append(modalityActionButton("Publicar", () => changeModalityState(modality, "publication")));
    }
    if (modality.status === "ACTIVE") actionWrap.append(modalityActionButton("Retirar", () => changeModalityState(modality, "retirement"), "danger"));
    actions.append(actionWrap);
    row.append(name, modalityNode("td", "", String(modality.version)), modalityNode("td", "", modality.is_homologatable ? "Si" : "No"), modalityNode("td", "", `${modality.min_participants} - ${modality.max_participants}`), modalityNode("td", "", `${modality.workflow_steps.length} pasos`), statusCell, actions);
    modalityAdminElements.modalitySettingsBody.append(row);
  });
}

function modalityActionButton(label, action, variant = "") {
  const button = modalityNode("button", `table-button ${variant}`, label);
  button.type = "button";
  button.addEventListener("click", action);
  return button;
}

function addWorkflowStepRow(data = {}) {
  const row = modalityNode("div", "workflow-step-row");
  const code = document.createElement("input");
  code.className = "workflow-code";
  code.placeholder = "CODIGO_PASO";
  code.required = true;
  code.value = data.code || "";
  const name = document.createElement("input");
  name.className = "workflow-name";
  name.placeholder = "Nombre visible";
  name.required = true;
  name.value = data.name || "";
  const type = document.createElement("select");
  type.className = "workflow-type";
  ["FORM", "DOCUMENT", "VALIDATION", "APPROVAL", "ASSIGNMENT", "ACTIVITY", "EVALUATION", "REGISTRATION", "CLOSURE"].forEach((value) => {
    const option = modalityNode("option", "", value);
    option.value = value;
    option.selected = value === data.step_type;
    type.append(option);
  });
  const role = document.createElement("select");
  role.className = "workflow-role";
  ["Estudiante", "Docente", "Director de programa", "Administrador", "Super administrador"].forEach((value) => {
    const option = modalityNode("option", "", value);
    option.value = value;
    option.selected = data.responsible_roles?.includes(value);
    role.append(option);
  });
  const remove = modalityNode("button", "icon-action danger-icon", "×");
  remove.type = "button";
  remove.title = "Eliminar paso";
  remove.setAttribute("aria-label", "Eliminar paso");
  remove.addEventListener("click", () => row.remove());
  row.append(code, name, type, role, remove);
  modalityAdminElements.workflowStepList.append(row);
}

function openModalityDialog(modality = null) {
  modalityAdminElements.modalityForm.reset();
  modalityAdminElements.workflowStepList.replaceChildren();
  modalityAdminElements.modalityFormMessage.textContent = "";
  modalityAdminElements.modalityId.value = modality?.id || "";
  modalityAdminElements.modalityCode.value = modality?.code || "";
  modalityAdminElements.modalityCode.disabled = Boolean(modality);
  modalityAdminElements.modalityName.value = modality?.name || "";
  modalityAdminElements.modalityDescription.value = modality?.description || "";
  modalityAdminElements.modalitySemester.value = modality?.initial_semester || "";
  modalityAdminElements.modalityDuration.value = modality?.duration_label || "Por definir";
  modalityAdminElements.modalityMinParticipants.value = modality?.min_participants || 1;
  modalityAdminElements.modalityMaxParticipants.value = modality?.max_participants || 1;
  modalityAdminElements.modalityHomologatable.checked = modality?.is_homologatable || false;
  modalityAdminElements.modalityFormTitle.textContent = modality ? "Editar modalidad" : "Nueva modalidad";
  const steps = modality?.workflow_steps || [
    { code: "APPLICATION", name: "Postulacion", step_type: "FORM", responsible_roles: ["Estudiante"] },
    { code: "CLOSURE", name: "Cierre", step_type: "CLOSURE", responsible_roles: ["Director de programa"] },
  ];
  steps.forEach(addWorkflowStepRow);
  modalityAdminElements.modalityDialog.showModal();
}

function collectWorkflowSteps() {
  return Array.from(modalityAdminElements.workflowStepList.querySelectorAll(".workflow-step-row")).map((row) => ({
    code: row.querySelector(".workflow-code").value.trim().toUpperCase().replaceAll(" ", "_"),
    name: row.querySelector(".workflow-name").value.trim(),
    step_type: row.querySelector(".workflow-type").value,
    responsible_roles: [row.querySelector(".workflow-role").value],
    is_decision: row.querySelector(".workflow-type").value === "APPROVAL",
  }));
}

async function saveModality(event) {
  event.preventDefault();
  const id = modalityAdminElements.modalityId.value;
  const payload = {
    name: modalityAdminElements.modalityName.value.trim(),
    description: modalityAdminElements.modalityDescription.value.trim(),
    is_homologatable: modalityAdminElements.modalityHomologatable.checked,
    initial_semester: modalityAdminElements.modalitySemester.value ? Number(modalityAdminElements.modalitySemester.value) : null,
    duration_label: modalityAdminElements.modalityDuration.value.trim() || "Por definir",
    min_participants: Number(modalityAdminElements.modalityMinParticipants.value),
    max_participants: Number(modalityAdminElements.modalityMaxParticipants.value),
    requirements: [],
    evaluation_criteria: [],
    workflow_steps: collectWorkflowSteps(),
  };
  if (!id) payload.code = modalityAdminElements.modalityCode.value.trim().toUpperCase();
  modalityAdminElements.modalityFormMessage.textContent = "Guardando borrador...";
  try {
    await modalityAdminJson(id ? `/api/v1/degree-work-modalities/${id}` : "/api/v1/degree-work-modalities", {
      method: id ? "PATCH" : "POST",
      body: JSON.stringify(payload),
    });
    modalityAdminElements.modalityDialog.close();
    await loadModalitySettings(modalityAdminState.user);
  } catch (error) {
    modalityAdminElements.modalityFormMessage.textContent = error.message;
  }
}

async function changeModalityState(modality, action) {
  try {
    await modalityAdminJson(`/api/v1/degree-work-modalities/${modality.id}/${action}`, { method: "POST" });
    await loadModalitySettings(modalityAdminState.user);
  } catch (error) {
    window.alert(error.message);
  }
}

async function deleteModality(modality) {
  if (!window.confirm(`Eliminar el borrador "${modality.name}"?`)) return;
  try {
    await modalityAdminJson(`/api/v1/degree-work-modalities/${modality.id}`, { method: "DELETE" });
    await loadModalitySettings(modalityAdminState.user);
  } catch (error) {
    window.alert(error.message);
  }
}

modalityAdminElements.newModalityButton.addEventListener("click", () => openModalityDialog());
modalityAdminElements.cancelModalityForm.addEventListener("click", () => modalityAdminElements.modalityDialog.close());
modalityAdminElements.addWorkflowStep.addEventListener("click", () => addWorkflowStepRow());
modalityAdminElements.modalityForm.addEventListener("submit", saveModality);
