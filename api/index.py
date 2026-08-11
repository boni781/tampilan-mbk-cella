from flask import (
    Flask,
    render_template,
    request,
    jsonify
)

import re
import json

from services.google_sheet import (
    get_data,
    get_sheet_names,
    get_unique_values
)

app = Flask(
    __name__,
    template_folder="../templates",
    static_folder="../static"
)

# =====================================================
# DEFAULT CONFIG
# =====================================================

def default_config():

    return {

        "spreadsheet_url": "",

        "dashboard_title": "Dashboard Data",

        "worksheet_name": "",

        "header_row": 1,

        "sheet_names": [],

        "headers": [],

        "data": [],

        "selected_columns": [],

        "chart": {

            "x": "",

            "y": "",

            "type": "bar"

        },

        "exclude_rules": [],

        "excluded_columns": []

    }


# =====================================================
# LOAD CONFIG DARI FORM
# =====================================================

def load_builder_config(form):

    config = default_config()

    config["spreadsheet_url"] = form.get(
        "spreadsheet_url",
        ""
    )

    config["dashboard_title"] = form.get(
        "dashboard_title",
        "Dashboard Data"
    ).strip() or "Dashboard Data"

    config["worksheet_name"] = form.get(
        "worksheet_name",
        ""
    )

    config["header_row"] = int(
        form.get(
            "header_row",
            1
        )
    )

    config["chart"]["x"] = form.get(
        "chart_x",
        ""
    )

    config["chart"]["y"] = form.get(
        "chart_y",
        ""
    )

    config["chart"]["type"] = form.get(
        "chart_type",
        "bar"
    )

    return config


# =====================================================
# BUILDER
# =====================================================

@app.route("/", methods=["GET", "POST"])
def builder():

    config = default_config()

    if request.method == "POST":

        config = load_builder_config(

            request.form

        )

        # =======================================
        # Ambil daftar worksheet
        # =======================================

        if config["spreadsheet_url"]:

            try:
                config["sheet_names"] = get_sheet_names(

                    config["spreadsheet_url"]

                )
            
            except Exception as e:

                print("========================================")
                print("ERROR GOOGLE SHEETS")
                print(e)
                print("========================================")

                config["sheet_names"] = []

                config["connection_error"] = (
                    "Data tidak dapat diambil dari Google Sheets. "
                    "Periksa koneksi internet atau sinyal Anda, "
                    "kemudian coba lagi."
                )

        # =======================================
        # Ambil data spreadsheet
        # =======================================

        if config["worksheet_name"]:

            headers, data = get_data(
    
                config["spreadsheet_url"],

                config["worksheet_name"],

                config["header_row"]

            )

            config["headers"] = headers

            config["data"] = data

    return render_template(

        "builder.html",

        config=config

    )
    

    # =====================================================
# AJAX
# =====================================================

@app.route("/get-filter-values", methods=["POST"])
def get_filter_values():

    spreadsheet_url = request.form.get(
        "spreadsheet_url",
        ""
    )

    worksheet_name = request.form.get(
        "worksheet_name",
        ""
    )

    header_row = int(
        request.form.get(
            "header_row",
            1
        )
    )

    header = request.form.get(
        "exclude_header",
        ""
    )

    if (
        spreadsheet_url == ""
        or worksheet_name == ""
        or header == ""
    ):

        return jsonify([])

    headers, data = get_data(

        spreadsheet_url,

        worksheet_name,

        header_row

    )

    values = get_unique_values(

        data,

        header

    )

    return jsonify(values)


# =====================================================
# FILTER DATA
# =====================================================

def apply_exclude_rules(
    data,
    rules
):

    if not rules:

        return data

    excluded_rows = {
        int(row_number)
        for rule in rules
        if rule.get("mode") == "rows"
        for row_number in rule.get("rows", [])
        if str(row_number).isdigit()
    }

    filtered = []

    for row_number, row in enumerate(data, start=1):

        if row_number in excluded_rows:
            continue

        remove = False

        for rule in rules:

            if rule.get("mode", "values") != "values":
                continue

            header = rule.get("header", "")

            values = rule.get("values", [])

            if row.get(header) in values:

                remove = True

                break

        if not remove:

            filtered.append(row)

    return filtered


def apply_column_exclusions(headers, data, rules):
    """Hapus kolom terpilih dari tabel, grafik, dan ringkasan dashboard."""

    excluded_columns = {
        rule.get("header")
        for rule in rules
        if rule.get("mode") == "column" and rule.get("header")
    }

    visible_headers = [header for header in headers if header not in excluded_columns]
    visible_data = [
        {header: row.get(header, "") for header in visible_headers}
        for row in data
    ]

    return visible_headers, visible_data, sorted(excluded_columns)


# =====================================================
# RINGKASAN KOLOM NUMERIK
# =====================================================

