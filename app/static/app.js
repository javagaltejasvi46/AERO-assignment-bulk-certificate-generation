// Bulk Certificate Generator client controller

// Application State
const state = {
  recipients: [
    { name: "Alice Johnson", email: "alice.johnson@example.com" },
    { name: "Bob Smith", email: "bob.smith@example.com" },
    { name: "Charlie Vance", email: "charlie.vance@example.com" },
  ],
  activeJobId: null,
  activeJobData: null,
  pollingTimer: null,
  isPollingEnabled: true,
  currentTab: "create",
  certFilter: "all",
  searchQuery: "",
};

// DOM Elements Cache
const DOM = {
  // Navigation
  navTabs: document.querySelectorAll(".nav-tab-btn"),
  views: document.querySelectorAll(".tab-view"),
  liveDot: document.getElementById("live-indicator-dot"),
  serverStatusPill: document.getElementById("server-status-pill"),
  serverStatusText: document.getElementById("server-status-text"),

  // Metadata Inputs
  courseInput: document.getElementById("course-name-input"),
  issuerInput: document.getElementById("issuer-name-input"),
  descInput: document.getElementById("cert-desc-input"),

  // Recipient Controls
  recipientCountBadge: document.getElementById("recipient-count-badge"),
  btnModeTable: document.getElementById("btn-mode-table"),
  btnModeBulk: document.getElementById("btn-mode-bulk"),
  panelModeTable: document.getElementById("panel-mode-table"),
  panelModeBulk: document.getElementById("panel-mode-bulk"),
  recipientsTbody: document.getElementById("recipients-table-body"),
  btnAddRow: document.getElementById("btn-add-row"),
  bulkTextarea: document.getElementById("bulk-textarea"),
  btnParseBulk: document.getElementById("btn-parse-bulk"),
  csvFileInput: document.getElementById("csv-file-input"),
  btnDownloadSampleCsv: document.getElementById("btn-download-sample-csv"),

  // Presets
  btnSampleDevs: document.getElementById("load-sample-devs"),
  btnSampleBootcamp: document.getElementById("load-sample-bootcamp"),
  btnSampleEdge: document.getElementById("load-sample-edge"),
  btnClearAll: document.getElementById("clear-all-recipients"),

  // Submission
  btnSubmitJob: document.getElementById("btn-submit-job"),
  submitBtnText: document.getElementById("submit-btn-text"),

  // Preview Card
  previewIssuerText: document.getElementById("preview-issuer-text"),
  previewCourseText: document.getElementById("preview-course-text"),
  previewDescText: document.getElementById("preview-desc-text"),
  previewRecipientName: document.getElementById("preview-recipient-name"),
  previewDate: document.getElementById("preview-date"),
  previewCertId: document.getElementById("preview-cert-id"),

  // Live Monitor
  monitorJobId: document.getElementById("monitor-job-id"),
  btnCopyJobId: document.getElementById("btn-copy-job-id"),
  manualJobIdInput: document.getElementById("manual-job-id-input"),
  btnLoadManualJob: document.getElementById("btn-load-manual-job"),
  monitorJobCourse: document.getElementById("monitor-job-course"),
  monitorJobIssuer: document.getElementById("monitor-job-issuer"),
  monitorJobDesc: document.getElementById("monitor-job-desc"),
  monitorStatusBadge: document.getElementById("monitor-status-badge"),
  monitorStatusText: document.getElementById("monitor-status-text"),
  btnPollRefresh: document.getElementById("btn-poll-refresh"),
  refreshSpinIcon: document.getElementById("refresh-spin-icon"),
  chkAutoPoll: document.getElementById("chk-auto-poll"),
  btnDownloadZip: document.getElementById("btn-download-zip"),
  progressStatusDesc: document.getElementById("progress-status-desc"),
  progressPercentVal: document.getElementById("progress-percent-val"),
  liquidProgressFill: document.getElementById("liquid-progress-fill"),

  // Metrics
  metricTotal: document.getElementById("metric-total"),
  metricCompleted: document.getElementById("metric-completed"),
  metricFailed: document.getElementById("metric-failed"),
  metricRate: document.getElementById("metric-rate"),

  // Certificates Table
  certsCountPill: document.getElementById("certs-count-pill"),
  filterPills: document.querySelectorAll(".filter-pill"),
  certSearchInput: document.getElementById("cert-search-input"),
  certsDataTbody: document.getElementById("certs-data-tbody"),

  // History Tab
  jobsHistoryTbody: document.getElementById("jobs-history-tbody"),
  btnRefreshHistory: document.getElementById("btn-refresh-history"),

  // Modal Preview
  modal: document.getElementById("pdf-preview-modal"),
  modalTitle: document.getElementById("modal-cert-title"),
  modalCertId: document.getElementById("modal-cert-id"),
  modalIframe: document.getElementById("pdf-preview-iframe"),
  modalDirectDownload: document.getElementById("modal-direct-download"),
  btnCloseModal: document.getElementById("btn-close-modal"),

  // Toast
  toastHost: document.getElementById("toast-host"),
};

