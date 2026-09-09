const degreeWorkState = {
  currentUser: null,
  modalities: [],
  settingsModalities: [],
  cases: [],
  selectedCaseId: null,
  selectedModalityCode: null,
  selectedJourneyStage: "OFFER",
};

const degreeWorkElements = {
  heading: document.querySelector("#degree-work-heading"),
  subtitle: document.querySelector("#degree-work-subtitle"),
  modalityCount: document.querySelector("#modality-count"),
  caseCount: document.querySelector("#case-count"),
  activeCaseCount: document.querySelector("#active-case-count"),
  closedCaseCount: document.querySelector("#closed-case-count"),
  journeyContext: document.querySelector("#journey-context"),
  journeyStages: document.querySelectorAll(".journey-stage"),
  journeyStepNumber: document.querySelector("#journey-step-number"),
  journeyStepTitle: document.querySelector("#journey-step-title"),
  journeyStepDescription: document.querySelector("#journey-step-description"),
  journeyConfiguredSteps: document.querySelector("#journey-configured-steps"),
  catalog: document.querySelector("#modality-catalog"),
  search: document.querySelector("#modality-search"),
  casesBody: document.querySelector("#degree-work-cases-body"),
  inboxTitle: document.querySelector("#case-inbox-title"),
  inboxDescription: document.querySelector("#case-inbox-description"),
  refresh: document.querySelector("#refresh-degree-work"),
  caseEmpty: document.querySelector("#case-empty"),
  caseDetail: document.querySelector("#case-detail"),
  caseDetailStatus: document.querySelector("#case-detail-status"),
  caseDetailTitle: document.querySelector("#case-detail-title"),
  caseDetailMeta: document.querySelector("#case-detail-meta"),
  caseProgressValue: document.querySelector("#case-progress-value"),
  caseProgressBar: document.querySelector("#case-progress-bar"),
  caseSteps: document.querySelector("#case-steps"),
  caseActions: document.querySelector("#case-actions"),
  caseHistory: document.querySelector("#case-history"),
  openCaseForm: document.querySelector("#open-case-form"),
  caseDialog: document.querySelector("#case-dialog"),
  caseForm: document.querySelector("#degree-work-case-form"),
  caseModality: document.querySelector("#case-modality"),
  caseTitle: document.querySelector("#case-title"),
  caseProgram: document.querySelector("#case-program"),
  caseFormMessage: document.querySelector("#case-form-message"),
  cancelCaseForm: document.querySelector("#cancel-case-form"),
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

const roleCopy = {
  Estudiante: ["Mi trabajo de grado", "Selecciona una modalidad y consulta el siguiente paso de tu proceso.", "Mis solicitudes"],
  Docente: ["Bandeja docente", "Revisa los casos asignados y registra las acciones de tu etapa.", "Casos asignados"],
  "Director de programa": ["Control del programa", "Gestiona avales, asignaciones, decisiones y registros finales.", "Casos del programa"],
  Administrador: ["Operacion institucional", "Consulta procesos y administra la configuracion operativa.", "Casos institucionales"],
  "Super administrador": ["Gobierno de trabajos de grado", "Supervisa procesos, modalidades, flujos y trazabilidad.", "Todos los casos"],
};

const statusCopy = {
  DRAFT: "Borrador",
  ACTIVE: "Activa",
  INACTIVE: "Inactiva",
  RETIRED: "Retirada",
  IN_PROGRESS: "En proceso",
  REQUIRES_CHANGES: "Requiere ajustes",
  REJECTED: "Rechazada",
  CLOSED: "Cerrada",
};

const journeyStages = [
  ["OFFER", "Oferta de modalidades", "Consulta las alternativas habilitadas y selecciona la que corresponde a tu proyecto."],
  ["ELIGIBILITY", "Validacion de elegibilidad", "Verifica semestre, requisitos academicos y condiciones particulares de la modalidad."],
  ["APPLICATION", "Postulacion y documentos", "Radica la solicitud y entrega los documentos exigidos para iniciar el proceso."],
  ["VALIDATION", "Validacion academica", "El programa revisa requisitos, integridad documental y condiciones de participacion."],
  ["FORMALIZATION", "Formalizacion y asignaciones", "Se registran avales, decisiones de comite y asignaciones de tutor o evaluador."],
  ["EXECUTION", "Ejecucion y seguimiento", "Desarrolla el trabajo con acompanamiento, entregas parciales y correcciones."],
  ["EVALUATION", "Evaluacion del resultado", "Los responsables aplican la rubrica vigente y registran sus conceptos."],
  ["REGISTRATION", "Homologacion o registro", "Se consolida la calificacion y se transfiere el resultado al registro correspondiente."],
  ["CLOSURE", "Cierre y trazabilidad", "Finaliza el caso conservando decisiones, responsables, documentos e historial."],
];

function clearElement(element) {
  element.replaceChildren();
}

function createNode(tag, className, text) {
  const node = document.createElement(tag);
  if (className) node.className = className;
  if (text !== undefined) node.textContent = text;
  return node;
}

async function degreeWorkJson(url, options = {}) {
  const response = await apiFetch(url, options);
  if (!response.ok) {
    let message = "No fue posible completar la operacion.";
    try {
      const payload = await response.json();
      message = payload.error?.message || payload.detail?.[0]?.msg || message;
    } catch (error) {
      message = "El servidor devolvio una respuesta no valida.";
    }
    throw new Error(message);
  }
  if (response.status === 204) return null;
  return response.json();
}

async function loadDegreeWork(user) {
  degreeWorkState.currentUser = user;
  const copy = roleCopy[user.role] || roleCopy.Estudiante;
  degreeWorkElements.heading.textContent = copy[0];
  degreeWorkElements.subtitle.textContent = copy[1];
  degreeWorkElements.inboxTitle.textContent = copy[2];
  degreeWorkElements.inboxDescription.textContent = "Procesos disponibles de acuerdo con tus permisos y asignaciones.";
  degreeWorkElements.catalog.setAttribute("aria-busy", "true");

  try {
    const [modalities, casePayload] = await Promise.all([
      degreeWorkJson("/api/v1/degree-work-modalities"),
      degreeWorkJson("/api/v1/degree-work-cases?page=1&page_size=100"),
    ]);
    degreeWorkState.modalities = modalities;
    degreeWorkState.cases = casePayload.data;
    degreeWorkElements.modalityCount.textContent = String(modalities.length);
    degreeWorkElements.caseCount.textContent = String(casePayload.total_items);
    degreeWorkElements.activeCaseCount.textContent = String(
      degreeWorkState.cases.filter((item) => !["CLOSED", "REJECTED"].includes(item.status)).length,
    );
    degreeWorkElements.closedCaseCount.textContent = String(
      degreeWorkState.cases.filter((item) => item.status === "CLOSED").length,
    );
    renderModalityCatalog();
    renderDegreeWorkCases();
    const selected = degreeWorkState.cases.find((item) => item.id === degreeWorkState.selectedCaseId)
      || degreeWorkState.cases[0];
    renderCaseDetail(selected || null);
  } catch (error) {
    renderDegreeWorkError(error.message);
  } finally {
    degreeWorkElements.catalog.removeAttribute("aria-busy");
  }
}

function renderDegreeWorkError(message) {
  clearElement(degreeWorkElements.catalog);
  degreeWorkElements.catalog.append(createNode("p", "empty-state error-state", message));
  clearElement(degreeWorkElements.casesBody);
  const row = document.createElement("tr");
  const cell = createNode("td", "", message);
  cell.colSpan = 7;
  row.append(cell);
  degreeWorkElements.casesBody.append(row);
}

function renderModalityCatalog() {
  clearElement(degreeWorkElements.catalog);
  const query = degreeWorkElements.search.value.trim().toLocaleLowerCase("es");
  const items = degreeWorkState.modalities.filter((modality) => {
    const searchable = `${modality.name} ${modality.description} ${modality.requirements.map((item) => item.name || "").join(" ")}`.toLocaleLowerCase("es");
    return searchable.includes(query);
  });
  if (!items.length) {
    degreeWorkElements.catalog.append(createNode("p", "empty-state", "No hay modalidades que coincidan con la busqueda."));
    return;
  }
  items.forEach((modality) => {
    const card = createNode("article", "modality-item");
    const heading = createNode("div", "modality-item-heading");
    const titleWrap = createNode("div");
    titleWrap.append(createNode("span", "modality-code", modality.code.replaceAll("_", " ")));
    titleWrap.append(createNode("h4", "", modality.name));
    heading.append(titleWrap, createNode("span", `homologation-tag ${modality.is_homologatable ? "yes" : "no"}`, modality.is_homologatable ? "Homologable" : "Registro directo"));
    const details = createNode("dl", "modality-facts");
    [["Inicio", modality.initial_semester ? `Semestre ${modality.initial_semester}` : "Por definir"], ["Duracion", modality.duration_label], ["Equipo", `${modality.min_participants} a ${modality.max_participants}`], ["Etapas", String(modality.workflow_steps.length)]].forEach(([label, value]) => {
      details.append(createNode("dt", "", label), createNode("dd", "", value));
    });
    const footer = createNode("div", "modality-item-footer");
    const requirement = modality.requirements[0]?.name || "Consulta los requisitos de la modalidad";
    const actions = createNode("div", "modality-item-actions");
    const inspect = createNode("button", "table-button", "Ver paso a paso");
    inspect.type = "button";
    inspect.addEventListener("click", () => {
      degreeWorkState.selectedModalityCode = modality.code;
      degreeWorkState.selectedCaseId = null;
      degreeWorkState.selectedJourneyStage = "OFFER";
      renderCaseDetail(null);
      document.querySelector("#degree-work-journey").scrollIntoView({ behavior: "smooth", block: "start" });
    });
    actions.append(inspect);
    if (degreeWorkState.currentUser?.role === "Estudiante") {
      const button = createNode("button", "button secondary compact-button", "Seleccionar");
      button.type = "button";
      button.addEventListener("click", () => openCaseDialog(modality.code));
      actions.append(button);
    }
    footer.append(createNode("p", "", requirement), actions);
    card.append(heading, createNode("p", "modality-description", modality.description), details, footer);
    degreeWorkElements.catalog.append(card);
  });
}

function renderDegreeWorkCases() {
  clearElement(degreeWorkElements.casesBody);
  if (!degreeWorkState.cases.length) {
    const row = document.createElement("tr");
    const cell = createNode("td", "", "No hay procesos disponibles para este rol.");
    cell.colSpan = 7;
    row.append(cell);
    degreeWorkElements.casesBody.append(row);
    return;
  }
  degreeWorkState.cases.forEach((item) => {
    const row = document.createElement("tr");
    const title = createNode("td");
    title.append(createNode("strong", "", item.title), createNode("small", "table-secondary", item.id.slice(0, 8).toUpperCase()));
    const status = createNode("span", `status-pill status-${item.status.toLowerCase()}`, statusCopy[item.status] || item.status);
    const progress = createNode("div", "table-progress");
    const progressTrack = createNode("span");
    const progressValue = createNode("i");
    progressValue.style.width = `${item.progress_percent}%`;
    progressTrack.append(progressValue);
    progress.append(progressTrack, createNode("b", "", `${item.progress_percent}%`));
    const actionCell = createNode("td");
    const action = createNode("button", "table-button", "Ver");
    action.type = "button";
    action.addEventListener("click", () => {
      degreeWorkState.selectedCaseId = item.id;
      renderCaseDetail(item);
    });
    actionCell.append(action);
    row.append(title, createNode("td", "", item.modality_name), createNode("td", "", item.program), createNode("td", "", item.current_step?.name || "Proceso finalizado"), createNode("td"), createNode("td"), actionCell);
    row.children[4].append(status);
    row.children[5].append(progress);
    degreeWorkElements.casesBody.append(row);
  });
}

function renderCaseDetail(item) {
  degreeWorkElements.caseEmpty.classList.toggle("is-hidden", Boolean(item));
  degreeWorkElements.caseDetail.classList.toggle("is-hidden", !item);
  if (!item) {
    const modality = degreeWorkState.modalities.find(
      (entry) => entry.code === degreeWorkState.selectedModalityCode,
    ) || degreeWorkState.modalities[0];
    renderJourney(modality || null, null);
    return;
  }
  degreeWorkState.selectedCaseId = item.id;
  degreeWorkState.selectedModalityCode = item.modality_code;
  degreeWorkElements.caseDetailStatus.textContent = statusCopy[item.status] || item.status;
  degreeWorkElements.caseDetailStatus.className = `status-pill status-${item.status.toLowerCase()}`;
  degreeWorkElements.caseDetailTitle.textContent = item.title;
  degreeWorkElements.caseDetailMeta.textContent = `${item.modality_name} · ${item.program} · Version ${item.modality_version}`;
  degreeWorkElements.caseProgressValue.textContent = `${item.progress_percent}%`;
  degreeWorkElements.caseProgressBar.style.width = `${item.progress_percent}%`;
  clearElement(degreeWorkElements.caseSteps);
  item.workflow_snapshot.forEach((workflowStep, index) => {
    const state = index < item.current_step_index ? "done" : index === item.current_step_index ? "current" : "pending";
    const row = createNode("li", state);
    row.append(createNode("span", "step-marker", state === "done" ? "✓" : String(index + 1)));
    const copy = createNode("div");
    copy.append(createNode("strong", "", workflowStep.name), createNode("small", "", workflowStep.responsible_roles.join(" · ")));
    row.append(copy);
    degreeWorkElements.caseSteps.append(row);
  });
  renderCaseActions(item);
  clearElement(degreeWorkElements.caseHistory);
  const history = [...item.history].reverse().slice(0, 5);
  if (!history.length) degreeWorkElements.caseHistory.append(createNode("li", "empty-history", "Aun no se han registrado movimientos."));
  history.forEach((event) => {
    const row = createNode("li");
    row.append(createNode("strong", "", event.action), createNode("span", "", `${event.actor_role} · ${event.step_code}`), createNode("small", "", event.comment || "Sin observacion"));
    degreeWorkElements.caseHistory.append(row);
  });
  const modality = degreeWorkState.modalities.find(
    (entry) => entry.code === item.modality_code,
  );
  degreeWorkState.selectedJourneyStage = journeyStageForStep(item.current_step);
  renderJourney(modality || null, item);
}

function journeyStageForStep(step) {
  if (!step) return "CLOSURE";
  const code = step.code || "";
  if (code === "SELECTION") return "OFFER";
  if (code.includes("ELIGIBILITY")) return "ELIGIBILITY";
  if (["APPLICATION", "DOCUMENT"].includes(code) || step.step_type === "DOCUMENT") return "APPLICATION";
  if (code.includes("REVIEW") || step.step_type === "VALIDATION") return "VALIDATION";
  if (["FACULTY_APPROVAL", "GENERAL_APPROVAL", "AGREEMENT", "ASSIGNMENT"].includes(code)
    || ["APPROVAL", "ASSIGNMENT"].includes(step.step_type)) return "FORMALIZATION";
  if (step.step_type === "ACTIVITY" || code === "EXECUTION") return "EXECUTION";
  if (["EVALUATION", "CALCULATION"].includes(step.step_type)) return "EVALUATION";
  if (["REGISTRATION", "HOMOLOGATION"].includes(code) || step.step_type === "REGISTRATION") return "REGISTRATION";
  return code === "CLOSURE" || step.step_type === "CLOSURE" ? "CLOSURE" : "APPLICATION";
}

function journeyStepsForStage(modality, item, stageCode) {
  const workflow = item?.workflow_snapshot || modality?.workflow_steps || [];
  const configured = workflow
    .map((step, index) => ({ ...step, workflowIndex: index }))
    .filter((step) => journeyStageForStep(step) === stageCode);
  if (stageCode === "OFFER" && !configured.length && modality) {
    return [{
      name: "Consulta y seleccion de modalidad",
      responsible_roles: ["Estudiante"],
      workflowIndex: -1,
      requirement: true,
    }];
  }
  if (stageCode === "ELIGIBILITY" && !configured.length && modality?.requirements?.length) {
    return modality.requirements.map((requirement, index) => ({
      name: requirement.name,
      responsible_roles: ["Estudiante"],
      workflowIndex: index,
      requirement: true,
    }));
  }
  return configured;
}

function renderJourney(modality, item) {
  const selectedCode = degreeWorkState.selectedJourneyStage;
  const currentCode = item ? journeyStageForStep(item.current_step) : selectedCode;
  degreeWorkElements.journeyContext.textContent = item
    ? `${item.title} · ${item.modality_name}`
    : modality
      ? `${modality.name} · Version ${modality.version}`
      : "Selecciona una modalidad para consultar su recorrido.";

  degreeWorkElements.journeyStages.forEach((button) => {
    const code = button.dataset.stage;
    const steps = journeyStepsForStage(modality, item, code);
    const stepIndexes = steps.filter((step) => !step.requirement).map((step) => step.workflowIndex);
    const completed = Boolean(item && stepIndexes.length
      && stepIndexes.every((index) => index < item.current_step_index));
    button.classList.toggle("selected", code === selectedCode);
    button.classList.toggle("actual", Boolean(item) && code === currentCode);
    button.classList.toggle("complete", completed);
    button.classList.toggle("not-required", !steps.length);
    button.setAttribute("aria-pressed", String(code === selectedCode));
  });

  const stageIndex = journeyStages.findIndex(([code]) => code === selectedCode);
  const [, title, description] = journeyStages[stageIndex];
  degreeWorkElements.journeyStepNumber.textContent = `Etapa ${stageIndex + 1} de ${journeyStages.length}`;
  degreeWorkElements.journeyStepTitle.textContent = title;
  degreeWorkElements.journeyStepDescription.textContent = description;
  clearElement(degreeWorkElements.journeyConfiguredSteps);
  const steps = journeyStepsForStage(modality, item, selectedCode);
  if (!steps.length) {
    degreeWorkElements.journeyConfiguredSteps.append(
      createNode("p", "journey-not-required", "Esta etapa no aplica en el flujo seleccionado."),
    );
    return;
  }
  steps.forEach((step, index) => {
    const row = createNode("article", "journey-configured-step");
    const sequence = createNode("span", "journey-sequence", String(index + 1));
    const copy = createNode("div");
    copy.append(
      createNode("strong", "", step.name),
      createNode("small", "", (step.responsible_roles || []).join(" · ")),
    );
    let state = "Configurada";
    if (item && !step.requirement) {
      if (step.workflowIndex < item.current_step_index) state = "Completada";
      else if (step.workflowIndex === item.current_step_index) state = "Etapa actual";
      else state = "Pendiente";
    }
    row.append(sequence, copy, createNode("span", `journey-step-state state-${state.toLowerCase().replaceAll(" ", "-")}`, state));
    degreeWorkElements.journeyConfiguredSteps.append(row);
  });
}

function renderCaseActions(item) {
  clearElement(degreeWorkElements.caseActions);
  const currentStep = item.current_step;
  if (!currentStep || ["CLOSED", "REJECTED"].includes(item.status)) return;
  const role = degreeWorkState.currentUser.role;
  const canTransition = role === "Super administrador" || currentStep.responsible_roles.includes(role);
  if (canTransition) {
    const complete = createNode("button", "button primary compact-button", currentStep.is_decision ? "Aprobar etapa" : "Completar etapa");
    complete.type = "button";
    complete.addEventListener("click", () => transitionSelectedCase("COMPLETE"));
    degreeWorkElements.caseActions.append(complete);
    if (currentStep.is_decision) {
      const reject = createNode("button", "button danger-button compact-button", "Rechazar");
      reject.type = "button";
      reject.addEventListener("click", () => transitionSelectedCase("REJECT"));
      degreeWorkElements.caseActions.append(reject);
    }
  } else {
    degreeWorkElements.caseActions.append(createNode("p", "case-waiting", `Pendiente de ${currentStep.responsible_roles.join(" o ")}.`));
  }
  if (["Director de programa", "Super administrador"].includes(role)) {
    const assign = createNode("button", "button secondary compact-button", item.assigned_teacher_id ? "Cambiar docente" : "Asignar docente");
    assign.type = "button";
    assign.addEventListener("click", () => assignTeacher(item));
    degreeWorkElements.caseActions.append(assign);
  }
}

async function transitionSelectedCase(action) {
  const caseId = degreeWorkState.selectedCaseId;
  let comment = "Etapa completada desde la plataforma";
  if (action === "REJECT") {
    comment = window.prompt("Motivo del rechazo:", "Requiere ajustes de fondo") || "";
    if (!comment) return;
  }
  try {
    await degreeWorkJson(`/api/v1/degree-work-cases/${caseId}/transitions`, {
      method: "POST",
      body: JSON.stringify({ action, comment }),
    });
    await loadDegreeWork(degreeWorkState.currentUser);
  } catch (error) {
    window.alert(error.message);
  }
}

async function assignTeacher(item) {
  try {
    const users = await degreeWorkJson("/api/v1/usuarios");
    const teachers = users.filter((user) => user.role === "Docente" && user.status === "Activo");
    if (!teachers.length) throw new Error("No hay docentes activos para asignar.");
    const options = teachers.map((teacher, index) => `${index + 1}. ${teacher.name}`).join("\n");
    const selection = Number(window.prompt(`Selecciona un docente:\n${options}`, "1"));
    const teacher = teachers[selection - 1];
    if (!teacher) return;
    await degreeWorkJson(`/api/v1/degree-work-cases/${item.id}/assignments`, {
      method: "POST",
      body: JSON.stringify({ teacher_id: teacher.id }),
    });
    await loadDegreeWork(degreeWorkState.currentUser);
  } catch (error) {
    window.alert(error.message);
  }
}

function fillCaseModalityOptions(selectedCode) {
  clearElement(degreeWorkElements.caseModality);
  degreeWorkState.modalities.forEach((modality) => {
    const option = createNode("option", "", modality.name);
    option.value = modality.code;
    option.selected = modality.code === selectedCode;
    degreeWorkElements.caseModality.append(option);
  });
}

function openCaseDialog(selectedCode = "") {
  degreeWorkElements.caseForm.reset();
  degreeWorkElements.caseProgram.value = "Ingenieria de software";
  degreeWorkElements.caseFormMessage.textContent = "";
  fillCaseModalityOptions(selectedCode);
  degreeWorkElements.caseDialog.showModal();
}

async function createDegreeWorkCase(event) {
  event.preventDefault();
  degreeWorkElements.caseFormMessage.textContent = "Guardando solicitud...";
  try {
    const created = await degreeWorkJson("/api/v1/degree-work-cases", {
      method: "POST",
      body: JSON.stringify({
        modality_code: degreeWorkElements.caseModality.value,
        title: degreeWorkElements.caseTitle.value.trim(),
        program: degreeWorkElements.caseProgram.value.trim(),
      }),
    });
    degreeWorkState.selectedCaseId = created.id;
    degreeWorkElements.caseDialog.close();
    await loadDegreeWork(degreeWorkState.currentUser);
  } catch (error) {
    degreeWorkElements.caseFormMessage.textContent = error.message;
  }
}

async function loadModalitySettings(user) {
  if (!["Administrador", "Super administrador"].includes(user.role)) return;
  degreeWorkState.currentUser = user;
  try {
    degreeWorkState.settingsModalities = await degreeWorkJson("/api/v1/degree-work-modalities?include_inactive=true");
    renderModalitySettings();
  } catch (error) {
    clearElement(degreeWorkElements.modalitySettingsBody);
    const row = document.createElement("tr");
    const cell = createNode("td", "", error.message);
    cell.colSpan = 7;
    row.append(cell);
    degreeWorkElements.modalitySettingsBody.append(row);
  }
}

function renderModalitySettings() {
  clearElement(degreeWorkElements.modalitySettingsBody);
  degreeWorkState.settingsModalities.forEach((modality) => {
    const row = document.createElement("tr");
    const name = createNode("td");
    name.append(createNode("strong", "", modality.name), createNode("small", "table-secondary", modality.code));
    const statusCell = createNode("td");
    statusCell.append(createNode("span", `status-pill status-${modality.status.toLowerCase()}`, statusCopy[modality.status] || modality.status));
    const actions = createNode("td");
    const actionWrap = createNode("div", "action-buttons");
    if (modality.status === "DRAFT") {
      actionWrap.append(modalityActionButton("Editar", () => openModalityDialog(modality)));
      actionWrap.append(modalityActionButton("Eliminar", () => deleteModality(modality), "danger"));
      if (degreeWorkState.currentUser.role === "Super administrador") actionWrap.append(modalityActionButton("Publicar", () => changeModalityState(modality, "publication")));
    }
    if (modality.status === "ACTIVE" && degreeWorkState.currentUser.role === "Super administrador") actionWrap.append(modalityActionButton("Retirar", () => changeModalityState(modality, "retirement"), "danger"));
    actions.append(actionWrap);
    row.append(name, createNode("td", "", String(modality.version)), createNode("td", "", modality.is_homologatable ? "Si" : "No"), createNode("td", "", `${modality.min_participants} - ${modality.max_participants}`), createNode("td", "", `${modality.workflow_steps.length} pasos`), statusCell, actions);
    degreeWorkElements.modalitySettingsBody.append(row);
  });
}

function modalityActionButton(label, action, variant = "") {
  const button = createNode("button", `table-button ${variant}`, label);
  button.type = "button";
  button.addEventListener("click", action);
  return button;
}

function addWorkflowStepRow(data = {}) {
  const row = createNode("div", "workflow-step-row");
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
    const option = createNode("option", "", value);
    option.value = value;
    option.selected = value === data.step_type;
    type.append(option);
  });
  const role = document.createElement("select");
  role.className = "workflow-role";
  ["Estudiante", "Docente", "Director de programa", "Administrador", "Super administrador"].forEach((value) => {
    const option = createNode("option", "", value);
    option.value = value;
    option.selected = data.responsible_roles?.includes(value);
    role.append(option);
  });
  const remove = createNode("button", "icon-action danger-icon", "×");
  remove.type = "button";
  remove.title = "Eliminar paso";
  remove.setAttribute("aria-label", "Eliminar paso");
  remove.addEventListener("click", () => row.remove());
  row.append(code, name, type, role, remove);
  degreeWorkElements.workflowStepList.append(row);
}

