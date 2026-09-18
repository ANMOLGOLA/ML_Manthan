// LendGuard AI - Loan Processing & Risk Audit System Client Logic

let CURRENT_APPLICATIONS = [];
let SAMPLE_PRESETS = [];
let SELECTED_APP_ID = null;

document.addEventListener("DOMContentLoaded", () => {
    initNavigation();
    initPresets();
    initDropzone();
    loadDashboardData();

    document.getElementById("btn-reseed").addEventListener("click", reseedData);
    document.getElementById("btn-refresh").addEventListener("click", loadDashboardData);
    document.getElementById("btn-process-input").addEventListener("click", processManualInput);
    document.getElementById("filter-status").addEventListener("change", renderQueueTable);
    document.getElementById("filter-risk").addEventListener("change", renderQueueTable);
    document.getElementById("global-search").addEventListener("input", filterApplications);
});

// Tab Navigation
function initNavigation() {
    const navItems = document.querySelectorAll(".nav-item");
    const tabs = document.querySelectorAll(".tab-content");

    navItems.forEach(item => {
        item.addEventListener("click", () => {
            const targetTab = item.getAttribute("data-tab");
            
            navItems.forEach(n => n.classList.remove("active"));
            tabs.forEach(t => t.classList.remove("active"));

            item.classList.add("active");
            document.getElementById(`tab-${targetTab}`).classList.add("active");
        });
    });
}

// Preset samples
function initPresets() {
    SAMPLE_PRESETS = [
        {
            applicant_id: "APP-PRESET-001",
            applicant_name: "Clean Profile Applicant",
            tax_id: "PAN-ABCD1234E",
            stated_monthly_income: 10000.0,
            claimed_existing_emi: 1000.0,
            requested_loan_amount: 100000.0,
            proposed_monthly_emi: 1500.0,
            salary_credits_3m: [10000.0, 10000.0, 10200.0],
            existing_emi_debits_3m: [1000.0, 1000.0, 1000.0],
            recurring_debits_3m: [1200.0, 1100.0, 1150.0],
            application_date: "2026-09-15",
            statement_end_date: "2026-09-10"
        },
        {
            applicant_id: "APP-PRESET-002",
            applicant_name: "Inflated Salary Applicant",
            tax_id: "SSN-990-11-2244",
            stated_monthly_income: 15000.0,
            claimed_existing_emi: 800.0,
            requested_loan_amount: 250000.0,
            proposed_monthly_emi: 3500.0,
            salary_credits_3m: [8000.0, 8100.0, 7900.0],
            existing_emi_debits_3m: [800.0, 800.0, 800.0],
            recurring_debits_3m: [1400.0, 1500.0, 1450.0],
            application_date: "2026-09-16",
            statement_end_date: "2026-09-12"
        },
        {
            applicant_id: "APP-PRESET-003",
            applicant_name: "Undeclared EMI Risk Profile",
            tax_id: "PAN-UNEMI5582K",
            stated_monthly_income: 7000.0,
            claimed_existing_emi: 300.0,
            requested_loan_amount: 200000.0,
            proposed_monthly_emi: 2800.0,
            salary_credits_3m: [7000.0, 7000.0, 7000.0],
            existing_emi_debits_3m: [2500.0, 2500.0, 2500.0],
            recurring_debits_3m: [1200.0, 1300.0, 1250.0],
            application_date: "2026-09-17",
            statement_end_date: "2026-09-10"
        },
        {
            applicant_id: "APP-PRESET-004",
            applicant_name: "Stale Document Profile",
            tax_id: "SSN-881-22-9900",
            stated_monthly_income: 9000.0,
            claimed_existing_emi: 1100.0,
            requested_loan_amount: 150000.0,
            proposed_monthly_emi: 2000.0,
            salary_credits_3m: [9000.0, 9000.0, 9000.0],
            existing_emi_debits_3m: [1100.0, 1100.0, 1100.0],
            application_date: "2026-09-18",
            statement_end_date: "2026-03-01"
        },
        {
            applicant_id: "APP-PRESET-005",
            applicant_name: "Corrupted PDF Sample",
            corrupted: true,
            extraction_failed: true,
            failure_reason: "OCR stream corrupt / low DPI scan"
        }
    ];
}

function loadSamplePreset(index) {
    const preset = SAMPLE_PRESETS[index];
    document.getElementById("json-editor").value = JSON.stringify(preset, null, 2);
}

