
const API = "/api";

const pageTitles = {
  overview: "Overview",
  issues: "Issue Management",
  report: "Report an Issue",
  simulator: "Impact Simulator",
  locations: "QR Locations",
  analytics: "Analytics"
};

let currentIssues = [];
let locations = [];
let charts = {};
let selectedIssueId = null;
let noticeTimer = null;
let searchDelay = null;

const $ = (selector) => document.querySelector(selector);
const $$ = (selector) => [...document.querySelectorAll(selector)];

function escapeHTML(value) {
  return String(value ?? "").replace(/[&<>"']/g, (char) => ({
    "&": "&amp;",
    "<": "&lt;",
    ">": "&gt;",
    '"': "&quot;",
    "'": "&#39;"
  })[char]);
}

function number(value, digits = 2) {
  return Number(value || 0).toLocaleString("en-IN", {
    maximumFractionDigits: digits
  });
}

function dateText(value) {
  if (!value) return "—";

  const normalized = value.includes("T")
    ? value
    : value.replace(" ", "T");

  const parsed = new Date(
    normalized.endsWith("Z") ||
    /[+-]\d{2}:\d{2}$/.test(normalized)
      ? normalized
      : `${normalized}Z`
  );

  return Number.isNaN(parsed.getTime())
    ? value
    : parsed.toLocaleString("en-IN", {
        day: "2-digit",
        month: "short",
        year: "numeric"
      });
}

function priorityClass(priority) {
  return ({
    Critical: "danger",
    High: "danger",
    Medium: "warning",
    Low: "success"
  })[priority] || "neutral";
}

function statusClass(status) {
  return status === "Resolved"
    ? "success"
    : status === "In Progress" || status === "Acknowledged"
      ? "warning"
      : status === "Reopened"
        ? "danger"
        : "neutral";
}

function showNotice(message, isError = false) {
  const notice = $("#notice");
  if (!notice) return;

  notice.textContent = message;
  notice.classList.remove("hidden", "error");

  if (isError) notice.classList.add("error");

  clearTimeout(noticeTimer);

  noticeTimer = setTimeout(() => {
    notice.classList.add("hidden");
  }, 6000);
}

async function api(path, options = {}) {
  const response = await fetch(`${API}${path}`, {
    ...options,
    headers: {
      ...(options.body
        ? { "Content-Type": "application/json" }
        : {}),
      ...(options.headers || {})
    }
  });

  const contentType = response.headers.get("content-type") || "";

  const data = contentType.includes("application/json")
    ? await response.json()
    : null;

  if (!response.ok) {
    const detail = data?.detail;

    throw new Error(
      typeof detail === "string"
        ? detail
        : JSON.stringify(detail || `Request failed (${response.status})`)
    );
  }

  return data;
}

function setText(selector, value) {
  const element = $(selector);
  if (element) element.textContent = value;
}

function setHTML(selector, value) {
  const element = $(selector);
  if (element) element.innerHTML = value;
}

// NAVIGATION

function navigate(page) {
  if (!pageTitles[page]) return;

  $$(".page").forEach((element) => {
    element.classList.toggle(
      "active",
      element.id === `page-${page}`
    );
  });

  $$(".nav-link").forEach((element) => {
    element.classList.toggle(
      "active",
      element.dataset.page === page
    );
  });

  setText("#pageTitle", pageTitles[page]);

  $("#sidebar")?.classList.remove("open");

  if (page === "overview") loadOverview();
  if (page === "issues") loadIssues();
  if (page === "locations") loadLocations();
  if (page === "analytics") loadAnalytics();

  window.scrollTo({ top: 0, behavior: "smooth" });
}

document.addEventListener("click", (event) => {
  const navigation = event.target.closest("[data-page]");

  if (navigation) {
    event.preventDefault();
    navigate(navigation.dataset.page);
  }
});

$("#mobileMenu")?.addEventListener("click", () => {
  $("#sidebar")?.classList.toggle("open");
});

// CONNECTION STATUS

