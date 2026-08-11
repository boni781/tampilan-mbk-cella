// =====================================================
// DASHBOARD.JS
// Mengatur grafik, pencarian tabel, ekspor CSV, unduh PNG,
// mode layar penuh, serta format angka dashboard.
// =====================================================

// =====================================================
// 1. STATUS GRAFIK
// Menyimpan instance Chart.js yang sedang aktif.
// =====================================================
let dashboardChart = null;

// =====================================================
// 2. INISIALISASI HALAMAN
// Dijalankan setelah HTML dashboard selesai dimuat.
// =====================================================
document.addEventListener("DOMContentLoaded", function () {
    createChart();
    buildNumericSummariesFromTable();
    initializeSearch();
    initializeExport();
    initializeDownload();
});

// =====================================================
// 3. RINGKASAN TOTAL DARI TABEL DETAIL DATA
// Membaca header dan nilai pada #dashboardTable, mengenali kolom
// numerik, lalu menjumlahkan setiap kolom sebagai kartu ringkasan.
// =====================================================
function buildNumericSummariesFromTable() {
    const table = document.getElementById("dashboardTable");
    const cards = document.getElementById("numericSummaryCards");
    const list = document.getElementById("numericSummaryList");
    const count = document.getElementById("numericColumnCount");

    if (!table || !cards || !list) return;

    const headers = [...table.querySelectorAll("thead th")].map(function (header) {
        return header.innerText.trim();
    });
    const rows = [...table.querySelectorAll("tbody tr")];
    const totals = [];

    headers.forEach(function (header, index) {
        const values = rows
            .map(function (row) {
                const cell = row.cells[index];
                return cell ? parseIndonesianNumber(cell.innerText) : null;
            })
            .filter(function (value) { return value !== null; });

        // Tetap jumlahkan nilai yang berformat angka. Nilai seperti "-",
        // kosong, atau teks penanda diabaikan agar satu sel tidak membuang
        // seluruh kolom numerik.
        if (values.length) {
            totals.push({ header: header, total: values.reduce((sum, value) => sum + value, 0), count: values.length });
        }
    });

    renderNumericSummary(cards, list, count, totals);
}

// Membaca angka Indonesia: 1.250,50 menjadi 1250.50.
function parseIndonesianNumber(value) {
    let text = String(value).trim();
    // Kode seperti "PSNX 052" adalah teks, bukan nilai numerik.
    if (/[a-z]/i.test(text)) return null;

    text = text.replace(/[^0-9,.-]/g, "");
    if (!text || ["-", ".", ","].includes(text)) return null;

    if (text.includes(",") && text.includes(".")) {
        text = text.lastIndexOf(",") > text.lastIndexOf(".")
            ? text.replace(/\./g, "").replace(",", ".")
            : text.replace(/,/g, "");
    } else if (text.includes(",")) {
        text = text.replace(",", ".");
    } else if ((text.match(/\./g) || []).length > 1 || (/\./.test(text) && text.split(".").pop().length === 3)) {
        text = text.replace(/\./g, "");
    }

    const number = Number(text);
    return Number.isFinite(number) ? number : null;
}

// Menggambar ulang kartu dan panel total dari hasil pembacaan tabel.
function renderNumericSummary(cards, list, count, totals) {
    const cardColors = ["blue", "green", "yellow", "purple", "orange", "red"];
    const alertColors = ["alert-blue", "alert-green", "alert-yellow"];

    cards.replaceChildren();
    list.replaceChildren();
    if (count) count.innerText = `${totals.length} kolom`;

    if (!totals.length) {
        cards.innerHTML = '<article class="card blue"><h3>Data Numerik</h3><h1>-</h1><p>Tidak ada kolom angka pada Detail Data.</p></article>';
        list.innerHTML = '<p class="empty">Tidak ada kolom numerik untuk dijumlahkan.</p>';
        return;
    }

    totals.forEach(function (item, index) {
        const card = document.createElement("article");
        card.className = `card ${cardColors[index % cardColors.length]}`;
        card.innerHTML = `<h3></h3><h1></h1><p>Total dari ${item.count} nilai angka</p>`;
        card.querySelector("h3").textContent = item.header;
        card.querySelector("h1").textContent = formatNumber(item.total);
        cards.appendChild(card);

        const alert = document.createElement("div");
        alert.className = `alert ${alertColors[index % alertColors.length]}`;
        const title = document.createElement("span");
        const total = document.createElement("small");
        title.textContent = item.header;
        total.textContent = formatNumber(item.total);
        alert.append(title, total);
        list.appendChild(alert);
    });
}