// Drag & Drop
function initDropzone() {
    const dropzone = document.getElementById("dropzone");
    const fileInput = document.getElementById("file-input");

    dropzone.addEventListener("dragover", (e) => {
        e.preventDefault();
        dropzone.classList.add("drag-over");
    });

    dropzone.addEventListener("dragleave", () => {
        dropzone.classList.remove("drag-over");
    });

    dropzone.addEventListener("drop", (e) => {
        e.preventDefault();
        dropzone.classList.remove("drag-over");
        if (e.dataTransfer.files.length > 0) {
            handleFileUpload(e.dataTransfer.files[0]);
        }
    });

    fileInput.addEventListener("change", (e) => {
        if (e.target.files.length > 0) {
            handleFileUpload(e.target.files[0]);
        }
    });
}

function handleFileUpload(file) {
    const reader = new FileReader();
    reader.onload = (e) => {
        const text = e.target.result;
        document.getElementById("json-editor").value = text;
    };
    reader.readAsText(file);
}

// Fetch dashboard data
async function loadDashboardData() {
    try {
        const [analyticsRes, appsRes] = await Promise.all([
            fetch("/api/analytics"),
            fetch("/api/applications")
        ]);

        const analytics = await analyticsRes.json();
        CURRENT_APPLICATIONS = await appsRes.json();

        renderKPIs(analytics);
        renderRecentTable(CURRENT_APPLICATIONS);
        renderInsights(analytics.inconsistency_breakdown || {});
        renderQueueTable();
    } catch (err) {
        console.error("Error loading dashboard data:", err);
    }
}

function renderKPIs(data) {
    document.getElementById("kpi-total").innerText = data.total_applications || 0;
    document.getElementById("kpi-approved").innerText = data.approved || 0;
    document.getElementById("kpi-flagged").innerText = data.flagged || 0;
    document.getElementById("kpi-manual").innerText = data.manual_review || 0;
    document.getElementById("kpi-dti").innerText = `${data.average_dti || 0}%`;

    const queueCount = (data.flagged || 0) + (data.manual_review || 0);
    document.getElementById("badge-queue-count").innerText = queueCount;
}

function renderRecentTable(apps) {
    const tbody = document.getElementById("tbody-recent");
    tbody.innerHTML = "";

    apps.slice(0, 5).forEach(app => {
        const tr = document.createElement("tr");
        const statedInc = app.extracted_data.stated_monthly_income || 0;
        const bankInc = app.calculated_metrics.average_salary || 0;

        tr.innerHTML = `
            <td><strong>${app.application_id}</strong></td>
            <td>${app.applicant_name}</td>
            <td>$${statedInc.toLocaleString()} vs $${bankInc.toLocaleString()}</td>
            <td><strong>${app.calculated_metrics.dti_ratio}%</strong></td>
            <td><span class="risk-${app.risk_level.toLowerCase()}">${app.risk_level}</span></td>
            <td><span class="badge-status status-${getStatusClass(app.status)}">${app.status}</span></td>
            <td>
                <button class="btn btn-sm btn-outline" onclick="openAuditModal('${app.application_id}')">
                    <i class="fa-solid fa-eye"></i> View Audit
                </button>
            </td>
        `;
        tbody.appendChild(tr);
    });
}

function renderInsights(incMap) {
    const container = document.getElementById("insights-container");
    container.innerHTML = "";

    const keys = Object.keys(incMap);
    if (keys.length === 0) {
        container.innerHTML = `<p style="color: var(--text-muted); text-align: center;">No inconsistencies detected across applications.</p>`;
        return;
    }

    keys.forEach(key => {
        const count = incMap[key];
        const div = document.createElement("div");
        div.className = "evidence-box medium";
        div.innerHTML = `
            <div class="evidence-header">
                <span>${key}</span>
                <span class="badge" style="background: var(--accent-amber); color: #000;">${count} Occurrences</span>
            </div>
            <div class="evidence-desc">Rule trigger counter across current document audit records.</div>
        `;
        container.appendChild(div);
    });
}