async function checkHealth() {
  try {
    const health = await api("/health");

    setHTML(
      "#connectionStatus",
      '<span class="status-dot"></span> System connected'
    );

    const apiStatus = $("#apiStatus");
    if (apiStatus) {
      apiStatus.className = "pill success";
      apiStatus.textContent = "Connected";
    }

    const dbStatus = $("#dbStatus");
    if (dbStatus) {
      dbStatus.className = "pill success";
      dbStatus.textContent = "Connected";
    }

    const aiStatus = $("#aiStatus");

    if (aiStatus) {
      aiStatus.className = health.ai_available
        ? "pill success"
        : "pill warning";

      aiStatus.textContent = health.ai_available
        ? "Gemini configured"
        : "AI fallback mode";
    }
  } catch (error) {
    setHTML(
      "#connectionStatus",
      '<span class="status-dot" style="background:#C24141"></span> Connection issue'
    );

    const apiStatus = $("#apiStatus");
    if (apiStatus) {
      apiStatus.className = "pill danger";
      apiStatus.textContent = "Unavailable";
    }

    const dbStatus = $("#dbStatus");
    if (dbStatus) {
      dbStatus.className = "pill danger";
      dbStatus.textContent = "Unavailable";
    }

    const aiStatus = $("#aiStatus");
    if (aiStatus) {
      aiStatus.className = "pill neutral";
      aiStatus.textContent = "Unknown";
    }
  }
}

// OVERVIEW

async function loadOverview() {
  try {
    const [summary, recent] = await Promise.all([
      api("/dashboard/summary"),
      api("/dashboard/recent-issues?limit=5")
    ]);

    setText("#metricTotal", number(summary.total_issues, 0));
    setText("#metricOpen", number(summary.open_issues, 0));
    setText(
      "#metricHigh",
      number(summary.high_priority_open_issues, 0)
    );
    setText(
      "#metricResolved",
      number(summary.resolved_issues, 0)
    );

    if (!recent.issues.length) {
      setHTML(
        "#recentIssues",
        '<div class="empty-state">No reports yet. Select “Report an issue” to create your first record.</div>'
      );
      return;
    }

    setHTML(
      "#recentIssues",
      recent.issues.map((issue) => `
        <div class="recent-item">
          <div>
            <h3>${escapeHTML(issue.title)}</h3>
            <p>${escapeHTML(issue.building)} · ${escapeHTML(issue.location_details)}</p>
            <p>${escapeHTML(dateText(issue.created_at))}</p>
          </div>
          <span class="pill ${priorityClass(issue.priority_level)}">
            ${escapeHTML(issue.priority_level)}
          </span>
        </div>
      `).join("")
    );
  } catch (error) {
    setHTML(
      "#recentIssues",
      `<div class="empty-state">${escapeHTML(error.message)}. Check that the backend is running.</div>`
    );
  }
}

// ISSUE MANAGEMENT

async function loadIssues() {
  const table = $("#issuesTable");
  if (!table) return;

  table.innerHTML =
    '<tr><td colspan="6" class="empty-state">Loading issues...</td></tr>';

  const params = new URLSearchParams();

  const status = $("#filterStatus")?.value || "";
  const priority = $("#filterPriority")?.value || "";
  const query = $("#issueSearch")?.value.trim() || "";

  if (status) params.set("status", status);
  if (priority) params.set("priority", priority);
  if (query) params.set("q", query);

  try {
    const result = await api(`/issues?${params.toString()}`);

    currentIssues = result.issues || [];

    setText(
      "#issueCount",
      `${result.total} report${result.total === 1 ? "" : "s"} found`
    );

    if (!currentIssues.length) {
      table.innerHTML =
        '<tr><td colspan="6" class="empty-state">No matching issues found.</td></tr>';
      return;
    }

    table.innerHTML = currentIssues.map((issue) => `
      <tr>
        <td>
          <strong>${escapeHTML(issue.title)}</strong>
          <small>${escapeHTML(issue.category)}</small>
        </td>
        <td>
          ${escapeHTML(issue.building)}
          <br><small>${escapeHTML(issue.location_details)}</small>
        </td>
        <td>
          <span class="pill ${priorityClass(issue.priority_level)}">
            ${escapeHTML(issue.priority_level)}
          </span>
          <br><small>Score: ${number(issue.priority_score)}</small>
        </td>
        <td>
          <span class="pill ${statusClass(issue.status)}">${escapeHTML(issue.status)}</span>
        </td>
        <td>${escapeHTML(dateText(issue.created_at))}</td>
        <td>
          <button class="table-action" data-open-issue="${issue.id}">
            Manage →
          </button>
        </td>
      </tr>
    `).join("");
  } catch (error) {
    table.innerHTML =
      `<tr><td colspan="6" class="empty-state">${escapeHTML(error.message)}</td></tr>`;
  }
}

$("#refreshIssues")?.addEventListener("click", loadIssues);
$("#filterStatus")?.addEventListener("change", loadIssues);
$("#filterPriority")?.addEventListener("change", loadIssues);

$("#issueSearch")?.addEventListener("input", () => {
  clearTimeout(searchDelay);
  searchDelay = setTimeout(loadIssues, 300);
});

$("#issuesTable")?.addEventListener("click", (event) => {
  const button = event.target.closest("[data-open-issue]");

  if (button) {
    openIssue(Number(button.dataset.openIssue));
  }
});

