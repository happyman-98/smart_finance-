(function() {
    const s = document.createElement("style");
    s.textContent = `@keyframes spin { from { transform: rotate(0deg); } to { transform: rotate(360deg); } }`;
    document.head.appendChild(s);
})();

const storedUser = localStorage.getItem("user");
if (!storedUser) window.location.href = "login.html";

let currentUser = JSON.parse(storedUser) || { name: "User" };
document.getElementById("header-username").textContent = currentUser.name;

const API   = "http://localhost:8000";
const token = localStorage.getItem("token");

async function apiFetch(path, options = {}) {
    const res = await fetch(`${API}${path}`, {
        ...options,
        headers: {
            "Content-Type": "application/json",
            "Authorization": `Bearer ${token}`,
            ...options.headers,
        },
    });
    if (res.status === 401) {
        localStorage.clear();
        window.location.href = "login.html";
    }
    return res.json();
}

let liveSummary = {
    net_balance:          0,
    total_income:         0,
    total_expense:        0,
    by_category:          {},
    monthly:              {},
    monthly_income:       currentUser.monthly_income       ?? 0,
    monthly_savings_goal: currentUser.monthly_savings_goal ?? 0,
};

let allTransactions = [];
let allGoals        = [];

let monthlyChartInstance  = null;
let categoryChartInstance = null;

function updateSystemClock() {
    document.getElementById("clock-display").innerText =
        new Date().toLocaleTimeString("en-US", { hour12: true });
}
setInterval(updateSystemClock, 1000);
updateSystemClock();

const toastEl = document.getElementById("global-toast-widget");

function triggerToastFeedback(message) {
    toastEl.innerText = message;
    toastEl.classList.add("visible");
    setTimeout(() => toastEl.classList.remove("visible"), 3000);
}

const navButtons   = document.querySelectorAll(".nav-item");
const contentViews = document.querySelectorAll(".view-frame");
const headerTitle  = document.getElementById("dynamic-title");

navButtons.forEach(btn => {
    btn.addEventListener("click", () => {
        const targetId = btn.getAttribute("data-target");
        if (!targetId) return;
        navButtons.forEach(b => b.classList.remove("active"));
        contentViews.forEach(v => v.classList.remove("active-view"));
        btn.classList.add("active");
        document.getElementById(targetId).classList.add("active-view");
        headerTitle.innerText = btn.textContent.trim();
        triggerToastFeedback(`Navigated to ${btn.textContent.trim()}`);
    });
});

document.getElementById("logout-trigger").addEventListener("click", () => {
    localStorage.removeItem("token");
    localStorage.removeItem("user");
    window.location.href = "login.html";
});

const MONTH_LABELS = ["Jan","Feb","Mar","Apr","May","Jun","Jul","Aug","Sep","Oct","Nov","Dec"];

const primaryCtx = document.getElementById("overviewFlowChart").getContext("2d");
monthlyChartInstance = new Chart(primaryCtx, {
    type: "bar",
    data: {
        labels: MONTH_LABELS,
        datasets: [
            { label: "Income ($)",  data: new Array(12).fill(0), backgroundColor: "#635BFF", borderRadius: 6 },
            { label: "Expense ($)", data: new Array(12).fill(0), backgroundColor: "#00FFC2", borderRadius: 6 },
        ],
    },
    options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: { legend: { labels: { color: "#8F9CAE" } } },
        scales: {
            x: { grid: { display: false }, ticks: { color: "#8F9CAE" } },
            y: { grid: { color: "#1E2330"  }, ticks: { color: "#8F9CAE" } },
        },
    },
});

const categoryCtx = document.getElementById("categoryDistributionChart").getContext("2d");
categoryChartInstance = new Chart(categoryCtx, {
    type: "doughnut",
    data: {
        labels: [],
        datasets: [{ data: [], backgroundColor: ["#FF4A6B","#635BFF","#00FFC2","#FFB800","#00B896","#FF8C42","#A78BFA"], borderWidth: 0 }],
    },
    options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: { legend: { position: "right", labels: { color: "#8F9CAE" } } },
    },
});

function updateMonthlyChart(monthly) {
    const incomeData  = MONTH_LABELS.map(m => monthly[m]?.income  ?? 0);
    const expenseData = MONTH_LABELS.map(m => monthly[m]?.expense ?? 0);
    monthlyChartInstance.data.datasets[0].data = incomeData;
    monthlyChartInstance.data.datasets[1].data = expenseData;
    monthlyChartInstance.update();
}

function updateCategoryChart(by_category) {
    categoryChartInstance.data.labels           = Object.keys(by_category);
    categoryChartInstance.data.datasets[0].data = Object.values(by_category);
    categoryChartInstance.update();
}

function fmtDate(dateStr) {
    return new Date(dateStr).toLocaleDateString("en-US", { month: "long", day: "numeric", year: "numeric" });
}