function openModalityDialog(modality = null) {
  degreeWorkElements.modalityForm.reset();
  clearElement(degreeWorkElements.workflowStepList);
  degreeWorkElements.modalityFormMessage.textContent = "";
  degreeWorkElements.modalityId.value = modality?.id || "";
  degreeWorkElements.modalityCode.value = modality?.code || "";
  degreeWorkElements.modalityCode.disabled = Boolean(modality);
  degreeWorkElements.modalityName.value = modality?.name || "";
  degreeWorkElements.modalityDescription.value = modality?.description || "";
  degreeWorkElements.modalitySemester.value = modality?.initial_semester || "";
  degreeWorkElements.modalityDuration.value = modality?.duration_label || "Por definir";
  degreeWorkElements.modalityMinParticipants.value = modality?.min_participants || 1;
  degreeWorkElements.modalityMaxParticipants.value = modality?.max_participants || 1;
  degreeWorkElements.modalityHomologatable.checked = modality?.is_homologatable || false;
  degreeWorkElements.modalityFormTitle.textContent = modality ? "Editar modalidad" : "Nueva modalidad";
  const steps = modality?.workflow_steps || [
    { code: "APPLICATION", name: "Postulacion", step_type: "FORM", responsible_roles: ["Estudiante"] },
    { code: "CLOSURE", name: "Cierre", step_type: "CLOSURE", responsible_roles: ["Director de programa"] },
  ];
  steps.forEach(addWorkflowStepRow);
  degreeWorkElements.modalityDialog.showModal();
}