// ISSUE DETAILS AND AI ANALYSIS

async function openIssue(id) {
  selectedIssueId = id;

  try {
    const data = await api(`/issues/${id}`);
    const issue = data.issue;

    setText("#modalTitle", issue.title);

    const missingInformation = Array.isArray(
      issue.ai_missing_information
    )
      ? issue.ai_missing_information
      : [];

    const aiSection = `
      <div class="modal-section">
        <h3>EcoPulse AI Analysis</h3>

        <div class="detail-grid">
          <div class="detail-box">
            <span>Analysis status</span>
            <strong>
              ${issue.ai_analyzed
                ? "Gemini analyzed"
                : "Rule-based fallback"}
            </strong>
          </div>

          <div class="detail-box">
            <span>AI urgency</span>
            <strong>${escapeHTML(issue.ai_urgency || "Unknown")}</strong>
          </div>
        </div>

        <h3>Explanation</h3>
        <p>${escapeHTML(
          issue.ai_explanation ||
          "No AI explanation is available for this report."
        )}</p>

        <h3>AI-suggested action</h3>
        <p>${escapeHTML(
          issue.ai_recommended_action ||
          "No AI-suggested action is available for this report."
        )}</p>

        <h3>Additional information needed</h3>

        ${
          missingInformation.length
            ? `<ul>${missingInformation.map((item) =>
                `<li>${escapeHTML(item)}</li>`
              ).join("")}</ul>`
            : '<p class="small muted">No additional information was flagged by the AI.</p>'
        }

        <p class="small muted">
          AI analysis is advisory. It does not replace physical inspection
          or professional safety assessment.
        </p>
      </div>
    `;

    const details = `
      <div class="detail-grid">
        <div class="detail-box">
          <span>Category</span>
          <strong>${escapeHTML(issue.category)}</strong>
        </div>

        <div class="detail-box">
          <span>Priority / score</span>
          <strong>${escapeHTML(issue.priority_level)} · ${number(issue.priority_score)}</strong>
        </div>

        <div class="detail-box">
          <span>Building</span>
          <strong>${escapeHTML(issue.building)}</strong>
        </div>

        <div class="detail-box">
          <span>Location</span>
          <strong>${escapeHTML(issue.location_details)}</strong>
        </div>

        <div class="detail-box">
          <span>Status</span>
          <strong>${escapeHTML(issue.status)}</strong>
        </div>

        <div class="detail-box">
          <span>Reported</span>
          <strong>${escapeHTML(dateText(issue.created_at))}</strong>
        </div>

        <div class="detail-box">
          <span>Severity / safety risk</span>
          <strong>${issue.severity}/5 · ${issue.safety_risk}/5</strong>
        </div>

        <div class="detail-box">
          <span>Estimated resource loss</span>
          <strong>${number(issue.estimated_resource_loss)}</strong>
        </div>
      </div>

      <div class="modal-section">
        <h3>Description</h3>
        <p>${escapeHTML(issue.description)}</p>
      </div>

      ${aiSection}

      <div class="modal-section">
        <h3>Official recommended action</h3>
        <p>${escapeHTML(issue.recommended_action)}</p>
        <p class="small muted">
          ${(issue.priority_reasons || []).map(escapeHTML).join(" · ")}
        </p>
      </div>

      <div class="modal-section">
        <h3>Status history</h3>
        ${
          (data.history || []).length
            ? data.history.map((item) => `
                <div class="health-row">
                  <span>
                    ${escapeHTML(item.previous_status || "New")}
                    → ${escapeHTML(item.new_status)}
                  </span>
                  <span class="small muted">
                    ${escapeHTML(dateText(item.changed_at))}
                  </span>
                </div>
                ${item.notes
                  ? `<p class="small muted">${escapeHTML(item.notes)}</p>`
                  : ""}
              `).join("")
            : '<p class="muted small">No status history.</p>'
        }
      </div>

      <div class="modal-section">
        <h3>Repair records</h3>
        ${
          (data.repairs || []).length
            ? data.repairs.map((repair) => `
                <div class="detail-box">
                  <strong>${escapeHTML(repair.repair_action)}</strong>
                  <p>${escapeHTML(repair.completion_notes || "No additional notes.")}</p>
                  <span>
                    ${repair.confirmed ? "Confirmed" : "Not confirmed"}
                    · ${escapeHTML(dateText(repair.completed_at))}
                  </span>
                </div>
              `).join("")
            : '<p class="small muted">No repair records yet.</p>'
        }
      </div>

      <div class="modal-section">
        <h3>Update status</h3>
        ${statusControls(issue)}
      </div>

      ${issue.status === "In Progress" ? repairFormHTML() : ""}
    `;

    setHTML("#modalContent", details);
    $("#issueModal")?.classList.remove("hidden");
  } catch (error) {
    showNotice(error.message, true);
  }
}