function renderTransactions(txList) {
    const ledger = document.getElementById("master-transaction-ledger");
    if (!txList.length) {
        ledger.innerHTML = `<p style="color:#8F9CAE;text-align:center;padding:20px;">No transactions found.</p>`;
        return;
    }
    ledger.innerHTML = txList.map(t => `
        <div class="feed-row" id="tx-${t.id}">
            <div class="row-meta">
                <div class="row-icon ${t.type === "income" ? "bg-mint-dim" : "bg-rose-dim"}">
                    <i class="fa-solid ${t.type === "income" ? "fa-arrow-trend-up" : "fa-arrow-trend-down"}"></i>
                </div>
                <div>
                    <div class="row-title">${t.merchant}</div>
                    <div class="row-sub">${fmtDate(t.date)} • ${t.category}</div>
                </div>
            </div>
            <div style="display:flex;align-items:center;gap:12px;">
                <div class="row-amt ${t.type === "income" ? "trend-up" : "trend-down"}">
                    ${t.type === "income" ? "+" : "-"}$${t.amount.toFixed(2)}
                </div>
                <button class="delete-tx-btn" data-id="${t.id}" title="Delete transaction">
                    <i class="fa-solid fa-trash-can"></i>
                </button>
            </div>
        </div>
    `).join("");

    document.querySelectorAll(".delete-tx-btn").forEach(btn => {
        btn.addEventListener("click", () => deleteTransaction(btn.dataset.id));
    });
}

function renderGoals(goalList) {
    allGoals = goalList;
    const container = document.getElementById("goals-container");
    let html = goalList.length === 0
        ? `<p style="color:#8F9CAE;text-align:center;padding:20px;">No goals yet — add one below.</p>`
        : goalList.map(g => {
            const pct = Math.min(100, Math.round((g.current_amount / g.target_amount) * 100));
            return `
            <div class="interactive-form-box" style="margin-bottom:16px;" id="goal-${g.id}">
                <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:10px;">
                    <h4>${g.title}</h4>
                    <span style="font-size:0.8rem;color:#8F9CAE;">Due: ${new Date(g.deadline).toLocaleDateString()}</span>
                </div>
                <div style="background:#0B0C10;padding:4px;border-radius:20px;border:1px solid #1E2330;">
                    <div style="background:linear-gradient(90deg,#635BFF,#00FFC2);height:16px;border-radius:20px;width:${pct}%;transition:width 0.5s;"></div>
                </div>
                <div style="display:flex;justify-content:space-between;font-size:0.8rem;margin-top:8px;color:#8F9CAE;">
                    <span>Saved: $${g.current_amount.toLocaleString("en-US", { minimumFractionDigits: 2 })}</span>
                    <span style="color:#00FFC2;">Target: $${g.target_amount.toLocaleString("en-US", { minimumFractionDigits: 2 })} (${pct}%)</span>
                </div>
                <div style="margin-top:14px;display:flex;gap:10px;align-items:center;">
                    <input type="number" class="input-element" style="margin:0;flex:1;" placeholder="Contribute amount ($)" id="contrib-${g.id}" min="0" step="0.01">
                    <button class="action-submit-btn" style="white-space:nowrap;" onclick="contributeToGoal(${g.id})">
                        Add Funds
                    </button>
                </div>
            </div>`;
        }).join("");

    html += `
        <div class="card-panel" style="margin-top:24px;">
            <h4 style="color:#00FFC2;margin-bottom:16px;">
                <i class="fa-solid fa-bullseye" style="margin-right:8px;"></i>Create New Goal
            </h4>
            <div style="display:grid;gap:14px;">
                <div>
                    <label style="font-size:0.78rem;font-weight:600;color:#8F9CAE;display:block;margin-bottom:6px;">Goal Title</label>
                    <input type="text" id="new-goal-title" class="input-element" style="margin:0;" placeholder="e.g. Emergency Fund, Vacation, MacBook…">
                </div>
                <div style="display:grid;grid-template-columns:1fr 1fr;gap:12px;">
                    <div>
                        <label style="font-size:0.78rem;font-weight:600;color:#8F9CAE;display:block;margin-bottom:6px;">Target Amount ($)</label>
                        <input type="number" id="new-goal-amount" class="input-element" style="margin:0;" placeholder="e.g. 5000" min="0" step="0.01">
                    </div>
                    <div>
                        <label style="font-size:0.78rem;font-weight:600;color:#8F9CAE;display:block;margin-bottom:6px;">Deadline</label>
                        <input type="date" id="new-goal-deadline" class="input-element" style="margin:0;">
                    </div>
                </div>
                <button class="action-submit-btn" id="create-goal-btn" onclick="createGoal()">Create Goal</button>
            </div>
        </div>`;

    container.innerHTML = html;
}

