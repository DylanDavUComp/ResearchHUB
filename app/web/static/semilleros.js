const semilleroState = {
  user: null,
  page: 1,
  totalPages: 0,
  items: [],
  selectedId: null,
  directors: [],
};

const semilleroUi = {
  heading: document.querySelector("#semillero-timeline-heading"),
  timeline: document.querySelector("#semillero-timeline"),
  note: document.querySelector("#semillero-timeline-note"),
  workflow: document.querySelector("#semillero-process"),
  select: document.querySelector("#semillero-case-select"),
  current: document.querySelector("#semillero-current"),
  history: document.querySelector("#semillero-history"),
  message: document.querySelector("#semillero-message"),
  pageLabel: document.querySelector("#semillero-page-label"),
  prev: document.querySelector("#semillero-prev"),
  next: document.querySelector("#semillero-next"),
  forms: {
    create: document.querySelector("#semillero-create-form"),
    assign: document.querySelector("#semillero-assign-form"),
    register: document.querySelector("#semillero-register-form"),
    validate: document.querySelector("#semillero-validate-form"),
    plan: document.querySelector("#semillero-plan-form"),
    decision: document.querySelector("#semillero-plan-decision-form"),
  },
  metrics: {
    stage: document.querySelector("#semillero-metric-stage"),
    stageDetail: document.querySelector("#semillero-metric-stage-detail"),
    hours: document.querySelector("#semillero-metric-hours"),
    registration: document.querySelector("#semillero-metric-registration"),
    plan: document.querySelector("#semillero-metric-plan"),
  },
};

const semilleroStageNames = [
  "Inscripción al semillero",
  "Registro en el semillero",
  "Validación de requisitos",
  "Plan individual de trabajo",
];

const semilleroActions = {
  SUBMIT: "Solicitud enviada",
  ASSIGN_REVIEWER: "Director asignado",
  REGISTER: "Registro confirmado",
  VALIDATE: "Requisitos validados",
  RETURN_VALIDATION: "Validación devuelta",
  SUBMIT_PLAN: "Plan presentado",
  APPROVE_PLAN: "Plan aprobado",
  RETURN_PLAN: "Plan devuelto",
};

async function semilleroRequest(path, options = {}) {
  const response = await apiFetch(`/api/v1/semillero-applications${path}`, options);
  if (!response.ok) {
    let message = "No fue posible completar la acción. Actualiza e intenta de nuevo.";
    try {
      const payload = await response.json();
      message = payload.error?.message || payload.detail?.[0]?.msg || message;
    } catch (_) {
      // Keep the stable fallback message.
    }
    throw new Error(message);
  }
  return response.json();
}

function selectedSemillero() {
  return semilleroState.items.find((item) => item.id === semilleroState.selectedId) || null;
}

function setSemilleroMessage(message, isError = false) {
  semilleroUi.message.textContent = message;
  semilleroUi.message.classList.toggle("is-error", isError);
}

function renderSemilleroTimeline(item) {
  const complete = item?.completed_stages || [];
  const current = item?.current_stage || 1;
  semilleroUi.heading.textContent = item
    ? current > 4 ? "Etapas 1 a 4 completadas" : `Etapas del proceso (${current} de 11)`
    : "Etapas del proceso";
  semilleroUi.note.textContent = item
    ? current > 4
      ? "El plan fue aprobado. Las etapas siguientes se definirán en la próxima revisión."
      : `Etapa actual: ${semilleroStageNames[current - 1]}.`
    : "Aún no hay una solicitud de semillero seleccionada.";
  [...semilleroUi.timeline.children].forEach((node, index) => {
    const number = index + 1;
    node.classList.toggle("done", number <= 4 && complete.includes(number));
    node.classList.toggle("current", number <= 4 && number === current);
    node.querySelector("span").textContent = number <= 4 && complete.includes(number) ? "✓" : String(number);
    if (number <= 4 && number === current) node.setAttribute("aria-current", "step");
    else node.removeAttribute("aria-current");
  });
}