function statusControls(issue) {
  const next = {
    Reported: ["Acknowledged"],
    Acknowledged: ["In Progress"],
    "In Progress": [],
    Resolved: ["Reopened"],
    Reopened: ["Acknowledged", "In Progress"]
  }[issue.status] || [];

  if (!next.length) {
    return `<p class="small muted">${
      issue.status === "In Progress"
        ? "Submit a repair verification below to resolve this issue."
        : "No direct status transition available."
    }</p>`;
  }

  return `
    <div class="form-grid-inner">
      <label class="field">
        Next status
        <select id="nextStatus">
          ${next.map((status) =>
            `<option value="${escapeHTML(status)}">${escapeHTML(status)}</option>`
          ).join("")}
        </select>
      </label>

      <label class="field">
        Notes
        <input id="statusNotes" maxlength="1000" placeholder="Optional update note">
      </label>

      <div class="full">
        <button class="btn btn-primary" id="saveStatus">
          Update status
        </button>
      </div>
    </div>
  `;
}

function repairFormHTML() {
  return `
    <form id="repairForm" class="repair-form">
      <h3>Repair verification</h3>

      <label class="field">
        Repair action
        <input name="repair_action" required minlength="3" maxlength="500"
          placeholder="What was repaired?">
      </label>

      <label class="field">
        Completion notes
        <textarea name="completion_notes" maxlength="1500" rows="3"
          placeholder="Describe the repair and any follow-up needed"></textarea>
      </label>

      <label class="field">
        Estimated repair cost (₹)
        <input name="estimated_repair_cost" type="number" min="0"
          max="1000000" step="any" value="0" required>
      </label>

      <label class="checkbox-field">
        <input name="confirmed" type="checkbox">
        I confirm that the repair has been completed
      </label>

      <p class="small muted">
        Only confirm after the repair has actually been inspected.
        This prototype does not independently verify physical repairs.
      </p>

      <button class="btn btn-primary" type="submit">
        Save repair record
      </button>
    </form>
  `;
}

$("#modalContent")?.addEventListener("click", async (event) => {
  if (!event.target.closest("#saveStatus")) return;

  const status = $("#nextStatus")?.value;
  const notes = $("#statusNotes")?.value || "";

  try {
    await api(`/issues/${selectedIssueId}/status`, {
      method: "PATCH",
      body: JSON.stringify({ status, notes })
    });

    showNotice("Issue status updated.");
    await refreshAfterIssueChange();
    await openIssue(selectedIssueId);
  } catch (error) {
    showNotice(error.message, true);
  }
});

$("#modalContent")?.addEventListener("submit", async (event) => {
  if (event.target.id !== "repairForm") return;

  event.preventDefault();

  const form = new FormData(event.target);

  const payload = {
    repair_action: form.get("repair_action"),
    completion_notes: form.get("completion_notes"),
    estimated_repair_cost: Number(form.get("estimated_repair_cost")),
    confirmed: form.has("confirmed")
  };

  try {
    await api(`/issues/${selectedIssueId}/repair-verification`, {
      method: "POST",
      body: JSON.stringify(payload)
    });

    showNotice(
      payload.confirmed
        ? "Repair recorded and issue marked resolved."
        : "Repair record saved. Issue remains in progress."
    );

    await refreshAfterIssueChange();
    await openIssue(selectedIssueId);
  } catch (error) {
    showNotice(error.message, true);
  }
});

$("#closeModal")?.addEventListener("click", () => {
  $("#issueModal")?.classList.add("hidden");
});

$("#issueModal")?.addEventListener("click", (event) => {
  if (event.target.id === "issueModal") {
    $("#issueModal").classList.add("hidden");
  }
});

document.addEventListener("keydown", (event) => {
  if (event.key === "Escape") {
    $("#issueModal")?.classList.add("hidden");
    $("#sidebar")?.classList.remove("open");
  }
});

async function refreshAfterIssueChange() {
  await Promise.all([
    loadOverview(),
    loadIssues(),
    loadAnalytics()
  ]);
}

// REPORT AN ISSUE AND GEMINI RESULTS

