const state = { data: null, filters: {} };

const byId = (id) => document.getElementById(id);
const formatNumber = new Intl.NumberFormat("es-PA");
const formatRate = (value) => `${Number(value).toLocaleString("es-PA", { minimumFractionDigits: 1, maximumFractionDigits: 1 })}%`;

function empty(node, message = "No hay información suficiente para esta selección.") {
  node.replaceChildren();
  const element = document.createElement("p");
  element.className = "empty";
  element.textContent = message;
  node.append(element);
}

function create(tag, className, text) {
  const element = document.createElement(tag);
  if (className) element.className = className;
  if (text !== undefined) element.textContent = text;
  return element;
}

function loading(targets) {
  for (const target of targets) {
    const node = typeof target === "string" ? byId(target) : target;
    if (!node) continue;
    node.replaceChildren(create("div", "loading", "Actualizando indicadores…"));
  }
}

function createBarChart(node, items, options = {}) {
  node.replaceChildren();
  if (!items?.length) return empty(node);
  const max = Math.max(...items.map((item) => item.rate), 1);
  for (const [index, item] of items.entries()) {
    const row = create("div", "bar-row");
    row.append(create("span", "bar-label", item.label));
    const track = create("span", "bar-track");
    const fill = create("span", `bar-fill ${index === 0 && options.highlight ? "amber" : ""}`);
    fill.style.width = "0%";
    const targetWidth = `${Math.max((item.rate / max) * 100, 2)}%`;
    fill.title = `${item.label}: ${formatRate(item.rate)} (${formatNumber.format(item.n ?? item.count ?? 0)} registros)`;
    track.append(fill);
    row.append(track, create("span", "bar-value", formatRate(item.rate)));
    node.append(row);
    
    // Trigger animation after append
    requestAnimationFrame(() => {
      requestAnimationFrame(() => {
        fill.style.width = targetWidth;
      });
    });
  }
}

function renderFilters(filters) {
  const container = byId("filter-fields");
  const knownIds = [...container.querySelectorAll("select")].map((select) => select.name).join("|");
  const incomingIds = filters.map((filter) => filter.id).join("|");
  if (knownIds === incomingIds) return;
  container.replaceChildren();
  for (const filter of filters) {
    const label = create("label", "filter-control");
    label.append(create("span", "", filter.label));
    const select = document.createElement("select");
    select.name = filter.id;
    select.setAttribute("aria-label", filter.label);
    for (const optionValue of filter.options) {
      const option = document.createElement("option");
      option.value = optionValue;
      option.textContent = optionValue;
      select.append(option);
    }
    select.value = state.filters[filter.id] || "Todos";
    select.addEventListener("change", () => {
      state.filters[filter.id] = select.value;
      refresh();
    });
    label.append(select);
    container.append(label);
  }
}

function renderKpis(kpis) {
  const container = byId("kpis");
  container.replaceChildren();
  for (const kpi of kpis) {
    const card = create("article", "kpi");
    card.append(create("span", "kpi-label", kpi.label));
    card.append(create("strong", "kpi-value", kpi.value));
    card.append(create("span", "kpi-context", kpi.context));
    container.append(card);
  }
}

function renderDecision(recommendation) {
  const grid = byId("decision-grid");
  grid.replaceChildren();
  const steps = [
    ["Problema", recommendation.problem],
    ["Evidencia", recommendation.finding],
    ["Acción sugerida", recommendation.action],
    ["Seguimiento", recommendation.follow_up],
  ];
  for (const [title, content] of steps) {
    const card = create("div", "decision-step");
    card.append(create("small", "", title), create("p", "", content));
    grid.append(card);
  }
}

function protocolText(title, content) {
  const block = document.createElement("p");
  block.append(create("strong", "", title), document.createTextNode(content));
  return block;
}

function renderProtocol(protocol) {
  const problem = byId("protocol-problem");
  problem.replaceChildren();
  problem.append(
    protocolText("Pregunta de análisis", protocol.question),
    protocolText("Objetivo general", protocol.objective),
  );
  const objectives = document.createElement("ul");
  for (const objective of protocol.objectives.slice(0, 3)) objectives.append(create("li", "", objective));
  problem.append(objectives);

  const design = byId("protocol-design");
  design.replaceChildren();
  design.append(
    protocolText("Tipo de estudio", protocol.design),
    protocolText("Unidad de análisis", protocol.unit),
    protocolText("Inclusión", protocol.eligibility.included),
    protocolText("Exclusión / manejo", protocol.eligibility.excluded),
  );

  const variables = byId("protocol-variables");
  variables.replaceChildren();
  const table = document.createElement("table");
  table.innerHTML = "<thead><tr><th>Variable</th><th>Rol</th><th>Tipo</th><th>Definición operacional</th></tr></thead>";
  const body = document.createElement("tbody");
  for (const variable of protocol.variables) {
    const row = document.createElement("tr");
    for (const value of [variable.name, variable.role, variable.type, variable.definition]) row.append(create("td", "", value));
    body.append(row);
  }
  table.append(body);
  variables.append(table);
}