function renderQueueTable() {
    const statusFilter = document.getElementById("filter-status").value;
    const riskFilter = document.getElementById("filter-risk").value;

    let filtered = CURRENT_APPLICATIONS;

    if (statusFilter) {
        filtered = filtered.filter(a => a.status.toUpperCase() === statusFilter.toUpperCase());
    }
    if (riskFilter) {
        filtered = filtered.filter(a => a.risk_level.toUpperCase() === riskFilter.toUpperCase());
    }

    const tbody = document.getElementById("tbody-queue");
    tbody.innerHTML = "";

    if (filtered.length === 0) {
        tbody.innerHTML = `<tr><td colspan="7" style="text-align: center; color: var(--text-muted);">No loan applications match the selected filter.</td></tr>`;
        return;
    }

    filtered.forEach(app => {
        const tr = document.createElement("tr");
        tr.innerHTML = `
            <td><strong>${app.application_id}</strong></td>
            <td>${app.applicant_name}</td>
            <td><span class="badge" style="background: rgba(255,255,255,0.1);">${app.inconsistencies.length} Flags</span></td>
            <td>${app.calculated_metrics.dti_ratio}%</td>
            <td><span class="risk-${app.risk_level.toLowerCase()}">${app.risk_level}</span></td>
            <td><span class="badge-status status-${getStatusClass(app.status)}">${app.status}</span></td>
            <td>
                <button class="btn btn-sm btn-primary" onclick="openAuditModal('${app.application_id}')">
                    <i class="fa-solid fa-signature"></i> Audit & Action
                </button>
            </td>
        `;
        tbody.appendChild(tr);
    });
}

function getStatusClass(status) {
    switch (status) {
        case "APPROVED": return "approved";
        case "FLAGGED": return "flagged";
        case "MANUAL_REVIEW": return "manual";
        case "REJECTED": return "rejected";
        default: return "flagged";
    }
}

// Process Input
async function processManualInput() {
    const rawVal = document.getElementById("json-editor").value.trim();
    if (!rawVal) {
        alert("Please enter or select a JSON loan document payload first.");
        return;
    }

    try {
        let payload;
        try {
            payload = JSON.parse(rawVal);
        } catch (e) {
            payload = { raw_text: rawVal };
        }

        const res = await fetch("/api/process", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(payload)
        });

        const record = await res.json();
        renderAuditOutputCard(record);
        loadDashboardData();
    } catch (err) {
        alert("Error processing input: " + err.message);
    }
}

function renderAuditOutputCard(record) {
    document.getElementById("result-empty").classList.add("hidden");
    const detailBox = document.getElementById("result-detail");
    detailBox.classList.remove("hidden");

    const badge = document.getElementById("result-status-badge");
    badge.innerText = record.status;
    badge.className = `badge-status status-${getStatusClass(record.status)}`;

    let incHtml = "";
    if (record.inconsistencies.length === 0) {
        incHtml = `<div class="evidence-box low">
            <div class="evidence-header"><i class="fa-solid fa-circle-check"></i> Clean Verification</div>
            <div class="evidence-desc">No inconsistencies detected. Salary, dates, and DTI ratios pass all rule checks.</div>
        </div>`;
    } else {
        record.inconsistencies.forEach(inc => {
            incHtml += `
                <div class="evidence-box ${inc.severity.toLowerCase()}">
                    <div class="evidence-header">
                        <span><i class="fa-solid fa-triangle-exclamation"></i> ${inc.title}</span>
                        <span>[${inc.severity}]</span>
                    </div>
                    <div class="evidence-desc">${inc.description}</div>
                    <div class="evidence-values">
                        <span>Expected: <strong>${inc.expected_value}</strong></span>
                        <span>Actual: <strong>${inc.actual_value}</strong></span>
                    </div>
                </div>
            `;
        });
    }

    detailBox.innerHTML = `
        <h4><i class="fa-solid fa-user"></i> ${record.applicant_name} (${record.application_id})</h4>
        <p style="font-size: 13px; color: var(--text-secondary); margin-bottom: 16px;">${record.routing_reason}</p>
        
        <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 12px; margin-bottom: 20px;">
            <div style="background: rgba(0,0,0,0.2); padding: 12px; border-radius: 8px;">
                <span style="font-size: 11px; color: var(--text-muted);">Avg Bank Income</span>
                <h4 style="color: var(--accent-green);">$${record.calculated_metrics.average_salary.toLocaleString()}</h4>
            </div>
            <div style="background: rgba(0,0,0,0.2); padding: 12px; border-radius: 8px;">
                <span style="font-size: 11px; color: var(--text-muted);">DTI Ratio</span>
                <h4 style="color: var(--accent-purple);">${record.calculated_metrics.dti_ratio}%</h4>
            </div>
        </div>

        <h5><i class="fa-solid fa-link"></i> Evidence Chain (${record.inconsistencies.length} Flags):</h5>
        <div style="margin-top: 10px;">${incHtml}</div>
    `;
}