async function loadDashboard() {
    try {
        const [summary, txList, goalList] = await Promise.all([
            apiFetch("/api/analytics/summary"),
            apiFetch("/api/transactions/"),
            apiFetch("/api/goals/"),
        ]);

        liveSummary = { ...liveSummary, ...summary };
        allTransactions = txList;

        const fmt = (n) => `$${Number(n).toLocaleString("en-US", { minimumFractionDigits: 2 })}`;
        document.getElementById("live-net-balance").innerText    = fmt(summary.net_balance);
        document.getElementById("metric-income").innerText       = fmt(summary.monthly_income       ?? currentUser.monthly_income       ?? 0);
        document.getElementById("metric-savings-goal").innerText = fmt(summary.savings_goal         ?? currentUser.monthly_savings_goal  ?? 0);

        renderTransactions(txList);
        renderGoals(goalList);

        if (summary.by_category && Object.keys(summary.by_category).length > 0) updateCategoryChart(summary.by_category);
        if (summary.monthly     && Object.keys(summary.monthly).length     > 0) updateMonthlyChart(summary.monthly);

    } catch (err) {
        console.error("Dashboard load error:", err);
        triggerToastFeedback("⚠️ Failed to load dashboard data.");
    }
}

loadDashboard();

async function deleteTransaction(id) {
    if (!confirm("Delete this transaction? This cannot be undone.")) return;
    try {
        await fetch(`${API}/api/transactions/${id}`, {
            method: "DELETE",
            headers: { "Authorization": `Bearer ${token}` },
        });
        triggerToastFeedback("Transaction deleted.");
        await loadDashboard();
    } catch (err) {
        triggerToastFeedback("⚠️ Could not delete transaction.");
    }
}

function applyFilters() {
    const typeVal = document.getElementById("filter-type").value;
    const catVal  = document.getElementById("filter-category").value.toLowerCase();
    const fromVal = document.getElementById("filter-from").value;
    const toVal   = document.getElementById("filter-to").value;

    let filtered = [...allTransactions];

    if (typeVal)  filtered = filtered.filter(t => t.type === typeVal);
    if (catVal)   filtered = filtered.filter(t => t.category.toLowerCase().includes(catVal));
    if (fromVal)  filtered = filtered.filter(t => new Date(t.date) >= new Date(fromVal));
    if (toVal)    filtered = filtered.filter(t => new Date(t.date) <= new Date(toVal + "T23:59:59"));

    renderTransactions(filtered);
}

document.addEventListener("DOMContentLoaded", () => {
    ["filter-type","filter-category","filter-from","filter-to"].forEach(id => {
        document.getElementById(id)?.addEventListener("change", applyFilters);
        document.getElementById(id)?.addEventListener("input",  applyFilters);
    });
    document.getElementById("filter-reset")?.addEventListener("click", () => {
        ["filter-type","filter-category","filter-from","filter-to"].forEach(id => {
            const el = document.getElementById(id);
            if (el) el.value = "";
        });
        renderTransactions(allTransactions);
    });
});

const drawerEl      = document.getElementById("add-tx-drawer");
const drawerOverlay = document.getElementById("drawer-overlay");

function openDrawer() {
    drawerEl.classList.add("open");
    drawerOverlay.classList.add("open");
    document.getElementById("tx-tab-manual").click();
}
function closeDrawer() {
    drawerEl.classList.remove("open");
    drawerOverlay.classList.remove("open");
}

document.getElementById("add-tx-btn")?.addEventListener("click", openDrawer);
drawerOverlay?.addEventListener("click", closeDrawer);
document.getElementById("drawer-close")?.addEventListener("click", closeDrawer);

document.querySelectorAll(".drawer-tab").forEach(tab => {
    tab.addEventListener("click", () => {
        document.querySelectorAll(".drawer-tab").forEach(t => t.classList.remove("active"));
        document.querySelectorAll(".drawer-pane").forEach(p => p.classList.remove("active"));
        tab.classList.add("active");
        document.getElementById(tab.dataset.pane).classList.add("active");
    });
});

document.querySelectorAll(".cat-chip").forEach(chip => {
    chip.addEventListener("click", () => {
        document.querySelectorAll(".cat-chip").forEach(c => c.classList.remove("sel"));
        chip.classList.add("sel");
    });
});

document.querySelectorAll(".type-btn").forEach(btn => {
    btn.addEventListener("click", () => {
        document.querySelectorAll(".type-btn").forEach(b => {
            b.classList.remove("sel-expense","sel-income");
        });
        btn.classList.add(btn.dataset.type === "expense" ? "sel-expense" : "sel-income");
    });
});