// ==========================================================================
// INITIALIZATION
// ==========================================================================
document.addEventListener("DOMContentLoaded", () => {
  renderRecipientsTable();
  updateLivePreview();
  setupEventListeners();
  checkServerHealth();
  loadJobHistory();
  checkUrlJobParam();
});

// ==========================================================================
// EVENT LISTENERS SETUP
// ==========================================================================
function setupEventListeners() {
  // Navigation Tabs
  DOM.navTabs.forEach((btn) => {
    btn.addEventListener("click", () => {
      const targetTab = btn.getAttribute("data-tab");
      switchTab(targetTab);
    });
  });

  // Metadata real-time preview updates
  DOM.courseInput.addEventListener("input", updateLivePreview);
  DOM.issuerInput.addEventListener("input", updateLivePreview);
  if (DOM.descInput) DOM.descInput.addEventListener("input", updateLivePreview);

  // Input Mode Toggle
  DOM.btnModeTable.addEventListener("click", () => setInputMode("table"));
  DOM.btnModeBulk.addEventListener("click", () => setInputMode("bulk"));

  // Add & Clear Recipients
  DOM.btnAddRow.addEventListener("click", () => {
    state.recipients.push({ name: "", email: "" });
    renderRecipientsTable();
    // Focus the newly added name input
    const inputs = DOM.recipientsTbody.querySelectorAll(".input-name");
    if (inputs.length > 0) inputs[inputs.length - 1].focus();
  });

  DOM.btnClearAll.addEventListener("click", () => {
    state.recipients = [];
    renderRecipientsTable();
    updateLivePreview();
    showToast("Cleared all recipients", "info");
  });

  // Presets
  DOM.btnSampleDevs.addEventListener("click", () => {
    state.recipients = [
      { name: "Alice Johnson", email: "alice.johnson@techdev.org" },
      { name: "Bob Smith", email: "bob.smith@techdev.org" },
      { name: "Charlie Vance", email: "charlie.vance@techdev.org" },
    ];
    renderRecipientsTable();
    updateLivePreview();
    showToast("Loaded 3 Dev Cohort preset", "success");
  });

  DOM.btnSampleBootcamp.addEventListener("click", () => {
    state.recipients = [
      { name: "Elena Rostova", email: "elena@bootcamp.io" },
      { name: "Marcus Aurelius Vance", email: "marcus@bootcamp.io" },
      { name: "Aria Montgomery", email: "aria@bootcamp.io" },
      { name: "Devon Chen", email: "devon@bootcamp.io" },
      { name: "Priya Sharma", email: "priya@bootcamp.io" },
      { name: "Liam O'Connor", email: "liam@bootcamp.io" },
      { name: "Sophia Rodriguez", email: "sophia@bootcamp.io" },
      { name: "Lucas Dubois", email: "lucas@bootcamp.io" },
      { name: "Fatima Al-Sayed", email: "fatima@bootcamp.io" },
      { name: "Kai Takahashi", email: "kai@bootcamp.io" },
    ];
    renderRecipientsTable();
    updateLivePreview();
    showToast("Loaded 10 Students batch preset", "success");
  });

  DOM.btnSampleEdge.addEventListener("click", () => {
    state.recipients = [
      { name: "José Müller-Thurgau", email: "jose@domain.eu" },
      { name: "François René de Chateaubriand", email: "francois@paris.fr" },
      { name: "Dr. Elizabeth Alexandra Mary-Windsor, Ph.D.", email: "queen@royal.uk" },
      { name: "Avery & Morgan & Associates Co.", email: "" },
    ];
    renderRecipientsTable();
    updateLivePreview();
    showToast("Loaded Unicode accents & edge-case names", "success");
  });

  // Bulk Text / CSV Parse
  DOM.btnParseBulk.addEventListener("click", parseBulkTextarea);
  DOM.csvFileInput.addEventListener("change", handleCsvUpload);
  if (DOM.btnDownloadSampleCsv) {
    DOM.btnDownloadSampleCsv.addEventListener("click", downloadSampleCsv);
  }

  // Submit Job
  DOM.btnSubmitJob.addEventListener("click", submitGenerationJob);

  // Monitor Controls
  DOM.btnPollRefresh.addEventListener("click", () => {
    if (state.activeJobId) {
      spinRefreshIcon();
      pollJobStatus(state.activeJobId);
    } else {
      showToast("No active job selected. Select one from Job Archives or create a batch.", "info");
    }
  });

  DOM.chkAutoPoll.addEventListener("change", (e) => {
    state.isPollingEnabled = e.target.checked;
    if (state.isPollingEnabled && state.activeJobId && isJobRunning()) {
      startPolling(state.activeJobId);
    } else {
      stopPolling();
    }
  });

  DOM.btnCopyJobId.addEventListener("click", () => {
    if (state.activeJobId) {
      navigator.clipboard.writeText(state.activeJobId);
      showToast("Job ID copied to clipboard!", "info");
    } else {
      showToast("No active job ID to copy.", "info");
    }
  });

  if (DOM.btnLoadManualJob) {
    DOM.btnLoadManualJob.addEventListener("click", handleManualJobLookup);
  }
  if (DOM.manualJobIdInput) {
    DOM.manualJobIdInput.addEventListener("keydown", (e) => {
      if (e.key === "Enter") handleManualJobLookup();
    });
  }

  DOM.btnDownloadZip.addEventListener("click", () => {
    if (state.activeJobId) {
      window.location.href = `/api/jobs/${state.activeJobId}/download`;
      showToast("Preparing ZIP archive download...", "info");
    }
  });

  // Certificate Filters & Search
  DOM.filterPills.forEach((pill) => {
    pill.addEventListener("click", () => {
      DOM.filterPills.forEach((p) => p.classList.remove("active"));
      pill.classList.add("active");
      state.certFilter = pill.getAttribute("data-filter");
      renderCertificatesTable();
    });
  });

  DOM.certSearchInput.addEventListener("input", (e) => {
    state.searchQuery = e.target.value.toLowerCase().trim();
    renderCertificatesTable();
  });

  // Job History
  DOM.btnRefreshHistory.addEventListener("click", loadJobHistory);

  // Modal
  DOM.btnCloseModal.addEventListener("click", closeModal);
  DOM.modal.addEventListener("click", (e) => {
    if (e.target === DOM.modal) closeModal();
  });
  document.addEventListener("keydown", (e) => {
    if (e.key === "Escape" && !DOM.modal.classList.contains("hidden")) {
      closeModal();
    }
  });
}