// Modal open/close
function openAuditModal(appId) {
    SELECTED_APP_ID = appId;
    const record = CURRENT_APPLICATIONS.find(a => a.application_id === appId);
    if (!record) return;

    document.getElementById("modal-app-title").innerText = `${record.applicant_name} (${record.application_id})`;
    const statusBadge = document.getElementById("modal-app-status");
    statusBadge.innerText = record.status;
    statusBadge.className = `badge-status status-${getStatusClass(record.status)}`;

    const body = document.getElementById("modal-app-body");
    
    let incHtml = "";
    record.inconsistencies.forEach(inc => {
        incHtml += `
            <div class="evidence-box ${inc.severity.toLowerCase()}">
                <div class="evidence-header">
                    <span>${inc.title}</span>
                    <span class="risk-${inc.severity.toLowerCase()}">${inc.severity}</span>
                </div>
                <div class="evidence-desc">${inc.description}</div>
                <div class="evidence-values">
                    <span>Source: ${inc.source_document}</span>
                    <span>Expected: ${inc.expected_value}</span>
                    <span>Actual: ${inc.actual_value}</span>
                </div>
            </div>
        `;
    });

    body.innerHTML = `
        <div style="margin-bottom: 20px;">
            <p><strong>Routing Reason:</strong> ${record.routing_reason}</p>
        </div>

        <div style="display: grid; grid-template-columns: repeat(3, 1fr); gap: 14px; margin-bottom: 24px;">
            <div style="background: rgba(255,255,255,0.03); padding: 12px; border-radius: 8px;">
                <span style="font-size: 12px; color: var(--text-muted);">Stated Salary</span>
                <h4>$${(record.extracted_data.stated_monthly_income || 0).toLocaleString()}</h4>
            </div>
            <div style="background: rgba(255,255,255,0.03); padding: 12px; border-radius: 8px;">
                <span style="font-size: 12px; color: var(--text-muted);">Verified Bank Salary</span>
                <h4 style="color: var(--accent-green);">$${record.calculated_metrics.average_salary.toLocaleString()}</h4>
            </div>
            <div style="background: rgba(255,255,255,0.03); padding: 12px; border-radius: 8px;">
                <span style="font-size: 12px; color: var(--text-muted);">Total Monthly EMI</span>
                <h4 style="color: var(--accent-amber);">$${record.calculated_metrics.total_emi.toLocaleString()}</h4>
            </div>
        </div>

        <h3><i class="fa-solid fa-link"></i> Inconsistency Evidence Chain</h3>
        <div style="margin-top: 14px;">${incHtml || "<p>No inconsistencies present.</p>"}</div>
    `;

    document.getElementById("modal-notes").value = record.reviewer_notes || "";
    document.getElementById("audit-modal").classList.remove("hidden");
}

function closeAuditModal() {
    document.getElementById("audit-modal").classList.add("hidden");
    SELECTED_APP_ID = null;
}

async function executeReviewAction(action) {
    if (!SELECTED_APP_ID) return;
    const notes = document.getElementById("modal-notes").value;

    try {
        await fetch(`/api/applications/${SELECTED_APP_ID}/review`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ action: action, reviewer_notes: notes })
        });

        closeAuditModal();
        loadDashboardData();
    } catch (err) {
        alert("Action failed: " + err.message);
    }
}

async function reseedData() {
    await fetch("/api/seed");
    loadDashboardData();
}

function triggerPipelineDemo(stage) {
    const nodes = document.querySelectorAll(".node-box");
    nodes.forEach(n => n.style.borderColor = "");
    const target = document.getElementById(`node-${stage}`);
    if (target) {
        target.style.borderColor = "var(--accent-cyan)";
        target.style.boxShadow = "0 0 25px var(--accent-cyan)";
        setTimeout(() => {
            target.style.borderColor = "";
            target.style.boxShadow = "";
        }, 1500);
    }
}

function filterApplications(e) {
    const term = e.target.value.toLowerCase();
    const rows = document.querySelectorAll("#tbody-queue tr");
    rows.forEach(row => {
        const text = row.innerText.toLowerCase();
        row.style.display = text.includes(term) ? "" : "none";
    });
}