function renderSemillero() {
  const item = selectedSemillero();
  const role = semilleroState.user?.role;
  semilleroUi.select.replaceChildren();
  if (!semilleroState.items.length) {
    const option = new Option("Sin solicitudes", "");
    semilleroUi.select.add(option);
  } else {
    semilleroState.items.forEach((entry) => {
      const option = new Option(`${entry.semillero_name} · ${entry.project_title}`, entry.id);
      semilleroUi.select.add(option);
    });
    semilleroUi.select.value = item?.id || semilleroState.items[0].id;
  }
  semilleroUi.select.disabled = semilleroState.items.length < 2;
  semilleroUi.pageLabel.textContent = `Página ${semilleroState.page} de ${Math.max(1, semilleroState.totalPages)}`;
  semilleroUi.prev.disabled = semilleroState.page <= 1;
  semilleroUi.next.disabled = semilleroState.page >= semilleroState.totalPages;
  renderSemilleroTimeline(item);
  semilleroUi.metrics.stage.textContent = item
    ? item.current_stage > 4 ? "Etapas 1 a 4 completas" : semilleroStageNames[item.current_stage - 1]
    : "Sin solicitud";
  semilleroUi.metrics.stageDetail.textContent = item
    ? `Etapa ${Math.min(item.current_stage, 4)} de las 4 habilitadas.`
    : "Envía tu inscripción para comenzar.";
  semilleroUi.metrics.hours.textContent = item?.planned_hours ? String(item.planned_hours) : "—";
  semilleroUi.metrics.registration.textContent = item?.registration_reference ? "Confirmado" : "Pendiente";
  semilleroUi.metrics.plan.textContent = item?.plan_status === "APPROVED" ? "Aprobado"
    : item?.plan_status === "SUBMITTED" ? "En revisión"
      : item?.plan_status === "RETURNED" ? "Devuelto" : "Sin presentar";
  Object.values(semilleroUi.forms).forEach((form) => form.classList.add("is-hidden"));
  semilleroUi.forms.create.classList.toggle("is-hidden", role !== "Estudiante");
  semilleroUi.history.replaceChildren();
  if (!item) {
    semilleroUi.current.textContent = role === "Estudiante"
      ? "Completa el formulario para iniciar tu solicitud."
      : "No hay solicitudes asignadas en esta página.";
    return;
  }
  const phase = item.plan_status === "SUBMITTED" ? "Plan en revisión"
    : item.plan_status === "RETURNED" ? "Plan devuelto"
      : item.current_stage === 2 && !item.reviewer_id ? "Pendiente de asignar director"
        : "Pendiente";
  const status = item.current_stage > 4
    ? "Plan aprobado"
    : `${semilleroStageNames[item.current_stage - 1]} · ${phase}`;
  semilleroUi.current.replaceChildren();
  const title = document.createElement("strong");
  title.textContent = item.project_title;
  const detail = document.createElement("p");
  detail.textContent = `${item.semillero_name} · ${item.program} · ${status}`;
  semilleroUi.current.append(title, detail);
  if (item.registration_reference) {
    const reference = document.createElement("p");
    reference.textContent = `Registro verificado: ${item.registration_reference}`;
    semilleroUi.current.append(reference);
  }
  if (item.plan_summary) {
    const plan = document.createElement("p");
    plan.textContent = `Plan: ${item.plan_summary} · ${item.planned_hours} horas previstas`;
    semilleroUi.current.append(plan);
  }
  [...item.history].reverse().slice(0, 5).forEach((event) => {
    const row = document.createElement("li");
    row.textContent = `${semilleroActions[event.action] || event.action} · ${new Date(event.created_at).toLocaleDateString("es-CO")}${event.comment ? ` · ${event.comment}` : ""}`;
    semilleroUi.history.append(row);
  });
  semilleroUi.forms.assign.classList.toggle("is-hidden", role !== "Super administrador" || item.current_stage > 4);
  semilleroUi.forms.register.classList.toggle("is-hidden", role !== "Director de programa" || item.reviewer_id !== semilleroState.user.id || item.current_stage !== 2);
  semilleroUi.forms.validate.classList.toggle("is-hidden", role !== "Director de programa" || item.reviewer_id !== semilleroState.user.id || item.current_stage !== 3);
  semilleroUi.forms.plan.classList.toggle("is-hidden", role !== "Estudiante" || item.current_stage !== 4 || item.plan_status === "SUBMITTED");
  semilleroUi.forms.decision.classList.toggle("is-hidden", role !== "Director de programa" || item.reviewer_id !== semilleroState.user.id || item.current_stage !== 4 || item.plan_status !== "SUBMITTED");
}