function renderFactors(factors) {
  const list = byId("factor-list");
  list.replaceChildren();
  if (!factors?.length) return empty(list);
  for (const factor of factors) {
    const row = create("article", "factor");
    const name = create("div", "factor-name", factor.factor);
    name.append(create("span", "factor-group", `Mayor tasa: ${factor.group} · n=${formatNumber.format(factor.n)}`));
    const track = create("span", "bar-track");
    const fill = create("span", "bar-fill amber");
    fill.style.width = "0%";
    const targetWidth = `${Math.min(factor.rate, 100)}%`;
    track.append(fill);
    const rate = create("div", "factor-rate", formatRate(factor.rate));
    rate.append(create("em", "", `${factor.delta >= 0 ? "+" : ""}${factor.delta.toFixed(1)} pp vs. promedio`));
    row.append(name, track, rate);
    list.append(row);

    // Trigger animation after append
    requestAnimationFrame(() => {
      requestAnimationFrame(() => {
        fill.style.width = targetWidth;
      });
    });
  }
}

function renderSegments(segments) {
  const body = byId("segment-table");
  body.replaceChildren();
  if (!segments?.length) {
    const row = document.createElement("tr");
    const cell = document.createElement("td");
    cell.colSpan = 3;
    cell.textContent = "No hay combinaciones con muestra suficiente bajo estos filtros.";
    row.append(cell); body.append(row); return;
  }
  for (const segment of segments) {
    const row = document.createElement("tr");
    for (const value of [segment.label, formatNumber.format(segment.n), formatRate(segment.rate)]) row.append(create("td", "", value));
    body.append(row);
  }
}

function renderQuality(quality, protocol) {
  byId("quality-rows").textContent = formatNumber.format(quality.rows);
  byId("quality-cols").textContent = formatNumber.format(quality.columns);
  const body = byId("quality-table");
  body.replaceChildren();
  if (!quality.missing?.length) {
    const row = document.createElement("tr");
    const cell = document.createElement("td");
    cell.colSpan = 4; cell.textContent = "No se detectaron campos vacíos o reglas especiales en esta fuente.";
    row.append(cell); body.append(row);
  } else {
    for (const issue of quality.missing) {
      const row = document.createElement("tr");
      for (const value of [issue.field, formatNumber.format(issue.count), formatRate(issue.rate), issue.note]) row.append(create("td", "", value));
      body.append(row);
    }
  }

  const eligibility = byId("eligibility-card");
  eligibility.replaceChildren();
  const counters = [
    ["Universo disponible", formatNumber.format(protocol.eligibility.all)],
    ["Desenlace válido", formatNumber.format(protocol.eligibility.valid_target)],
    ["Apto para modelo", formatNumber.format(protocol.eligibility.usable)],
  ];
  for (const [label, value] of counters) {
    const block = document.createElement("div");
    block.append(create("strong", "", value), document.createTextNode(label));
    eligibility.append(block);
  }
  const ethics = create("ul", "ethics-list");
  for (const note of protocol.ethics) ethics.append(create("li", "", note));
  eligibility.append(ethics);
}

function renderModel(model) {
  const note = byId("model-note");
  const context = byId("model-context");
  const table = byId("model-table");
  const features = byId("feature-chart");
  const risks = byId("risk-chart");
  table.replaceChildren();
  if (model.status !== "ok") {
    note.textContent = model.message || "La validación del modelo no está disponible.";
    context.textContent = "";
    empty(features, "Sin importancias disponibles.");
    empty(risks, "Sin estratos disponibles.");
    const row = document.createElement("tr");
    const cell = document.createElement("td");
    cell.colSpan = 6; cell.textContent = "No hay métricas de validación disponibles.";
    row.append(cell); table.append(row); return;
  }
  note.textContent = model.note;
  context.textContent = `Modelo seleccionado: ${model.selected} · entrenamiento n=${formatNumber.format(model.train_n)} · prueba n=${formatNumber.format(model.test_n)}`;
  for (const candidate of model.models) {
    const row = document.createElement("tr");
    const values = [candidate.name, candidate.accuracy, candidate.precision, candidate.recall, candidate.f1, candidate.auc];
    for (const [index, value] of values.entries()) {
      const cell = create("td", "", index === 0 ? value : Number(value).toFixed(3));
      if (candidate.name === model.selected) cell.style.fontWeight = "750";
      row.append(cell);
    }
    table.append(row);
  }
  features.replaceChildren();
  const maxFeature = Math.max(...model.features.map((item) => item.value), .0001);
  for (const item of model.features) {
    const row = create("div", "bar-row");
    row.append(create("span", "bar-label", item.label));
    const track = create("span", "bar-track");
    const fill = create("span", "bar-fill");
    fill.style.width = "0%";
    const targetWidth = `${Math.max((item.value / maxFeature) * 100, 2)}%`;
    track.append(fill);
    row.append(track, create("span", "bar-value", item.value.toFixed(3)));
    features.append(row);

    requestAnimationFrame(() => {
      requestAnimationFrame(() => {
        fill.style.width = targetWidth;
      });
    });
  }
  createBarChart(risks, model.risk_bands.map((item) => ({
    label: `${item.label} · estimado ${formatRate(item.predicted)}`,
    rate: item.observed,
    n: item.n,
  })), { highlight: true });
}