def parse_number(value):
    """Membaca angka berformat Indonesia, misalnya 1.250,50."""

    if value is None:
        return None

    text = str(value).strip()

    if text == "":
        return None

    # Kode seperti "PSNX 052" bukan nilai numerik.
    if re.search(r"[A-Za-z]", text):
        return None

    text = re.sub(r"[^0-9,.-]", "", text)

    if text in ("", "-", ".", ","):
        return None

    if "," in text and "." in text:
        if text.rfind(",") > text.rfind("."):
            text = text.replace(".", "").replace(",", ".")
        else:
            text = text.replace(",", "")
    elif "," in text:
        text = text.replace(",", ".")
    elif text.count(".") > 1 or (
        text.count(".") == 1
        and len(text.rsplit(".", 1)[1]) == 3
    ):
        text = text.replace(".", "")

    try:
        return float(text)
    except ValueError:
        return None


def format_number_id(value):
    """Memformat hasil total dengan pemisah ribuan Indonesia."""

    if value == int(value):
        return f"{int(value):,}".replace(",", ".")

    return f"{value:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")


def build_numeric_summaries(headers, data):
    """Menghitung total setiap kolom yang seluruh nilai terisinya numerik."""

    summaries = []

    for header in headers:
        values = [
            parse_number(row.get(header))
            for row in data
            if str(row.get(header, "")).strip() != ""
        ]

        numeric_values = [value for value in values if value is not None]

        # Nilai kosong atau penanda nonangka tidak membatalkan total kolom.
        if numeric_values:
            total = sum(numeric_values)
            summaries.append({
                "header": header,
                "total": format_number_id(total),
                "count": len(numeric_values)
            })

    return summaries


# =====================================================
# CHART DATA
# =====================================================

def build_chart_data(
    data,
    chart_x,
    chart_y
):

    labels = []

    values = []

    for row in data:

        labels.append(

            row.get(
                chart_x,
                ""
            )

        )

        value = parse_number(row.get(chart_y))

        values.append(value if value is not None else 0)

    return labels, values

# =====================================================
# DASHBOARD
# =====================================================

@app.route("/dashboard", methods=["POST"])
def dashboard():

    # ==========================================
    # Load Config
    # ==========================================

    config = load_builder_config(
        request.form
    )

    # ==========================================
    # Ambil Data Spreadsheet
    # ==========================================

    headers, data = get_data(

        config["spreadsheet_url"],

        config["worksheet_name"],

        config["header_row"]

    )

    config["headers"] = headers

    config["data"] = data
    

    # ==========================================
    # Ambil Semua Rule Exclude
    # ==========================================

    rules = []

    rule_headers = request.form.getlist(
        "rule_header[]"
    )

    rule_values = request.form.getlist(
        "rule_values[]"
    )

    # Rule baru dikirim sebagai JSON dari Builder. Format lama tetap didukung.
    raw_rules = request.form.get("rules", "")

    if raw_rules:
        try:
            parsed_rules = json.loads(raw_rules)
            if isinstance(parsed_rules, list):
                for rule in parsed_rules:
                    mode = rule.get("mode", "values")
                    if mode == "rows" and rule.get("rows"):
                        rules.append({"mode": "rows", "rows": rule["rows"]})
                    elif mode == "column" and rule.get("header"):
                        rules.append({"mode": "column", "header": rule["header"]})
                    elif mode == "values" and rule.get("header") and rule.get("values"):
                        rules.append({"mode": "values", "header": rule["header"], "values": rule["values"]})
        except (TypeError, ValueError, json.JSONDecodeError):
            rules = []

    if not rules:
        for header, values in zip(rule_headers, rule_values):
            if header == "":
                continue

            rules.append({
                "mode": "values",
                "header": header,
                "values": [v for v in values.split("||") if v != ""]
            })

    config["exclude_rules"] = rules

    # ==========================================
    # Terapkan Rule
    # ==========================================

    filtered_data = apply_exclude_rules(

        config["data"],

        config["exclude_rules"]

    )

    config["data"] = filtered_data

    visible_headers, visible_data, excluded_columns = apply_column_exclusions(
        config["headers"],
        config["data"],
        config["exclude_rules"]
    )

    config["dashboard_title"] = request.form.get(

        "dashboard_title",

        "Dashboard Data"

    ).strip() or "Dashboard Data"

    config["headers"] = visible_headers
    config["data"] = visible_data
    config["excluded_columns"] = excluded_columns

    # Ringkasan menggunakan data setelah rule pengecualian diterapkan.
    numeric_summaries = build_numeric_summaries(
        config["headers"],
        config["data"]
    )

    # ==========================================
    # Chart
    # ==========================================

    chart_labels = []

    chart_values = []

    if (

        config["chart"]["x"] != ""

        and

        config["chart"]["y"] != ""

        and config["chart"]["x"] in config["headers"]

        and config["chart"]["y"] in config["headers"]

    ):

        chart_labels, chart_values = build_chart_data(

            config["data"],

            config["chart"]["x"],

            config["chart"]["y"]

        )

    # ==========================================
    # Dashboard
    # ==========================================

    return render_template(

        "dashboard.html",

        config=config,

        chart_labels=chart_labels,

        chart_values=chart_values,

        numeric_summaries=numeric_summaries

    )


# =====================================================
# MAIN
# =====================================================

if __name__ == "__main__":

    app.run(
        debug=True
    )