async function loadSemilleroWorkflow(user) {
  semilleroState.user = user;
  if (!["Estudiante", "Director de programa", "Super administrador"].includes(user.role)) {
    semilleroUi.workflow.classList.add("is-hidden");
    semilleroUi.note.textContent = "El seguimiento de semilleros está disponible para estudiantes y responsables asignados.";
    return;
  }
  semilleroUi.workflow.classList.remove("is-hidden");
  try {
    const payload = await semilleroRequest(`?page=${semilleroState.page}&page_size=20`);
    semilleroState.items = payload.data;
    semilleroState.totalPages = payload.total_pages;
    if (!semilleroState.items.some((item) => item.id === semilleroState.selectedId)) {
      semilleroState.selectedId = semilleroState.items[0]?.id || null;
    }
    if (user.role === "Super administrador") {
      await searchSemilleroDirectors();
    }
    renderSemillero();
    setSemilleroMessage("");
  } catch (error) {
    setSemilleroMessage(error.message || "No fue posible cargar el proceso.", true);
    semilleroUi.note.textContent = "No fue posible cargar el avance.";
  }
}

async function searchSemilleroDirectors() {
  const query = semilleroUi.forms.assign.elements.namedItem("director_query").value.trim();
  semilleroState.directors = await semilleroRequest(`/reviewers?q=${encodeURIComponent(query)}`);
  const picker = semilleroUi.forms.assign.elements.namedItem("reviewer_id");
  picker.replaceChildren();
  semilleroState.directors.forEach((person) => picker.add(new Option(person.name, person.id)));
  semilleroUi.forms.assign.querySelector("button[type=submit]").disabled = !semilleroState.directors.length;
}

let directorSearchTimer;
semilleroUi.forms.assign.elements.namedItem("director_query").addEventListener("input", () => {
  clearTimeout(directorSearchTimer);
  directorSearchTimer = setTimeout(() => {
    searchSemilleroDirectors().catch((error) => setSemilleroMessage(error.message, true));
  }, 300);
});

async function submitSemillero(path, payload) {
  const item = selectedSemillero();
  const target = path && item ? `/${item.id}${path}` : path;
  try {
    const updated = await semilleroRequest(target, {
      method: "POST",
      headers: { "Content-Type": "application/json", "Idempotency-Key": crypto.randomUUID() },
      body: JSON.stringify(payload),
    });
    semilleroState.selectedId = updated.id;
    if (!path) semilleroState.page = 1;
    await loadSemilleroWorkflow(semilleroState.user);
    setSemilleroMessage("Cambios guardados correctamente.");
  } catch (error) {
    setSemilleroMessage(error.message || "No fue posible guardar los cambios.", true);
  }
}

semilleroUi.select.addEventListener("change", (event) => {
  semilleroState.selectedId = event.target.value;
  renderSemillero();
});
semilleroUi.prev.addEventListener("click", () => {
  semilleroState.page -= 1;
  loadSemilleroWorkflow(semilleroState.user);
});
semilleroUi.next.addEventListener("click", () => {
  semilleroState.page += 1;
  loadSemilleroWorkflow(semilleroState.user);
});
semilleroUi.forms.create.addEventListener("submit", (event) => {
  event.preventDefault();
  const data = new FormData(event.currentTarget);
  submitSemillero("", Object.fromEntries(data));
});
semilleroUi.forms.assign.addEventListener("submit", (event) => {
  event.preventDefault();
  submitSemillero("/reviewer", {
    expected_version: selectedSemillero().version,
    reviewer_id: new FormData(event.currentTarget).get("reviewer_id"),
  });
});
semilleroUi.forms.register.addEventListener("submit", (event) => {
  event.preventDefault();
  submitSemillero("/register", {
    expected_version: selectedSemillero().version,
    reference: new FormData(event.currentTarget).get("reference"),
  });
});
semilleroUi.forms.validate.addEventListener("submit", (event) => {
  event.preventDefault();
  const data = new FormData(event.currentTarget);
  submitSemillero("/validate", {
    expected_version: selectedSemillero().version,
    eligible: event.submitter.value === "true",
    semester: Number(data.get("semester")),
    comment: data.get("comment"),
  });
});
semilleroUi.forms.plan.addEventListener("submit", (event) => {
  event.preventDefault();
  const data = new FormData(event.currentTarget);
  submitSemillero("/plan", {
    expected_version: selectedSemillero().version,
    summary: data.get("summary"),
    deliverables: data.get("deliverables"),
    planned_hours: Number(data.get("planned_hours")),
  });
});
semilleroUi.forms.decision.addEventListener("submit", (event) => {
  event.preventDefault();
  submitSemillero("/plan-decision", {
    expected_version: selectedSemillero().version,
    approved: event.submitter.value === "true",
    comment: new FormData(event.currentTarget).get("comment"),
  });
});