document.getElementById("manual-tx-submit")?.addEventListener("click", async () => {
    const typeBtn  = document.querySelector(".type-btn.sel-expense, .type-btn.sel-income");
    const type     = typeBtn?.dataset.type ?? "expense";
    const amount   = parseFloat(document.getElementById("tx-amount").value);
    const merchant = document.getElementById("tx-merchant").value.trim();
    const dateVal  = document.getElementById("tx-date").value;
    const category = document.querySelector(".cat-chip.sel")?.textContent.replace(/^[^\s]+\s/,"").trim() ?? "Other";

    if (!amount || amount <= 0 || !merchant || !dateVal) {
        triggerToastFeedback("⚠️ Please fill in amount, merchant, and date.");
        return;
    }

    try {
        await apiFetch("/api/transactions/", {
            method: "POST",
            body: JSON.stringify({ type, amount, merchant, category, date: new Date(dateVal).toISOString() }),
        });
        triggerToastFeedback(`✅ ${type === "income" ? "Income" : "Expense"} of $${amount.toFixed(2)} saved.`);
        closeDrawer();
        document.getElementById("tx-amount").value   = "";
        document.getElementById("tx-merchant").value = "";
        await loadDashboard();
    } catch (err) {
        triggerToastFeedback("⚠️ Failed to save transaction.");
    }
});

const ocrFileInput = document.getElementById("ocr-file-input");
const dropZoneEl   = document.getElementById("ocr-drop-zone");

dropZoneEl?.addEventListener("click", () => ocrFileInput?.click());

let dragCounter = 0;

dropZoneEl?.addEventListener("dragenter", e => {
    e.preventDefault();
    e.stopPropagation();
    dragCounter++;
    dropZoneEl.classList.add("drag");
});

dropZoneEl?.addEventListener("dragover", e => {
    e.preventDefault();
    e.stopPropagation();
    e.dataTransfer.dropEffect = "copy";
});

dropZoneEl?.addEventListener("dragleave", e => {
    e.preventDefault();
    e.stopPropagation();
    dragCounter--;
    if (dragCounter === 0) dropZoneEl.classList.remove("drag");
});

dropZoneEl?.addEventListener("drop", e => {
    e.preventDefault();
    e.stopPropagation();
    dragCounter = 0;
    dropZoneEl.classList.remove("drag");
    const file = e.dataTransfer.files[0];
    if (file) handleOCRFile(file);
});

ocrFileInput?.addEventListener("change", () => {
    if (ocrFileInput.files[0]) handleOCRFile(ocrFileInput.files[0]);
});

function resetDropZone() {
    const dropZone = document.getElementById("ocr-drop-zone");
    if (!dropZone) return;
    dropZone.innerHTML = `
        <i class="fa-solid fa-file-image" style="font-size:2rem;color:#635BFF;display:block;margin-bottom:10px;"></i>
        <div style="font-size:0.95rem;font-weight:600;color:#F3F4F6;margin-bottom:4px;">Drop receipt image here</div>
        <div style="font-size:0.8rem;color:#8F9CAE;">or click to browse — JPG, PNG, PDF</div>
        <input type="file" id="ocr-file-input" accept="image/*,.pdf" style="display:none;">`;
    document.getElementById("ocr-file-input")?.addEventListener("change", () => {
        const f = document.getElementById("ocr-file-input").files[0];
        if (f) handleOCRFile(f);
    });
}

function showOCRAlert(type, message) {
    const colors = {
        error:   { bg: "rgba(255,74,107,0.12)", border: "#FF4A6B", icon: "fa-circle-xmark",         text: "#FF4A6B" },
        warning: { bg: "rgba(255,184,0,0.10)",  border: "#FFB800", icon: "fa-triangle-exclamation",  text: "#FFB800" },
        success: { bg: "rgba(0,255,194,0.08)",  border: "#00FFC2", icon: "fa-circle-check",          text: "#00FFC2" },
    };
    const c = colors[type] || colors.warning;

    const html = `
        <div style="
            padding:12px 14px;
            border-radius:10px;
            border:1px solid ${c.border};
            background:${c.bg};
            display:flex;
            align-items:flex-start;
            gap:10px;
            font-size:0.82rem;
            line-height:1.5;
            color:#F3F4F6;
        ">
            <i class="fa-solid ${c.icon}" style="color:${c.text};margin-top:2px;flex-shrink:0;"></i>
            <span>${message}</span>
        </div>`;

    // Primary slot: inside the result box, always visible when result is shown
    const slot = document.getElementById("ocr-alert-slot");
    if (slot) {
        slot.innerHTML = html;
        slot.style.display = "block";
        return;
    }

    // Fallback: above the confirm button inside the pane
    const confirmEl = document.getElementById("ocr-confirm-section");
    if (confirmEl) {
        let fallback = document.getElementById("ocr-alert-banner");
        if (!fallback) {
            fallback = document.createElement("div");
            fallback.id = "ocr-alert-banner";
            fallback.style.marginTop = "12px";
            confirmEl.insertAdjacentElement("beforebegin", fallback);
        }
        fallback.innerHTML = html;
        fallback.style.display = "block";
    }
}