// ==========================================================================
// TAB SWITCHING
// ==========================================================================
function switchTab(tabId) {
  state.currentTab = tabId;

  DOM.navTabs.forEach((btn) => {
    if (btn.getAttribute("data-tab") === tabId) {
      btn.classList.add("active");
    } else {
      btn.classList.remove("active");
    }
  });

  DOM.views.forEach((view) => {
    if (view.id === `view-${tabId}`) {
      view.classList.add("active");
    } else {
      view.classList.remove("active");
    }
  });

  if (tabId === "history") {
    loadJobHistory();
  }
}

// ==========================================================================
// RECIPIENT MANAGEMENT & TABLE BUILDER
// ==========================================================================
function setInputMode(mode) {
  if (mode === "table") {
    DOM.btnModeTable.classList.add("active");
    DOM.btnModeBulk.classList.remove("active");
    DOM.panelModeTable.classList.remove("hidden");
    DOM.panelModeBulk.classList.add("hidden");
  } else {
    DOM.btnModeBulk.classList.add("active");
    DOM.btnModeTable.classList.remove("active");
    DOM.panelModeBulk.classList.remove("hidden");
    DOM.panelModeTable.classList.add("hidden");
  }
}

function renderRecipientsTable() {
  DOM.recipientsTbody.innerHTML = "";

  state.recipients.forEach((recipient, index) => {
    const tr = document.createElement("tr");

    tr.innerHTML = `
      <td style="color: var(--text-muted); font-family: var(--font-mono); font-size: 12px;">${index + 1}</td>
      <td>
        <input type="text" class="table-input input-name" placeholder="Recipient Full Name" value="${escapeHtml(recipient.name)}" data-index="${index}" />
      </td>
      <td>
        <input type="email" class="table-input input-email" placeholder="email@address.com" value="${escapeHtml(recipient.email || "")}" data-index="${index}" />
      </td>
      <td style="text-align: center;">
        <button type="button" class="table-row-delete-btn" data-index="${index}" title="Remove row">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" class="micro-icon"><line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/></svg>
        </button>
      </td>
    `;

    // Row input listeners
    const nameInput = tr.querySelector(".input-name");
    const emailInput = tr.querySelector(".input-email");
    const delBtn = tr.querySelector(".table-row-delete-btn");

    nameInput.addEventListener("input", (e) => {
      state.recipients[index].name = e.target.value;
      if (index === 0) updateLivePreview();
      updateRecipientCount();
    });

    nameInput.addEventListener("focus", () => {
      if (state.recipients[index].name) {
        DOM.previewRecipientName.textContent = state.recipients[index].name;
      }
    });

    emailInput.addEventListener("input", (e) => {
      state.recipients[index].email = e.target.value;
    });

    delBtn.addEventListener("click", () => {
      state.recipients.splice(index, 1);
      renderRecipientsTable();
      updateLivePreview();
    });

    DOM.recipientsTbody.appendChild(tr);
  });

  updateRecipientCount();
}