function collectWorkflowSteps() {
  return Array.from(degreeWorkElements.workflowStepList.querySelectorAll(".workflow-step-row")).map((row) => ({
    code: row.querySelector(".workflow-code").value.trim().toUpperCase().replaceAll(" ", "_"),
    name: row.querySelector(".workflow-name").value.trim(),
    step_type: row.querySelector(".workflow-type").value,
    responsible_roles: [row.querySelector(".workflow-role").value],
    is_decision: row.querySelector(".workflow-type").value === "APPROVAL",
  }));
}

async function saveModality(event) {
  event.preventDefault();
  const id = degreeWorkElements.modalityId.value;
  const payload = {
    name: degreeWorkElements.modalityName.value.trim(),
    description: degreeWorkElements.modalityDescription.value.trim(),
    is_homologatable: degreeWorkElements.modalityHomologatable.checked,
    initial_semester: degreeWorkElements.modalitySemester.value ? Number(degreeWorkElements.modalitySemester.value) : null,
    duration_label: degreeWorkElements.modalityDuration.value.trim() || "Por definir",
    min_participants: Number(degreeWorkElements.modalityMinParticipants.value),
    max_participants: Number(degreeWorkElements.modalityMaxParticipants.value),
    requirements: [],
    evaluation_criteria: [],
    workflow_steps: collectWorkflowSteps(),
  };
  if (!id) payload.code = degreeWorkElements.modalityCode.value.trim().toUpperCase();
  degreeWorkElements.modalityFormMessage.textContent = "Guardando borrador...";
  try {
    await degreeWorkJson(id ? `/api/v1/degree-work-modalities/${id}` : "/api/v1/degree-work-modalities", {
      method: id ? "PATCH" : "POST",
      body: JSON.stringify(payload),
    });
    degreeWorkElements.modalityDialog.close();
    await loadModalitySettings(degreeWorkState.currentUser);
  } catch (error) {
    degreeWorkElements.modalityFormMessage.textContent = error.message;
  }
}