async function handleOCRFile(file) {
    const prog      = document.getElementById("ocr-progress");
    const fill      = document.getElementById("ocr-progress-fill");
    const resultEl  = document.getElementById("ocr-result-box");
    const confirmEl = document.getElementById("ocr-confirm-section");
    const dropZone  = document.getElementById("ocr-drop-zone");

    prog.style.display      = "block";
    fill.style.width        = "0%";
    resultEl.style.display  = "none";
    confirmEl.style.display = "none";
    document.getElementById("ocr-breakdown")?.remove();
    document.getElementById("ocr-alert-banner")?.remove();
    const alertSlot = document.getElementById("ocr-alert-slot");
    if (alertSlot) { alertSlot.innerHTML = ""; alertSlot.style.display = "none"; }

    dropZone.innerHTML = `
        <div style="text-align:center;padding:10px 0;">
            <div style="font-size:1.5rem;margin-bottom:8px;animation:spin 1s linear infinite;display:inline-block;">⏳</div>
            <div style="font-size:0.9rem;font-weight:600;color:#A78BFA;margin-bottom:4px;" id="ocr-status-text">Uploading receipt…</div>
            <div style="font-size:0.75rem;color:#8F9CAE;" id="ocr-file-name">${file.name} · ${(file.size/1024).toFixed(1)} KB</div>
        </div>`;

    const steps = [
        [800,  "Sending to Gemini…"],
        [3000, "Reading receipt…"],
        [6000, "Extracting fields…"],
        [10000,"Almost done…"],
    ];
    const timers = steps.map(([delay, msg]) =>
        setTimeout(() => {
            const el = document.getElementById("ocr-status-text");
            if (el) el.textContent = msg;
        }, delay)
    );

    let pct = 0;
    const iv = setInterval(() => {
        pct = Math.min(pct + 1, 85);
        fill.style.width = pct + "%";
    }, 300);

    try {
        const engine   = document.querySelector(".eng-btn.sel")?.dataset.engine ?? "gemini";
        const formData = new FormData();
        formData.append("file", file);
        formData.append("engine", engine);

        console.log(`[OCR] Uploading "${file.name}" (${(file.size/1024).toFixed(1)} KB) — engine: ${engine}`);

        const res = await fetch(`${API}/api/upload-receipt`, {
            method: "POST",
            headers: { "Authorization": `Bearer ${token}` },
            body: formData,
        });

        timers.forEach(clearTimeout);
        clearInterval(iv);
        fill.style.width = "100%";

        if (!res.ok) {
            const errData = await res.json().catch(() => ({}));
            throw new Error(errData.detail ?? `Server error ${res.status}`);
        }

        const data = await res.json();

        resetDropZone();
        setTimeout(() => { prog.style.display = "none"; }, 300);

        console.group(`[OCR] Result — status: ${data.status}`);
        console.log("Engine:", data.engine);
        console.log("Confidence:", ((data.confidence ?? 0) * 100).toFixed(1) + "%");
        console.log("Extracted:", data.extracted);
        if (data.line_items?.length) console.table(data.line_items);
        if (data.taxes?.length)      console.table(data.taxes);
        if (data.tax_total != null)  console.log("Tax total:", data.tax_total);
        console.groupEnd();

        const confidence = data.confidence ?? 0;
        const confPct    = Math.round(confidence * 100);
        const extracted  = data.extracted ?? {};
        const lineItems  = data.line_items ?? [];
        const taxes      = data.taxes ?? [];
        const taxTotal   = data.tax_total ?? 0;

        const merchant = extracted.merchant ?? "";
        const amount   = extracted.total    ?? "";
        const currency = extracted.currency ?? "";
        const rawDate  = extracted.date     ?? "";

        let dateVal = "";
        if (rawDate) {
            try { dateVal = new Date(rawDate).toISOString().split("T")[0]; }
            catch { dateVal = String(rawDate).split("T")[0]; }
        }

        document.getElementById("ocr-merchant").value = merchant;
        document.getElementById("ocr-amount").value   = amount;
        document.getElementById("ocr-date").value     = dateVal;

        const confEl = document.getElementById("ocr-conf");
        confEl.textContent = `${confPct}% confidence`;
        confEl.style.color = confidence >= 0.85 ? "#00FFC2" : confidence >= 0.5 ? "#FFB800" : "#FF4A6B";
        document.getElementById("ocr-engine-used").textContent = `Engine: ${data.engine ?? engine}`;

        let breakdownHtml = `<div id="ocr-breakdown" style="margin-top:14px;font-size:0.78rem;color:#8F9CAE;">`;

        if (currency) {
            breakdownHtml += `
                <div style="display:flex;justify-content:space-between;padding:4px 0;border-bottom:1px solid #1E2330;">
                    <span>Currency</span><span style="color:#F3F4F6;">${currency}</span>
                </div>`;
        }

        if (lineItems.length) {
            breakdownHtml += `<div style="margin:10px 0 4px;font-weight:600;color:#8F9CAE;">Line Items</div>
            <table style="width:100%;border-collapse:collapse;">
                <thead><tr style="color:#635BFF;text-align:left;">
                    <th style="padding:3px 6px;">Item</th>
                    <th style="padding:3px 6px;text-align:right;">Qty</th>
                    <th style="padding:3px 6px;text-align:right;">Rate</th>
                    <th style="padding:3px 6px;text-align:right;">Amount</th>
                </tr></thead>
                <tbody>${lineItems.map(item => `
                <tr style="border-top:1px solid #1E2330;">
                    <td style="padding:3px 6px;">${item.name ?? "—"}</td>
                    <td style="padding:3px 6px;text-align:right;">${item.qty ?? "—"}</td>
                    <td style="padding:3px 6px;text-align:right;">${item.rate != null ? Number(item.rate).toFixed(2) : "—"}</td>
                    <td style="padding:3px 6px;text-align:right;">${item.taxable_value != null ? Number(item.taxable_value).toFixed(2) : "—"}</td>
                </tr>`).join("")}</tbody>
            </table>`;
        }

        if (taxes.length) {
            breakdownHtml += `<div style="margin:10px 0 4px;font-weight:600;color:#8F9CAE;">Tax Breakdown</div>
            ${taxes.map(t => `
                <div style="display:flex;justify-content:space-between;padding:3px 0;border-bottom:1px solid #1E2330;">
                    <span>${t.kind ?? "Tax"}${t.rate_pct != null ? ` (${t.rate_pct}%)` : ""}</span>
                    <span style="color:#FFB800;">${t.amount != null ? Number(t.amount).toFixed(2) : "—"}</span>
                </div>`).join("")}
            <div style="display:flex;justify-content:space-between;padding:5px 0;font-weight:700;">
                <span>Tax Total</span><span style="color:#FFB800;">${Number(taxTotal).toFixed(2)}</span>
            </div>`;
        }

        breakdownHtml += `</div>`;

        const fieldsGrid = resultEl.querySelector("div[style*='display:grid']");
        if (fieldsGrid) {
            fieldsGrid.insertAdjacentHTML("afterend", breakdownHtml);
        } else {
            resultEl.insertAdjacentHTML("beforeend", breakdownHtml);
        }

        resultEl.style.display  = "block";
        confirmEl.style.display = "block";

        const missingFields = [];
        if (!merchant) missingFields.push("merchant");
        if (!amount)   missingFields.push("amount");
        if (!dateVal)  missingFields.push("date");

        if (confidence === 0 || (!merchant && !amount)) {
            showOCRAlert("error",
                `<strong>Scan failed.</strong> No data could be extracted from this image. ` +
                `Try a clearer photo, better lighting, or switch to a different engine. ` +
                `You can still fill in the fields manually and save.`
            );
        } else if (confidence < 0.5) {
            showOCRAlert("error",
                `<strong>Very low confidence (${confPct}%).</strong> The receipt was hard to read — ` +
                `${missingFields.length ? `fields missing: <strong>${missingFields.join(", ")}</strong>. ` : ""}` +
                `Please review every field carefully before saving.`
            );
        } else if (confidence < 0.85) {
            showOCRAlert("warning",
                `<strong>Low confidence (${confPct}%).</strong> Some fields may be wrong. ` +
                `${missingFields.length ? `Missing: <strong>${missingFields.join(", ")}</strong>. ` : ""}` +
                `Check the values below before confirming.`
            );
        } else {
            showOCRAlert("success",
                `Receipt scanned successfully (${confPct}% confidence). Review the fields below and confirm to save.`
            );
        }

        setTimeout(() => {
            confirmEl.scrollIntoView({ behavior: "smooth", block: "nearest" });
        }, 100);

    } catch (err) {
        timers.forEach(clearTimeout);
        clearInterval(iv);
        prog.style.display = "none";

        resetDropZone();

        const resultEl  = document.getElementById("ocr-result-box");
        const confirmEl = document.getElementById("ocr-confirm-section");

        resultEl.style.display  = "block";
        confirmEl.style.display = "block";

        document.getElementById("ocr-merchant").value = "";
        document.getElementById("ocr-amount").value   = "";
        document.getElementById("ocr-date").value     = "";
        document.getElementById("ocr-conf").textContent  = "";
        document.getElementById("ocr-engine-used").textContent = "";

        showOCRAlert("error",
            `<strong>Scan failed.</strong> ${err.message ?? "The server could not process this image."} ` +
            `You can fill in the fields manually below and still save the expense.`
        );

        console.error("[OCR] Error:", err);
    }
}