function updateRecipientCount() {
  const count = state.recipients.filter((r) => r.name && r.name.trim() !== "").length;
  DOM.recipientCountBadge.textContent = `${count} recipient${count === 1 ? "" : "s"}`;
}

// Bulk text parse
function parseBulkTextarea() {
  const rawText = DOM.bulkTextarea.value.trim();
  if (!rawText) {
    showToast("Please paste text before parsing", "error");
    return;
  }

  const lines = rawText.split("\n");
  const parsed = [];

  for (let line of lines) {
    line = line.trim();
    if (!line) continue;

    // Check for comma, semicolon, or tab separator
    let parts = [];
    if (line.includes(",")) {
      parts = line.split(",");
    } else if (line.includes("\t")) {
      parts = line.split("\t");
    } else if (line.includes(";")) {
      parts = line.split(";");
    } else {
      parts = [line];
    }

    const name = parts[0].trim().replace(/^["']|["']$/g, "");
    let email = (parts[1] || "").trim().replace(/^["']|["']$/g, "");

    // Ignore CSV header row if present
    if (parsed.length === 0 && (name.toLowerCase() === "name" || name.toLowerCase() === "full name") && (!email || email.toLowerCase().includes("email"))) {
      continue;
    }

    if (name) {
      parsed.push({ name, email });
    }
  }

  if (parsed.length > 0) {
    state.recipients = parsed;
    renderRecipientsTable();
    updateLivePreview();
    setInputMode("table");
    showToast(`Successfully parsed ${parsed.length} recipients`, "success");
  } else {
    showToast("Could not parse valid recipients from text", "error");
  }
}

// CSV File Upload
function handleCsvUpload(event) {
  const file = event.target.files[0];
  if (!file) return;

  const reader = new FileReader();
  reader.onload = (e) => {
    DOM.bulkTextarea.value = e.target.result;
    parseBulkTextarea();
  };
  reader.readAsText(file);
  event.target.value = "";
}

function downloadSampleCsv() {
  const sampleCsv = `Name,Email\nAlice Johnson,alice.johnson@example.com\nBob Smith,bob.smith@example.com\nCharlie Vance,charlie.vance@example.com\nDr. Elena Rostova,elena.rostova@research.org\n`;
  const blob = new Blob([sampleCsv], { type: "text/csv;charset=utf-8;" });
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = "recipients_sample.csv";
  document.body.appendChild(a);
  a.click();
  document.body.removeChild(a);
  URL.revokeObjectURL(url);
  showToast("Downloaded sample recipients CSV template", "info");
}

// ==========================================================================
// LIVE TEMPLATE PREVIEW
// ==========================================================================
function updateLivePreview() {
  const course = DOM.courseInput.value.trim() || "Certificate of Completion";
  const issuer = DOM.issuerInput.value.trim() || "Global Tech Academy";
  const desc = DOM.descInput
    ? (DOM.descInput.value.trim() || "has successfully mastered all prescribed coursework and criteria for")
    : "has successfully mastered all prescribed coursework and criteria for";

  DOM.previewCourseText.textContent = course;
  DOM.previewIssuerText.textContent = issuer.toUpperCase();
  if (DOM.previewDescText) DOM.previewDescText.textContent = desc;

  const firstValid = state.recipients.find((r) => r.name && r.name.trim() !== "");
  DOM.previewRecipientName.textContent = firstValid ? firstValid.name : "Recipient Full Name";

  const today = new Date().toLocaleDateString("en-US", {
    year: "numeric",
    month: "short",
    day: "numeric",
  });
  DOM.previewDate.textContent = `Date: ${today}`;
}

// ==========================================================================
// SUBMIT BATCH JOB (ASYNC API CALL)
// ==========================================================================
async function submitGenerationJob() {
  const validRecipients = state.recipients.filter(
    (r) => r.name && r.name.trim() !== ""
  );

  if (validRecipients.length === 0) {
    showToast("Please add at least one recipient with a name.", "error");
    return;
  }

  if (validRecipients.length > 500) {
    showToast("Maximum 500 recipients allowed per batch job.", "error");
    return;
  }

  // Check email formats if provided
  for (const r of validRecipients) {
    if (r.email && r.email.trim() !== "") {
      const parts = r.email.split("@");
      if (parts.length !== 2 || !parts[1].includes(".")) {
        showToast(`Invalid email '${r.email}' for recipient ${r.name}`, "error");
        return;
      }
    }
  }

  const payload = {
    recipients: validRecipients.map((r) => ({
      name: r.name.trim(),
      email: r.email && r.email.trim() !== "" ? r.email.trim() : null,
    })),
    course_name: DOM.courseInput.value.trim() || "Certificate of Completion",
    issuer_name: DOM.issuerInput.value.trim() || "Organization",
    description: DOM.descInput && DOM.descInput.value.trim()
      ? DOM.descInput.value.trim()
      : "has successfully mastered all prescribed coursework and criteria for",
  };

  setSubmittingState(true);

  try {
    const response = await fetch("/api/jobs", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });

    if (!response.ok) {
      const errData = await response.json().catch(() => ({}));
      const detail = errData.detail || "Server rejected request";
      let errMsg = "Server rejected request";
      if (Array.isArray(detail)) {
        errMsg = detail
          .map((d) => (d.msg ? d.msg.replace(/^Value error,\s*/i, "") : JSON.stringify(d)))
          .join("; ");
      } else if (typeof detail === "string") {
        errMsg = detail;
      } else {
        errMsg = JSON.stringify(detail);
      }
      throw new Error(errMsg);
    }

    const data = await response.json();
    showToast(`Job queued! ID: ${data.job_id}`, "success");

    // Load active job into tracker
    state.activeJobId = data.job_id;
    switchTab("monitor");
    DOM.chkAutoPoll.checked = true;
    state.isPollingEnabled = true;

    // Immediately poll and start interval
    await pollJobStatus(data.job_id);
    startPolling(data.job_id);
  } catch (err) {
    showToast(`Error creating job: ${err.message}`, "error");
  } finally {
    setSubmittingState(false);
  }
}

function setSubmittingState(isSubmitting) {
  DOM.btnSubmitJob.disabled = isSubmitting;
  DOM.submitBtnText.textContent = isSubmitting
    ? "Enqueuing Background Work..."
    : "Generate Certificates Now";
}

// ==========================================================================
// LIVE POLLING & PROGRESS TRACKER
// ==========================================================================
function startPolling(jobId) {
  stopPolling();
  DOM.liveDot.style.display = "inline-block";

  state.pollingTimer = setInterval(async () => {
    if (!state.isPollingEnabled) return;
    await pollJobStatus(jobId);
  }, 1500);
}

function stopPolling() {
  if (state.pollingTimer) {
    clearInterval(state.pollingTimer);
    state.pollingTimer = null;
  }
  DOM.liveDot.style.display = "none";
}

async function handleManualJobLookup() {
  const inputId = DOM.manualJobIdInput.value.trim();
  if (!inputId) {
    showToast("Please enter a 12-character Job ID", "error");
    return;
  }
  try {
    spinRefreshIcon();
    const response = await fetch(`/api/jobs/${inputId}`);
    if (!response.ok) {
      throw new Error(`Job '${inputId}' was not found`);
    }
    const job = await response.json();
    state.activeJobId = job.id;
    state.activeJobData = job;
    updateMonitorView(job);
    DOM.manualJobIdInput.value = "";
    showToast(`Loaded Job ${job.id}`, "success");
    if (job.status === "running" || job.status === "pending") {
      startPolling(job.id);
    }
  } catch (err) {
    showToast(err.message, "error");
  }
}

function checkUrlJobParam() {
  const params = new URLSearchParams(window.location.search);
  const jobId = params.get("job") || params.get("job_id");
  if (jobId) {
    state.activeJobId = jobId;
    switchTab("monitor");
    pollJobStatus(jobId);
    startPolling(jobId);
  }
}

function isJobRunning() {
  if (!state.activeJobData) return false;
  return (
    state.activeJobData.status === "pending" ||
    state.activeJobData.status === "running"
  );
}

async function pollJobStatus(jobId) {
  try {
    const response = await fetch(`/api/jobs/${jobId}`);
    if (!response.ok) {
      throw new Error(`Failed to fetch job ${jobId}`);
    }

    const job = await response.json();
    state.activeJobData = job;
    updateMonitorView(job);

    // If job is finished, halt auto-polling
    if (job.status === "done" || job.status === "failed") {
      stopPolling();
      DOM.btnDownloadZip.disabled = job.completed === 0;
      if (job.status === "done") {
        showToast(
          `Batch completed! ${job.completed} generated, ${job.failed} failed.`,
          "success"
        );
      }
    }
  } catch (err) {
    console.error("Poll error:", err);
  }
}

function updateMonitorView(job) {
  DOM.monitorJobId.textContent = job.id;
  DOM.monitorJobCourse.textContent = job.course_name || "Untitled Certificate";
  DOM.monitorJobIssuer.textContent = `Issuer: ${job.issuer_name || "—"}`;
  if (DOM.monitorJobDesc) {
    DOM.monitorJobDesc.textContent = job.description || "";
  }

  // Status Badge
  DOM.monitorStatusBadge.className = `status-badge-lg status-${job.status}`;
  DOM.monitorStatusText.textContent = job.status.toUpperCase();

  // Metrics
  const total = job.total_certificates || 0;
  const completed = job.completed || 0;
  const failed = job.failed || 0;
  const processed = completed + failed;
  const percent = total > 0 ? Math.round((processed / total) * 100) : 0;
  const rate = processed > 0 ? Math.round((completed / processed) * 100) : 0;

  DOM.metricTotal.textContent = total;
  DOM.metricCompleted.textContent = completed;
  DOM.metricFailed.textContent = failed;
  DOM.metricRate.textContent = `${rate}%`;

  // Progress Bar
  DOM.liquidProgressFill.style.width = `${percent}%`;
  DOM.progressPercentVal.textContent = `${percent}%`;
  DOM.progressStatusDesc.textContent =
    job.status === "done"
      ? "All certificates processed"
      : job.status === "running"
      ? `Processing certificates (${processed}/${total})...`
      : `Queued in worker pool (${total} total)`;

  // ZIP download button state
  DOM.btnDownloadZip.disabled = completed === 0;

  // Render Certificates List
  renderCertificatesTable();
}

function renderCertificatesTable() {
  if (!state.activeJobData || !state.activeJobData.certificates) {
    return;
  }

  let certs = state.activeJobData.certificates;

  // Filter by status pill
  if (state.certFilter !== "all") {
    certs = certs.filter((c) => c.status === state.certFilter);
  }

  // Filter by search query
  if (state.searchQuery) {
    certs = certs.filter((c) => {
      const name = (c.recipient_name || "").toLowerCase();
      const email = (c.recipient_email || "").toLowerCase();
      const id = (c.id || "").toLowerCase();
      return (
        name.includes(state.searchQuery) ||
        email.includes(state.searchQuery) ||
        id.includes(state.searchQuery)
      );
    });
  }

  DOM.certsCountPill.textContent = `${certs.length} certs`;
  DOM.certsDataTbody.innerHTML = "";

  if (certs.length === 0) {
    const tr = document.createElement("tr");
    tr.innerHTML = `
      <td colspan="6" style="text-align: center; padding: 32px; color: var(--text-muted);">
        No certificates match the current filter or search.
      </td>
    `;
    DOM.certsDataTbody.appendChild(tr);
    return;
  }

  certs.forEach((cert) => {
    const tr = document.createElement("tr");
    const isSuccess = cert.status === "success";
    const dateStr = cert.created_at
      ? new Date(cert.created_at).toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" })
      : "—";

    tr.innerHTML = `
      <td><code class="cert-id-tag">${cert.id}</code></td>
      <td style="font-weight: 600;">${escapeHtml(cert.recipient_name)}</td>
      <td style="color: var(--text-secondary);">${escapeHtml(cert.recipient_email || "—")}</td>
      <td>
        <span class="status-pill-table ${cert.status}">
          ${cert.status}
        </span>
        ${cert.error_message ? `<div style="font-size: 11px; color: var(--accent-rose); margin-top: 3px;">${escapeHtml(cert.error_message)}</div>` : ""}
      </td>
      <td style="color: var(--text-muted); font-size: 12px;">${dateStr}</td>
      <td style="text-align: right;">
        <div class="actions-cell">
          ${
            isSuccess
              ? `
            <button type="button" class="action-icon-btn btn-preview-cert" data-id="${cert.id}" data-name="${escapeHtml(cert.recipient_name)}">
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" class="mini-icon"><path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z"/><circle cx="12" cy="12" r="3"/></svg>
              <span>Preview</span>
            </button>
            <a href="/api/certificates/${cert.id}/download" download class="action-icon-btn">
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" class="mini-icon"><path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/><polyline points="7 10 12 15 17 10"/><line x1="12" y1="15" x2="12" y2="3"/></svg>
              <span>PDF</span>
            </a>
          `
              : `<span style="font-size: 11.5px; color: var(--text-muted);">Unavailable</span>`
          }
        </div>
      </td>
    `;

    // Preview click
    const previewBtn = tr.querySelector(".btn-preview-cert");
    if (previewBtn) {
      previewBtn.addEventListener("click", () => {
        openPdfPreview(cert.id, cert.recipient_name);
      });
    }

    DOM.certsDataTbody.appendChild(tr);
  });
}

// ==========================================================================
// JOB ARCHIVES & HISTORY
// ==========================================================================
async function loadJobHistory() {
  DOM.jobsHistoryTbody.innerHTML = `
    <tr><td colspan="7" style="text-align: center; padding: 24px; color: var(--text-muted);">Loading job archives...</td></tr>
  `;

  try {
    const res = await fetch("/api/jobs?limit=50");
    if (!res.ok) throw new Error("Failed to load historical jobs");

    const jobs = await res.json();
    DOM.jobsHistoryTbody.innerHTML = "";

    if (!jobs || jobs.length === 0) {
      DOM.jobsHistoryTbody.innerHTML = `
        <tr><td colspan="7" style="text-align: center; padding: 32px; color: var(--text-muted);">No job records found in database.</td></tr>
      `;
      return;
    }

    jobs.forEach((job) => {
      const tr = document.createElement("tr");
      const createdStr = job.created_at
        ? new Date(job.created_at).toLocaleDateString("en-US", {
            month: "short",
            day: "numeric",
            hour: "2-digit",
            minute: "2-digit",
          })
        : "—";

      tr.innerHTML = `
        <td><code class="history-badge">${job.id}</code></td>
        <td style="font-weight: 600;">${escapeHtml(job.course_name || "—")}</td>
        <td style="color: var(--text-secondary);">${escapeHtml(job.issuer_name || "—")}</td>
        <td>
          <span style="font-weight: 600;">${job.completed}</span>
          <span style="color: var(--text-muted);">/ ${job.total_certificates}</span>
          ${job.failed > 0 ? `<span style="color: var(--accent-rose); font-size: 11px;">(${job.failed} failed)</span>` : ""}
        </td>
        <td><span class="status-pill-table ${job.status}">${job.status}</span></td>
        <td style="color: var(--text-muted); font-size: 12px;">${createdStr}</td>
        <td style="text-align: right;">
          <div class="actions-cell">
            <button type="button" class="action-icon-btn btn-load-job" data-id="${job.id}">
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" class="mini-icon"><circle cx="12" cy="12" r="10"/><polyline points="12 6 12 12 16 14"/></svg>
              <span>Inspect</span>
            </button>
            ${
              job.completed > 0
                ? `<a href="/api/jobs/${job.id}/download" download class="action-icon-btn" title="Download ZIP">
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" class="mini-icon"><path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/><polyline points="7 10 12 15 17 10"/><line x1="12" y1="15" x2="12" y2="3"/></svg>
                <span>ZIP</span>
              </a>`
                : ""
            }
          </div>
        </td>
      `;

      tr.querySelector(".btn-load-job").addEventListener("click", () => {
        state.activeJobId = job.id;
        switchTab("monitor");
        pollJobStatus(job.id);
        if (job.status === "running" || job.status === "pending") {
          startPolling(job.id);
        }
      });

      DOM.jobsHistoryTbody.appendChild(tr);
    });
  } catch (err) {
    DOM.jobsHistoryTbody.innerHTML = `
      <tr><td colspan="7" style="text-align: center; padding: 24px; color: var(--accent-rose);">Error: ${err.message}</td></tr>
    `;
  }
}

// ==========================================================================
// MODAL PDF PREVIEW
// ==========================================================================
function openPdfPreview(certId, recipientName) {
  const downloadUrl = `/api/certificates/${certId}/download`;
  DOM.modalTitle.textContent = `${recipientName} — Certificate`;
  DOM.modalCertId.textContent = `Certificate ID: ${certId}`;
  DOM.modalIframe.src = downloadUrl;
  DOM.modalDirectDownload.href = downloadUrl;
  DOM.modalDirectDownload.setAttribute("download", `certificate_${certId}.pdf`);

  DOM.modal.classList.remove("hidden");
}

function closeModal() {
  DOM.modal.classList.add("hidden");
  DOM.modalIframe.src = "about:blank";
}

// ==========================================================================
// TOAST NOTIFICATIONS & UTILITIES
// ==========================================================================
function showToast(message, type = "info") {
  const toast = document.createElement("div");
  toast.className = `glass-toast toast-${type}`;

  const iconSvg =
    type === "success"
      ? `<svg viewBox="0 0 24 24" fill="none" stroke="#34d399" stroke-width="2" class="mini-icon"><polyline points="20 6 9 17 4 12"/></svg>`
      : type === "error"
      ? `<svg viewBox="0 0 24 24" fill="none" stroke="#f87171" stroke-width="2" class="mini-icon"><circle cx="12" cy="12" r="10"/><line x1="15" y1="9" x2="9" y2="15"/><line x1="9" y1="9" x2="15" y2="15"/></svg>`
      : `<svg viewBox="0 0 24 24" fill="none" stroke="#00f2fe" stroke-width="2" class="mini-icon"><circle cx="12" cy="12" r="10"/><line x1="12" y1="16" x2="12" y2="12"/><line x1="12" y1="8" x2="12.01" y2="8"/></svg>`;

  toast.innerHTML = `${iconSvg}<span>${escapeHtml(message)}</span>`;
  DOM.toastHost.appendChild(toast);

  setTimeout(() => {
    toast.style.opacity = "0";
    toast.style.transform = "translateX(40px)";
    toast.style.transition = "all 0.3s ease";
    setTimeout(() => toast.remove(), 300);
  }, 4200);
}

function spinRefreshIcon() {
  DOM.refreshSpinIcon.style.transition = "transform 0.5s ease";
  DOM.refreshSpinIcon.style.transform = "rotate(360deg)";
  setTimeout(() => {
    DOM.refreshSpinIcon.style.transition = "none";
    DOM.refreshSpinIcon.style.transform = "rotate(0deg)";
  }, 500);
}

async function checkServerHealth() {
  try {
    const res = await fetch("/api/health");
    if (!res.ok) {
      // Try root if /api/health not mounted yet
      await fetch("/");
    }
    DOM.serverStatusPill.style.display = "flex";
  } catch (err) {
    DOM.serverStatusText.textContent = "Offline";
    DOM.serverStatusPill.style.borderColor = "rgba(244, 63, 94, 0.4)";
    DOM.serverStatusPill.style.color = "#f87171";
  }
}

function escapeHtml(str) {
  if (!str) return "";
  return String(str)
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;")
    .replace(/'/g, "&#039;");
}