$("#reportForm")?.addEventListener("submit", async (event) => {
  event.preventDefault();

  const formElement = event.currentTarget;
  const form = new FormData(formElement);
  const payload = Object.fromEntries(form.entries());

  payload.severity = Number(payload.severity);
  payload.safety_risk = Number(payload.safety_risk);
  payload.estimated_resource_loss =
    Number(payload.estimated_resource_loss || 0);
  payload.unresolved_hours = Number(payload.unresolved_hours || 0);
  payload.near_electrical = form.has("near_electrical");

  const button = event.submitter;

  if (button) {
    button.disabled = true;
    button.textContent = "Analyzing and submitting...";
  }

  try {
    const result = await api("/issues", {
      method: "POST",
      body: JSON.stringify(payload)
    });

    const aiStatus = result.ai?.analyzed
      ? `Gemini analyzed the report. Urgency: ${result.ai.urgency || "Unknown"}.`
      : "Report saved using rule-based fallback.";

    showNotice(
      `Report #${result.issue.id} created. Priority: ${result.issue.priority_level}. ${aiStatus}`
    );

    formElement.reset();
    navigate("issues");

    await Promise.all([
      loadOverview(),
      loadIssues()
    ]);

    await openIssue(result.issue.id);
  } catch (error) {
    showNotice(error.message, true);
  } finally {
    if (button) {
      button.disabled = false;
      button.textContent = "Submit report";
    }
  }
});

// QR LOCATION PREFILL
function applyLocationPrefill() {
  const params = new URLSearchParams(window.location.search);

  const building = (params.get("building") || "").trim();
  const location = (params.get("location") || "")
    .replace(/\s+/g, " ")
    .trim();

  // If the URL has no QR location details,
  // keep the normal dashboard behavior.
  if (!building && !location) {
    return;
  }

  // Find the building and location fields.
  const buildingField = $("#reportBuilding");
  const locationField = $("#reportLocation");

  // Fill the fields when they exist.
  if (buildingField && building) {
    buildingField.value = building;
  }

  if (locationField && location) {
    locationField.value = location;
  }

  // Navigate directly to the report page.
  navigate("report");

  // Inform the user that the location was filled.
  showNotice(
    `Campus location prefilled: ${
      building && location
        ? `${building} · ${location}`
        : building || location
    }`
  );
}

// IMPACT SIMULATOR HELPERS

function readPositiveNumber(formData, name, label, allowZero = false) {
  const raw = formData.get(name);

  if (raw === null || String(raw).trim() === "") {
    throw new Error(`${label} is required.`);
  }

  const value = Number(raw);

  if (
    !Number.isFinite(value) ||
    (allowZero ? value < 0 : value <= 0)
  ) {
    throw new Error(
      `${label} must be ${allowZero ? "zero or greater" : "greater than zero"}.`
    );
  }

  return value;
}

// WATER CONSERVATION

function calculateWaterLocally() {
  const form = $("#waterForm");
  if (!form) return;

  const rate = Number(
    form.elements.namedItem("leakage_litres_per_hour")?.value
  );

  const hours = Number(
    form.elements.namedItem("hours_avoided")?.value
  );

  if (
    !Number.isFinite(rate) || rate < 0 ||
    !Number.isFinite(hours) || hours < 0
  ) {
    setHTML("#waterResult", `— <small>L</small>`);
    setText("#waterFormula", "Enter a valid leakage rate and number of hours.");
    return;
  }

  const saved = rate * hours;

  setHTML("#waterResult", `${number(saved)} <small>L</small>`);
  setText(
    "#waterFormula",
    `${number(rate)} L/hour × ${number(hours)} hours = ${number(saved)} L. Estimate only.`
  );
  setText(
    "#waterExtra",
    `Potential leakage prevented: ${number(saved)} litres. Actual savings depend on the leak and repair.`
  );
}

$("#waterForm")?.addEventListener("input", calculateWaterLocally);

$("#waterForm")?.addEventListener("submit", async (event) => {
  event.preventDefault();

  const form = new FormData(event.currentTarget);

  let rate;
  let hours;

  try {
    rate = readPositiveNumber(
      form,
      "leakage_litres_per_hour",
      "Leakage rate"
    );

    hours = readPositiveNumber(
      form,
      "hours_avoided",
      "Hours of leakage avoided"
    );
  } catch (error) {
    showNotice(error.message, true);
    return;
  }

  const estimate = rate * hours;

  calculateWaterLocally();

  try {
    const result = await api("/simulate/water", {
      method: "POST",
      body: JSON.stringify({
        leakage_litres_per_hour: rate,
        hours_avoided: hours
      })
    });

    const backendSaved =
      result?.potential_water_saved_litres ??
      result?.estimated_water_saved_litres ??
      result?.litres_saved;

    const saved =
      backendSaved !== undefined &&
      backendSaved !== null &&
      Number.isFinite(Number(backendSaved))
        ? Number(backendSaved)
        : estimate;

    setHTML("#waterResult", `${number(saved)} <small>L</small>`);
    setText(
      "#waterFormula",
      `${number(rate)} L/hour × ${number(hours)} hours = ${number(saved)} L. Estimate only.`
    );
    setText(
      "#waterExtra",
      `Potential leakage prevented: ${number(saved)} litres. Actual savings depend on the leak and repair.`
    );
  } catch (error) {
    showNotice(
      `Water estimate calculated locally. Server error: ${error.message}`,
      true
    );
  }
});