document.getElementById("ocr-confirm-btn")?.addEventListener("click", async () => {
    const amount   = parseFloat(document.getElementById("ocr-amount").value);
    const merchant = document.getElementById("ocr-merchant").value.trim();
    const dateVal  = document.getElementById("ocr-date").value;

    if (!merchant) {
        showOCRAlert("error", "Merchant name is required. Please enter it above.");
        return;
    }
    if (!amount || amount <= 0) {
        showOCRAlert("error", "A valid amount is required. Please enter it above.");
        return;
    }
    if (!dateVal) {
        showOCRAlert("error", "Date is required. Please select a date above.");
        return;
    }

    const btn = document.getElementById("ocr-confirm-btn");
    btn.disabled = true;
    btn.textContent = "Saving…";

    try {
        const params = new URLSearchParams({ merchant, amount, date: dateVal });
        const res = await fetch(`${API}/api/upload-receipt/confirm?${params}`, {
            method: "POST",
            headers: { "Authorization": `Bearer ${token}` },
        });
        if (!res.ok) throw new Error(`Server error ${res.status}`);

        const saved = await res.json();
        console.log("[OCR] Manually confirmed and saved:", saved);

        btn.textContent = "Updating dashboard…";

        await loadDashboard();

        triggerToastFeedback(`✅ Receipt saved — $${amount.toFixed(2)} from ${merchant}.`);
        closeDrawer();

    } catch (err) {
        console.error("[OCR] Confirm error:", err);
        showOCRAlert("error", `Failed to save: ${err.message ?? "Please try again."}`);
    }

    btn.disabled = false;
    btn.textContent = "Confirm & Save";
});

