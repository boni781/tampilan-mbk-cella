// =====================================================
// DASHBOARD BUILDER: rule nilai, baris, dan kolom.
// =====================================================

let headers = [];
let rows = [];

document.addEventListener("DOMContentLoaded", function () {
    headers = readJson("headers-data", []);
    rows = readJson("rows-data", []);

    initializeChartSelects();
    document.getElementById("addRule").addEventListener("click", addRule);
    document.getElementById("builderForm").addEventListener("submit", serializeRules);
});

// Menjadikan pemilih sumbu dan jenis grafik lebih rapi serta konsisten.
function initializeChartSelects() {
    document.querySelectorAll(".chart-select").forEach(function (select) {
        new TomSelect(select, {
            create: false,
            allowEmptyOption: true,
            maxItems: 1,
            closeAfterSelect: true,
            placeholder: select.name === "chart_type" ? "Pilih jenis grafik" : "Pilih header"
        });
    });
}

function readJson(id, fallback) {
    const element = document.getElementById(id);
    if (!element) return fallback;
    try { return JSON.parse(element.textContent); } catch { return fallback; }
}

// Membuat satu rule baru; tidak ada rule otomatis agar dashboard tetap dapat dijalankan tanpa pengecualian.
function addRule() {
    if (!headers.length) {
        alert("Load spreadsheet terlebih dahulu agar header dan data tersedia.");
        return;
    }

    const fragment = document.getElementById("ruleTemplate").content.cloneNode(true);
    const rule = fragment.querySelector(".exclude-rule");
    document.getElementById("ruleContainer").appendChild(fragment);

    setupHeaderSelect(rule.querySelector(".rule-header-select"));
    setupHeaderSelect(rule.querySelector(".rule-column-select"));
    const valueTom = createTom(rule.querySelector(".rule-value-select"), "Pilih nilai...");
    const rowTom = createTom(rule.querySelector(".rule-row-select"), "Pilih baris...");

    rows.forEach(function (row, index) {
        const preview = headers.slice(0, 2).map(header => `${header}: ${row[header] || "-"}`).join(" | ");
        rowTom.addOption({ value: String(index + 1), text: `Baris ${index + 1} — ${preview}` });
    });

    const headerSelect = rule.querySelector(".rule-header-select");
    rule.querySelector(".load-values").addEventListener("click", function () {
        loadValues(headerSelect.value, valueTom);
    });
    headerSelect.addEventListener("change", function () { loadValues(this.value, valueTom); });
    rule.querySelector(".rule-mode").addEventListener("change", function () { setRuleMode(rule); });
    rule.querySelector(".remove-rule").addEventListener("click", function () {
        valueTom.destroy();
        rowTom.destroy();
        rule.remove();
    });
}

function setupHeaderSelect(select) {
    select.innerHTML = '<option value="">-- Pilih Header --</option>';
    headers.forEach(function (header) {
        const option = document.createElement("option");
        option.value = header;
        option.textContent = header;
        select.appendChild(option);
    });
}

function createTom(select, placeholder) {
    return new TomSelect(select, { plugins: ["remove_button"], create: false, persist: false, maxItems: null, closeAfterSelect: false, placeholder: placeholder });
}

function setRuleMode(rule) {
    const mode = rule.querySelector(".rule-mode").value;
    rule.querySelector(".mode-values").hidden = mode !== "values";
    rule.querySelector(".mode-rows").hidden = mode !== "rows";
    rule.querySelector(".mode-column").hidden = mode !== "column";
}

// Mengambil nilai unik pada sebuah kolom melalui Flask agar sesuai data spreadsheet terbaru.
async function loadValues(header, tom) {
    tom.clear();
    tom.clearOptions();
    if (!header) return;

    const formData = new FormData();
    ["spreadsheet_url", "worksheet_name", "header_row"].forEach(function (name) {
        formData.append(name, document.querySelector(`[name="${name}"]`).value);
    });
    formData.append("exclude_header", header);

    try {
        const response = await fetch("/get-filter-values", { method: "POST", body: formData });
        if (!response.ok) throw new Error("Gagal memuat nilai.");
        (await response.json()).forEach(value => tom.addOption({ value: value, text: value }));
        tom.refreshOptions(false);
    } catch (error) {
        alert("Nilai tidak dapat dimuat. Pastikan spreadsheet, worksheet, dan koneksi Google Sheets tersedia.");
        console.error(error);
    }
}

// Mengirim semua rule dalam satu format JSON yang dibaca oleh route /dashboard.
function serializeRules() {
    const rules = [];
    document.querySelectorAll(".exclude-rule").forEach(function (rule) {
        const mode = rule.querySelector(".rule-mode").value;

        if (mode === "values") {
            const header = rule.querySelector(".rule-header-select").value;
            const values = rule.querySelector(".rule-value-select").tomselect.getValue();
            if (header && values.length) rules.push({ mode: "values", header: header, values: values });
        }

        if (mode === "rows") {
            const selectedRows = rule.querySelector(".rule-row-select").tomselect.getValue();
            if (selectedRows.length) rules.push({ mode: "rows", rows: selectedRows });
        }

        if (mode === "column") {
            const header = rule.querySelector(".rule-column-select").value;
            if (header) rules.push({ mode: "column", header: header });
        }
    });
    document.getElementById("rules").value = JSON.stringify(rules);
}