// ELECTRICITY CONSERVATION

function calculateElectricityLocally() {
  const form = $("#electricityForm");
  if (!form) return;

  const getValue = (name) =>
    Number(form.elements.namedItem(name)?.value);

  const power = getValue("power_kw_per_device");
  const devices = getValue("device_count");
  const hours = getValue("hours_avoided");
  const tariff = getValue("tariff_per_kwh");
  const factor = getValue("emission_factor");

  if (
    ![power, devices, hours, tariff, factor].every(Number.isFinite) ||
    power < 0 || devices < 0 || hours < 0 ||
    tariff < 0 || factor < 0
  ) {
    return;
  }

  const energy = power * devices * hours;

  setHTML("#energyResult", `${number(energy)} <small>kWh</small>`);
  setHTML("#costResult", `₹${number(energy * tariff)}`);
  setText("#emissionsResult", `${number(energy * factor)} kg`);
  setText(
    "#electricityFormula",
    `${number(power)} kW × ${number(devices)} devices × ${number(hours)} hours = ${number(energy)} kWh. Estimate only.`
  );
}

$("#electricityForm")?.addEventListener(
  "input",
  calculateElectricityLocally
);

$("#electricityForm")?.addEventListener("submit", async (event) => {
  event.preventDefault();

  const form = new FormData(event.currentTarget);

  let power;
  let devices;
  let hours;
  let tariff;
  let factor;

  try {
    power = readPositiveNumber(
      form, "power_kw_per_device", "Power per device"
    );
    devices = readPositiveNumber(
      form, "device_count", "Number of devices"
    );
    hours = readPositiveNumber(
      form, "hours_avoided", "Hours avoided"
    );
    tariff = readPositiveNumber(
      form, "tariff_per_kwh", "Electricity tariff", true
    );
    factor = readPositiveNumber(
      form, "emission_factor", "Emission factor", true
    );

    if (!Number.isInteger(devices)) {
      throw new Error("Number of devices must be a whole number.");
    }
  } catch (error) {
    showNotice(error.message, true);
    return;
  }

  const energy = power * devices * hours;
  const cost = energy * tariff;
  const emissions = energy * factor;

  calculateElectricityLocally();

  try {
    const result = await api("/simulate/electricity", {
      method: "POST",
      body: JSON.stringify({
        power_kw_per_device: power,
        device_count: devices,
        hours_avoided: hours,
        tariff_per_kwh: tariff,
        emission_factor: factor
      })
    });

    const serverEnergy = Number(result?.energy_saved_kwh);
    const serverCost = Number(result?.cost_saved);
    const serverEmissions = Number(result?.emissions_avoided_kg_co2e);

    const finalEnergy = Number.isFinite(serverEnergy)
      ? serverEnergy
      : energy;

    const finalCost = Number.isFinite(serverCost)
      ? serverCost
      : cost;

    const finalEmissions = Number.isFinite(serverEmissions)
      ? serverEmissions
      : emissions;

    setHTML("#energyResult", `${number(finalEnergy)} <small>kWh</small>`);
    setHTML("#costResult", `₹${number(finalCost)}`);
    setText("#emissionsResult", `${number(finalEmissions)} kg`);
  } catch (error) {
    showNotice(
      `Electricity estimate calculated locally. Server error: ${error.message}`,
      true
    );
  }
});

// PLASTIC WASTE REDUCTION

// Illustrative weights in grams, not verified measurements.
const plasticWeightsGrams = {
  bottle: 20,
  cup: 5,
  bag: 5,
  straw: 0.5,
  wrapper: 2
};

function selectedPlasticWeight() {
  const type = $("#plasticType")?.value || "bottle";

  if (type === "custom") {
    return Number($("#customWeight")?.value || 0);
  }

  return plasticWeightsGrams[type] ?? plasticWeightsGrams.bottle;
}