document.querySelectorAll(".eng-btn").forEach(btn => {
    btn.addEventListener("click", () => {
        document.querySelectorAll(".eng-btn").forEach(b => b.classList.remove("sel"));
        btn.classList.add("sel");
    });
});

document.getElementById("simulate-deposit-btn")?.addEventListener("click", async () => {
    const amount = parseFloat(document.getElementById("deposit-input-amount").value);
    if (isNaN(amount) || amount <= 0) { alert("Please enter a positive amount."); return; }
    const btn = document.getElementById("simulate-deposit-btn");
    btn.disabled = true;
    try {
        await apiFetch("/api/transactions/", {
            method: "POST",
            body: JSON.stringify({ type: "income", amount, merchant: "Manual Deposit", category: "Deposit", date: new Date().toISOString().split("T")[0] }),
        });
        triggerToastFeedback(`Deposit of +$${amount.toFixed(2)} processed.`);
        document.getElementById("deposit-input-amount").value = "";
        await loadDashboard();
    } catch (err) { triggerToastFeedback("⚠️ Deposit failed. Try again."); }
    btn.disabled = false;
});

async function createGoal() {
    const title    = document.getElementById("new-goal-title")?.value.trim();
    const amount   = parseFloat(document.getElementById("new-goal-amount")?.value);
    const deadline = document.getElementById("new-goal-deadline")?.value;

    if (!title || !amount || amount <= 0 || !deadline) {
        triggerToastFeedback("⚠️ Please fill in all goal fields.");
        return;
    }
    const btn = document.getElementById("create-goal-btn");
    btn.disabled = true; btn.textContent = "Creating…";
    try {
        await apiFetch("/api/goals/", {
            method: "POST",
            body: JSON.stringify({ title, target_amount: amount, deadline: new Date(deadline).toISOString() }),
        });
        triggerToastFeedback(`✅ Goal "${title}" created.`);
        await loadDashboard();
    } catch (err) { triggerToastFeedback("⚠️ Failed to create goal."); }
    btn.disabled = false; btn.textContent = "Create Goal";
}

async function contributeToGoal(goalId) {
    const input  = document.getElementById(`contrib-${goalId}`);
    const amount = parseFloat(input?.value);
    if (!amount || amount <= 0) { triggerToastFeedback("⚠️ Enter a valid contribution amount."); return; }
    try {
        await apiFetch(`/api/goals/${goalId}/contribute`, {
            method: "POST",
            body: JSON.stringify({ amount }),
        });
        triggerToastFeedback(`✅ $${amount.toFixed(2)} added to goal.`);
        await loadDashboard();
    } catch (err) { triggerToastFeedback("⚠️ Contribution failed."); }
}

const chatBtn      = document.getElementById("chatbot-button");
const chatWindow   = document.getElementById("chatbot-window");
const closeBtn     = document.getElementById("close-chatbot");
const chatInput    = document.getElementById("chat-user-input");
const chatSendBtn  = document.getElementById("chat-send-btn");
const msgContainer = document.getElementById("chat-messages-container");

chatBtn.addEventListener("click",  () => chatWindow.classList.toggle("open"));
closeBtn.addEventListener("click", () => chatWindow.classList.remove("open"));

document.getElementById("chat-reset-btn")?.addEventListener("click", async () => {
    try {
        await apiFetch("/api/chat/reset", { method: "POST" });
        msgContainer.innerHTML = `<div class="msg-bubble bot-msg">
            Hi! I'm your SmartAssist. Conversation cleared.<br>
            • <strong>"What is my balance?"</strong><br>
            • <strong>"Give me a budget tip"</strong>
        </div>`;
        triggerToastFeedback("Chat history cleared.");
    } catch (err) { triggerToastFeedback("⚠️ Could not reset chat."); }
});