// =====================================================
// 4. MEMBUAT GRAFIK DINAMIS
// Data chartLabels, chartValues, dan chartType dikirim oleh Flask.
// =====================================================
function createChart() {
    destroyChart();

    const canvas = document.getElementById("mainChart");
    if (!canvas || chartLabels.length === 0) return;

    const color = getChartColor(chartType);
    const isCircularChart = ["pie", "doughnut"].includes(chartType);
    const isSmallScreen = window.matchMedia("(max-width: 700px)").matches;

    dashboardChart = new Chart(canvas, {
        type: chartType,
        data: {
            labels: chartLabels,
            datasets: [{
                label: chartType.toUpperCase(),
                data: chartValues,
                borderColor: color.border,
                backgroundColor: color.background,
                borderWidth: chartType === "line" ? 3 : 1.5,
                borderRadius: chartType === "bar" ? 6 : 0,
                borderSkipped: false,
                radius: isCircularChart ? "92%" : undefined,
                cutout: chartType === "doughnut" ? "58%" : undefined,
                fill: chartType === "line",
                tension: 0.3
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            animation: { duration: 750, easing: "easeOutQuart" },
            interaction: { intersect: false, mode: "index" },
            layout: { padding: isCircularChart ? { top: 8, right: 12, bottom: 8, left: 12 } : { top: 8, right: 10, bottom: 0, left: 4 } },
            plugins: {
                legend: { position: isCircularChart ? (isSmallScreen ? "bottom" : "right") : "top", display: true, labels: { boxWidth: 16, boxHeight: 10, padding: 14, useBorderRadius: true, borderRadius: 3, color: "#526b7d", font: { weight: "600" } } },
                tooltip: {
                    backgroundColor: "rgba(25, 58, 82, .94)",
                    padding: 12,
                    cornerRadius: 9,
                    displayColors: true,
                    callbacks: {
                        label: function (context) {
                            return formatNumber(context.parsed.y ?? context.parsed);
                        }
                    }
                }
            },
            // Grafik Pie dan Doughnut tidak memakai sumbu X/Y.
            scales: isCircularChart ? {} : {
                x: { grid: { display: false }, ticks: { autoSkip: true, maxTicksLimit: 12, color: "#6e8291", font: { size: 11 } } },
                y: {
                    beginAtZero: true,
                    grid: { color: "rgba(111, 142, 164, .16)", drawBorder: false },
                    ticks: { color: "#6e8291", callback: function (value) { return formatNumber(value); } }
                }
            }
        }
    });
}

// =====================================================
// 5. PENCARIAN TABEL
// Menyaring seluruh kolom tabel berdasarkan kata kunci.
// =====================================================
function initializeSearch() {
    const input = document.getElementById("searchInput");
    if (!input) return;

    input.addEventListener("keyup", function () {
        const keyword = this.value.toLowerCase();
        let visible = 0;

        document.querySelectorAll("#dashboardTable tbody tr").forEach(function (row) {
            const show = row.innerText.toLowerCase().includes(keyword);
            row.style.display = show ? "" : "none";
            if (show) visible++;
        });

        updateVisibleRows(visible);
    });
}

// =====================================================
// 6. JUMLAH BARIS TERLIHAT
// Memperbarui angka setelah tabel difilter melalui pencarian.
// =====================================================
function updateVisibleRows(total) {
    const element = document.getElementById("visibleRows");
    if (element) element.innerText = total;
}

// =====================================================
// 7. EKSPOR CSV
// Mengekspor header dan hanya baris tabel yang sedang terlihat.
// =====================================================
function initializeExport() {
    const button = document.getElementById("exportExcel");
    if (button) button.addEventListener("click", exportCSV);
}

function exportCSV() {
    const table = document.getElementById("dashboardTable");
    if (!table) return;

    const csv = [];
    table.querySelectorAll("tr").forEach(function (row) {
        if (row.style.display === "none") return;

        const line = [];
        row.querySelectorAll("th,td").forEach(function (column) {
            line.push(`"${column.innerText.replace(/"/g, '""')}"`);
        });
        csv.push(line.join(","));
    });

    const blob = new Blob([csv.join("\n")], { type: "text/csv;charset=utf-8" });
    const url = URL.createObjectURL(blob);
    const link = document.createElement("a");
    link.href = url;
    link.download = "Dashboard.csv";
    link.click();
    URL.revokeObjectURL(url);
}

// =====================================================
// 8. UNDUH GRAFIK PNG
// Mengubah canvas Chart.js menjadi file gambar PNG.
// =====================================================
function initializeDownload() {
    const button = document.getElementById("downloadChart");
    if (button) button.addEventListener("click", downloadChart);
}

function downloadChart() {
    if (!dashboardChart) return;

    const link = document.createElement("a");
    link.download = "Dashboard Chart.png";
    link.href = dashboardChart.toBase64Image();
    link.click();
}

// =====================================================
// 9. RESPONSIVE GRAFIK
// Menyesuaikan ukuran grafik saat ukuran jendela berubah.
// =====================================================
window.addEventListener("resize", function () {
    if (dashboardChart) dashboardChart.resize();
});

// =====================================================
// 10. REFRESH DAN HAPUS GRAFIK
// Dipakai jika grafik perlu dibuat ulang atau diperbarui.
// =====================================================
function refreshChart() {
    if (dashboardChart) dashboardChart.update();
}

function destroyChart() {
    if (dashboardChart) {
        dashboardChart.destroy();
        dashboardChart = null;
    }
}

// =====================================================
// 11. FORMAT ANGKA
// Menampilkan angka dengan pemisah ribuan Indonesia.
// =====================================================
function formatNumber(value) {
    return new Intl.NumberFormat("id-ID").format(value);
}

// =====================================================
// 12. WARNA OTOMATIS GRAFIK
// Memilih warna sesuai tipe grafik yang dipilih di Builder.
// =====================================================
function getChartColor(type) {
    if (type === "line") {
        return { border: "rgb(37,99,235)", background: "rgba(37,99,235,0.15)" };
    }

    if (type === "pie") {
        const colors = ["#2563eb", "#16a34a", "#ea580c", "#dc2626", "#9333ea", "#0891b2", "#ca8a04", "#6b7280"];
        return { border: colors, background: colors };
    }

    const colors = ["rgba(52,152,219,.72)", "rgba(46,204,113,.68)", "rgba(241,196,15,.70)", "rgba(142,68,173,.66)", "rgba(230,126,34,.68)", "rgba(231,76,60,.64)"];
    const borders = ["#2584c0", "#27ae60", "#c9a20b", "#754092", "#c76a17", "#c83e33"];
    return { border: borders, background: colors };
}

// =====================================================
// 13. LAYAR PENUH GRAFIK
// Dipanggil oleh tombol Fullscreen pada dashboard.html.
// =====================================================
function toggleFullscreen() {
    const element = document.querySelector(".chart-container");
    if (!element) return;

    if (!document.fullscreenElement) {
        element.requestFullscreen();
    } else {
        document.exitFullscreen();
    }
}