function updatePlasticAssumption() {
  const type = $("#plasticType")?.value || "bottle";
  const customField = $("#customWeightField");
  const customInput = $("#customWeight");

  if (customField) {
    customField.hidden = type !== "custom";
  }

  if (customInput) {
    customInput.required = type === "custom";
  }

  const weight = selectedPlasticWeight();

  setText(
    "#plasticWeightAssumption",
    Number.isFinite(weight) && weight > 0
      ? `${number(weight, 3)} g`
      : "Enter a valid weight"
  );
}

function calculatePlasticLocally() {
  const form = $("#plasticForm");
  if (!form) return;

  const countInput =
    $("#plasticItems") ||
    form.elements.namedItem("items_avoided");

  const count = Number(countInput?.value || 0);
  const weight = selectedPlasticWeight();

  updatePlasticAssumption();

  if (
    !Number.isFinite(count) ||
    !Number.isInteger(count) ||
    count <= 0 ||
    !Number.isFinite(weight) ||
    weight <= 0
  ) {
    setText("#plasticResult", "—");
    setText("#plasticMassResult", "—");
    setText("#plasticAlternativeResult", "—");
    setText(
      "#plasticFormula",
      "Enter a positive item count and valid weight."
    );
    return;
  }

  const totalKg = count * weight / 1000;

  setText("#plasticResult", number(count, 0));
  setText("#plasticMassResult", `${number(totalKg, 4)} kg`);
  setText("#plasticAlternativeResult", `${number(count, 0)} uses`);
  setText(
    "#plasticFormula",
    `${number(count, 0)} items × ${number(weight, 3)} g/item = ${number(totalKg, 4)} kg of estimated plastic avoided. Estimate only.`
  );
}

$("#plasticType")?.addEventListener("change", calculatePlasticLocally);
$("#plasticItems")?.addEventListener("input", calculatePlasticLocally);
$("#customWeight")?.addEventListener("input", calculatePlasticLocally);
$("#plasticForm")?.addEventListener("input", calculatePlasticLocally);

$("#plasticForm")?.addEventListener("submit", async (event) => {
  event.preventDefault();

  const form = new FormData(event.currentTarget);

  let count;

  try {
    count = readPositiveNumber(
      form,
      "items_avoided",
      "Items avoided"
    );

    if (!Number.isInteger(count)) {
      throw new Error("Items avoided must be a whole number.");
    }

    const weight = selectedPlasticWeight();

    if (!Number.isFinite(weight) || weight <= 0) {
      throw new Error("Enter a valid plastic item weight.");
    }
  } catch (error) {
    showNotice(error.message, true);
    return;
  }

  calculatePlasticLocally();

  try {
    const result = await api("/simulate/plastic", {
      method: "POST",
      body: JSON.stringify({
        items_avoided: count
      })
    });

    const serverCount = Number(result?.single_use_items_avoided);

    if (Number.isFinite(serverCount) && serverCount >= 0) {
      setText("#plasticResult", number(serverCount, 0));
    }
  } catch (error) {
    showNotice(
      `Plastic estimate calculated locally. Server error: ${error.message}`,
      true
    );
  }
});

// INITIAL SIMULATOR RESULTS

function setInitialSimulatorResults() {
  calculateWaterLocally();
  calculateElectricityLocally();
  calculatePlasticLocally();
}

// QR LOCATIONS

async function loadLocations() {
  const list = $("#locationsList");
  if (!list) return;

  try {
    const result = await api("/locations");
    locations = result.locations || [];

    if (!locations.length) {
      list.innerHTML =
        '<div class="empty-state">No campus locations yet. Add your first location above.</div>';
      return;
    }

    list.innerHTML = locations.map((location) => `
      <div class="location-item">
        <div>
          <strong>
            ${escapeHTML(location.building_name)} · ${escapeHTML(location.location_name)}
          </strong>
          <small>
            ${escapeHTML(location.location_details || "No additional details")}
          </small>
        </div>
        <button class="btn btn-secondary" data-qr-location="${location.id}">
          Generate QR
        </button>
      </div>
    `).join("");
  } catch (error) {
    list.innerHTML =
      `<div class="empty-state">${escapeHTML(error.message)}</div>`;
  }
}

$("#locationForm")?.addEventListener("submit", async (event) => {
  event.preventDefault();

  const form = new FormData(event.currentTarget);

  const payload = {
    building_name: String(form.get("building_name") || "").trim(),
    location_name: String(form.get("location_name") || "").trim(),
    location_details: String(form.get("location_details") || "").trim()
  };

  try {
    await api("/locations", {
      method: "POST",
      body: JSON.stringify(payload)
    });

    event.currentTarget.reset();
    showNotice("Campus location registered.");
    await loadLocations();
  } catch (error) {
    showNotice(error.message, true);
  }
});