function appendMessage(text, role) {
    const bubble = document.createElement("div");
    bubble.className = `msg-bubble ${role === "user" ? "user-msg" : "bot-msg"}`;
    bubble.innerHTML = text.replace(/\n/g, "<br>");
    msgContainer.appendChild(bubble);
    msgContainer.scrollTop = msgContainer.scrollHeight;
    return bubble;
}

function showTyping() {
    const el = document.createElement("div");
    el.className = "typing-indicator";
    el.id = "typing-indicator";
    el.innerHTML = `<div class="typing-dot"></div><div class="typing-dot"></div><div class="typing-dot"></div>`;
    msgContainer.appendChild(el);
    msgContainer.scrollTop = msgContainer.scrollHeight;
}

function hideTyping() {
    document.getElementById("typing-indicator")?.remove();
}

async function sendMessage() {
    const userText = chatInput.value.trim();
    if (!userText) return;
    chatInput.value = "";
    chatSendBtn.disabled = true;
    appendMessage(userText, "user");
    showTyping();
    try {
        const res = await fetch(`${API}/api/chat/stream`, {
            method: "POST",
            headers: { "Content-Type": "application/json", "Authorization": `Bearer ${token}` },
            body: JSON.stringify({ message: userText }),
        });
        if (res.status === 401) { localStorage.clear(); window.location.href = "login.html"; return; }
        hideTyping();
        const bubble = appendMessage("", "bot");
        let full = "";
        const reader  = res.body.getReader();
        const decoder = new TextDecoder();
        let buffer    = "";
        while (true) {
            const { done, value } = await reader.read();
            if (done) break;
            buffer += decoder.decode(value, { stream: true });
            const lines = buffer.split("\n");
            buffer = lines.pop();
            for (const line of lines) {
                if (!line.startsWith("data: ")) continue;
                const chunk = line.slice(6);
                if (chunk === "[DONE]") break;
                full += chunk;
                bubble.innerHTML = full.replace(/\n/g, "<br>");
                msgContainer.scrollTop = msgContainer.scrollHeight;
            }
        }
        if (!full) appendMessage("Sorry, I couldn't get a response. Please try again.", "bot");
    } catch (err) {
        hideTyping();
        appendMessage("⚠️ Connection error. Check your network and try again.", "bot");
    }
    chatSendBtn.disabled = false;
    chatInput.focus();
}

chatSendBtn.addEventListener("click", sendMessage);
chatInput.addEventListener("keydown", e => { if (e.key === "Enter" && !e.shiftKey) sendMessage(); });

function prefillSettings() {
    const fields = {
        "settings-name":           currentUser.name,
        "settings-email":          currentUser.email,
        "settings-phone":          currentUser.phone,
        "settings-dob":            currentUser.dob,
        "settings-monthly-income": currentUser.monthly_income,
        "settings-savings-goal":   currentUser.monthly_savings_goal,
    };
    Object.entries(fields).forEach(([id, val]) => {
        const el = document.getElementById(id);
        if (el && val !== undefined && val !== null) el.value = val;
    });
}
prefillSettings();

document.getElementById("settings-save-btn")?.addEventListener("click", async () => {
    const incomeVal = parseFloat(document.getElementById("settings-monthly-income").value);
    const goalVal   = parseFloat(document.getElementById("settings-savings-goal").value);
    const name      = document.getElementById("settings-name").value.trim();
    const phone     = document.getElementById("settings-phone").value.trim();
    const dob       = document.getElementById("settings-dob").value;

    if (isNaN(incomeVal) || isNaN(goalVal) || incomeVal < 0 || goalVal < 0) {
        triggerToastFeedback("⚠️ Please enter valid positive numbers.");
        return;
    }
    const btn = document.getElementById("settings-save-btn");
    btn.disabled = true; btn.textContent = "Saving…";
    try {
        const updatedUser = await apiFetch("/api/auth/me", {
            method: "PUT",
            body: JSON.stringify({ name, phone, dob: dob || null, monthly_income: incomeVal, monthly_savings_goal: goalVal }),
        });
        const merged = { ...currentUser, ...updatedUser };
        localStorage.setItem("user", JSON.stringify(merged));
        currentUser = merged;
        document.getElementById("header-username").textContent = merged.name;
        liveSummary.monthly_income       = updatedUser.monthly_income;
        liveSummary.monthly_savings_goal = updatedUser.monthly_savings_goal;
        const fmt2 = n => `$${Number(n).toLocaleString("en-US", { minimumFractionDigits: 2 })}`;
        document.getElementById("metric-income").innerText       = fmt2(updatedUser.monthly_income);
        document.getElementById("metric-savings-goal").innerText = fmt2(updatedUser.monthly_savings_goal);
        triggerToastFeedback("✅ Profile saved successfully.");
    } catch (err) { triggerToastFeedback("⚠️ Failed to save settings."); }
    btn.disabled = false; btn.textContent = "Save Changes";
});