function renderMethod(method) {
  const list = byId("method-list");
  list.replaceChildren();
  for (const [title, description] of method) {
    const item = document.createElement("li");
    item.append(create("strong", "", title), document.createTextNode(description));
    list.append(item);
  }
}

function render(data) {
  state.data = data;
  byId("source-pill").textContent = `${data.dataset.name} · ${data.dataset.source}${data.dataset.fallback ? " · fuente temporal" : ""}`;
  byId("footer-source").textContent = `Fuente: ${data.dataset.source}`;
  renderFilters(data.filters);
  renderProtocol(data.protocol);
  renderKpis(data.kpis);
  renderDecision(data.recommendation);
  createBarChart(byId("distribution-chart"), data.distribution, { highlight: true });
  const summary = byId("overview-insight");
  summary.replaceChildren();
  summary.append(create("small", "", "LECTURA RÁPIDA"));
  summary.append(create("strong", "", `${formatRate(data.selection.prevalence)} de tasa observada`));
  summary.append(create("p", "", `${formatNumber.format(data.selection.positive)} de ${formatNumber.format(data.selection.n)} registros filtrados cumplen el resultado definido.`));
  renderFactors(data.factors);
  createBarChart(byId("age-chart"), data.age_rates, { highlight: true });
  createBarChart(byId("bmi-chart"), data.bmi_rates, { highlight: true });
  renderSegments(data.segments);
  renderModel(data.model);
  renderQuality(data.quality, data.protocol);
  renderMethod(data.method);
}

async function refresh() {
  loading(["kpis", "distribution-chart", "factor-list", "age-chart", "bmi-chart"]);
  const query = new URLSearchParams(Object.entries(state.filters).filter(([, value]) => value && value !== "Todos"));
  try {
    const response = await fetch(`/api/dashboard?${query.toString()}`);
    const data = await response.json();
    if (!response.ok) throw new Error(data.error || "No fue posible procesar el dataset.");
    render(data);
  } catch (error) {
    const card = create("section", "error-card");
    card.append(
      create("h1", "", "El tablero no pudo cargar los datos"),
      create("p", "", error.message),
      create("p", "", "Verifica que haya un CSV compatible dentro de data/ y vuelve a intentar."),
    );
    document.querySelector("main").replaceWith(card);
  }
}

byId("reset-filters").addEventListener("click", () => {
  state.filters = {};
  for (const select of document.querySelectorAll("#filter-fields select")) select.value = "Todos";
  refresh();
});

const calcForm = byId("calc-form");
if (calcForm) {
  calcForm.addEventListener("submit", async (e) => {
    e.preventDefault();
    const btn = calcForm.querySelector(".calc-button");
    const originalText = btn.textContent;
    btn.textContent = "Calculando...";
    btn.disabled = true;

    try {
      const payload = {
        Age: parseFloat(byId("calc-age").value),
        BMI: parseFloat(byId("calc-bmi").value),
        HighBP: parseInt(byId("calc-bp").value, 10),
        HighChol: parseInt(byId("calc-chol").value, 10),
        GenHlth: parseInt(byId("calc-genhlth").value, 10),
        DiffWalk: parseInt(byId("calc-diffwalk").value, 10),
        HeartDiseaseorAttack: parseInt(byId("calc-heart").value, 10)
      };

      const response = await fetch("/api/score/calculate", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload)
      });
      
      const result = await response.json();
      if (!response.ok) throw new Error(result.error || "Error al calcular el score.");
      
      byId("calc-score-val").textContent = `${result.score} pts`;
      byId("calc-score-desc").textContent = `Nivel de riesgo: ${result.risk_level} (${formatRate(result.probability * 100)} probabilidad estimada)`;
      byId("calc-result").style.display = "block";
    } catch (error) {
      alert(error.message);
    } finally {
      btn.textContent = originalText;
      btn.disabled = false;
    }
  });
}

refresh();