async function changeModalityState(modality, action) {
  try {
    await degreeWorkJson(`/api/v1/degree-work-modalities/${modality.id}/${action}`, { method: "POST" });
    await loadModalitySettings(degreeWorkState.currentUser);
  } catch (error) {
    window.alert(error.message);
  }
}

async function deleteModality(modality) {
  if (!window.confirm(`Eliminar el borrador "${modality.name}"?`)) return;
  try {
    await degreeWorkJson(`/api/v1/degree-work-modalities/${modality.id}`, { method: "DELETE" });
    await loadModalitySettings(degreeWorkState.currentUser);
  } catch (error) {
    window.alert(error.message);
  }
}

degreeWorkElements.search.addEventListener("input", renderModalityCatalog);
degreeWorkElements.journeyStages.forEach((button) => {
  button.addEventListener("click", () => {
    degreeWorkState.selectedJourneyStage = button.dataset.stage;
    const item = degreeWorkState.cases.find(
      (entry) => entry.id === degreeWorkState.selectedCaseId,
    );
    const modality = degreeWorkState.modalities.find(
      (entry) => entry.code === (item?.modality_code || degreeWorkState.selectedModalityCode),
    ) || degreeWorkState.modalities[0];
    renderJourney(modality || null, item || null);
  });
});
degreeWorkElements.refresh.addEventListener("click", () => loadDegreeWork(degreeWorkState.currentUser));
degreeWorkElements.openCaseForm.addEventListener("click", () => openCaseDialog());
degreeWorkElements.cancelCaseForm.addEventListener("click", () => degreeWorkElements.caseDialog.close());
degreeWorkElements.caseForm.addEventListener("submit", createDegreeWorkCase);
degreeWorkElements.newModalityButton.addEventListener("click", () => openModalityDialog());
degreeWorkElements.cancelModalityForm.addEventListener("click", () => degreeWorkElements.modalityDialog.close());
degreeWorkElements.addWorkflowStep.addEventListener("click", () => addWorkflowStepRow());
degreeWorkElements.modalityForm.addEventListener("submit", saveModality);