$("#locationsList")?.addEventListener("click", async (event) => {
  const button = event.target.closest("[data-qr-location]");
  if (!button) return;

  const id = Number(button.dataset.qrLocation);
  const location = locations.find((item) => item.id === id);

  if (!location) return;

  try {
    const response = await fetch(`${API}/locations/${id}/qr`);

    if (!response.ok) {
      throw new Error("Unable to generate the QR code.");
    }

    const blob = await response.blob();
    const objectURL = URL.createObjectURL(blob);

    setHTML(
      "#qrPreview",
      `
        <img
          src="${objectURL}"
          alt="QR code for ${escapeHTML(location.building_name)} - ${escapeHTML(location.location_name)}"
        >
        <strong>${escapeHTML(location.building_name)}</strong>
        <p>${escapeHTML(location.location_name)}</p>
      `
    );

    const download = $("#qrDownload");

    if (download) {
      download.href = objectURL;
      download.download = `ecopulse-location-${id}.png`;
      download.classList.remove("disabled-link");
    }

    showNotice("QR code generated.");
  } catch (error) {
    showNotice(error.message, true);
  }
});

// ANALYTICS

function makeChart(id, type, labels, values, label) {
  if (charts[id]) {
    charts[id].destroy();
    delete charts[id];
  }

  const canvas = document.getElementById(id);

  if (!canvas || typeof Chart === "undefined") return;

  charts[id] = new Chart(canvas, {
    type,
    data: {
      labels,
      datasets: [{
        label,
        data: values,
        backgroundColor: type === "line"
          ? "rgba(47, 191, 134, 0.14)"
          : [
              "#2FBF86",
              "#20394F",
              "#7B9CB5",
              "#E8B85A",
              "#D97575",
              "#92C9B0",
              "#9B8BC4"
            ],
        borderColor: type === "line" ? "#2FBF86" : "#FFFFFF",
        borderWidth: type === "line" ? 2 : 1,
        pointRadius: type === "line" ? 3 : 0,
        fill: type === "line",
        tension: 0.3
      }]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        legend: {
          display: type !== "bar" && type !== "line"
        },
        tooltip: {
          enabled: true
        }
      },
      scales: type === "doughnut" ? {} : {
        y: {
          beginAtZero: true,
          ticks: { precision: 0 }
        },
        x: {
          grid: { display: false }
        }
      }
    }
  });
}

async function loadAnalytics() {
  try {
    const summary = await api("/dashboard/summary");

    setText("#analyticsRepairs", number(summary.confirmed_repairs, 0));

    setText(
      "#analyticsResolution",
      `${summary.total_issues
        ? Math.round(
            summary.resolved_issues / summary.total_issues * 100
          )
        : 0}%`
    );

    setText(
      "#analyticsCategories",
      number((summary.by_category || []).length, 0)
    );

    setText(
      "#analyticsCritical",
      number(
        (summary.by_priority || [])
          .filter((item) => item.priority_level === "Critical")
          .reduce((sum, item) => sum + item.count, 0),
        0
      )
    );

    makeChart(
      "statusChart",
      "doughnut",
      (summary.by_status || []).map((item) => item.status),
      (summary.by_status || []).map((item) => item.count),
      "Issues"
    );

    makeChart(
      "priorityChart",
      "bar",
      (summary.by_priority || []).map((item) => item.priority_level),
      (summary.by_priority || []).map((item) => item.count),
      "Issues"
    );

    makeChart(
      "categoryChart",
      "bar",
      (summary.by_category || []).map((item) => item.category),
      (summary.by_category || []).map((item) => item.count),
      "Issues"
    );

    const dailyMap = new Map(
      (summary.daily_reports || []).map((item) => [
        item.date,
        item.count
      ])
    );

    const dates = [];

    for (let i = 6; i >= 0; i--) {
      const date = new Date();
      date.setDate(date.getDate() - i);

      const key = [
        date.getFullYear(),
        String(date.getMonth() + 1).padStart(2, "0"),
        String(date.getDate()).padStart(2, "0")
      ].join("-");

      dates.push({
        key,
        label: date.toLocaleDateString("en-IN", {
          day: "2-digit",
          month: "short"
        })
      });
    }

    makeChart(
      "dailyChart",
      "line",
      dates.map((item) => item.label),
      dates.map((item) => dailyMap.get(item.key) || 0),
      "Reports"
    );
  } catch (error) {
    showNotice(`Analytics could not load: ${error.message}`, true);
  }
}

$("#refreshAnalytics")?.addEventListener("click", loadAnalytics);

// STARTUP

async function initializeApp() {
  setInitialSimulatorResults();
  await checkHealth();
  await loadOverview();
  applyLocationPrefill();
}

initializeApp();
