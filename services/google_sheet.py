import os
import json
import re

import gspread

from google.oauth2.service_account import Credentials


# =====================================================
# GOOGLE API
# =====================================================

SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive"
]


# =====================================================
# LOAD CREDENTIALS
# =====================================================

def get_credentials():

    # =================================================
    # RAILWAY / DEPLOYMENT
    # =================================================

    credentials_json = os.getenv(
        "GOOGLE_CREDENTIALS_JSON"
    )

    if credentials_json:

        try:

            info = json.loads(
                credentials_json
            )

            return Credentials.from_service_account_info(
                info,
                scopes=SCOPES
            )

        except json.JSONDecodeError as e:

            raise RuntimeError(
                "GOOGLE_CREDENTIALS_JSON tidak valid."
            ) from e

    # =================================================
    # LOCAL
    # =================================================

    credentials_file = os.getenv(
        "GOOGLE_CREDENTIALS_FILE",
        "credentials.json"
    )

    if not os.path.exists(credentials_file):

        raise RuntimeError(
            "Google credentials tidak ditemukan. "
            "Pastikan credentials.json tersedia "
            "untuk penggunaan lokal atau "
            "GOOGLE_CREDENTIALS_JSON tersedia "
            "untuk deployment."
        )

    return Credentials.from_service_account_file(
        credentials_file,
        scopes=SCOPES
    )


# =====================================================
# CONNECT
# =====================================================

def connect(spreadsheet_url):

    creds = get_credentials()

    client = gspread.authorize(
        creds
    )

    spreadsheet = client.open_by_url(
        spreadsheet_url
    )

    return spreadsheet


# =====================================================
# WORKSHEET
# =====================================================

def get_sheet_names(spreadsheet_url):

    spreadsheet = connect(
        spreadsheet_url
    )

    worksheets = spreadsheet.worksheets()

    return [
        ws.title
        for ws in worksheets
    ]


def get_worksheet(
    spreadsheet_url,
    worksheet_name
):

    spreadsheet = connect(
        spreadsheet_url
    )

    return spreadsheet.worksheet(
        worksheet_name
    )


# =====================================================
# GET DATA
# =====================================================

def get_data(
    spreadsheet_url,
    worksheet_name,
    header_row=1
):

    sheet = get_worksheet(
        spreadsheet_url,
        worksheet_name
    )

    values = sheet.get_all_values()

    # ======================================
    # Sheet kosong
    # ======================================

    if not values:

        return [], []

    # ======================================
    # Validasi Header Row
    # ======================================

    if header_row < 1:

        header_row = 1

    if header_row > len(values):

        return [], []

    # ======================================
    # Header
    # ======================================

    headers = list(
        values[header_row - 1]
    )

    # ======================================
    # Ganti header kosong
    # ======================================

    for i in range(len(headers)):

        if headers[i].strip() == "":

            headers[i] = f"Kolom_{i + 1}"

    # ======================================
    # Data
    # ======================================

    result = []

    for row in values[header_row:]:

        # Samakan jumlah kolom
        normalized_row = (
            list(row)
            + [""] * max(
                0,
                len(headers) - len(row)
            )
        )

        # Jika row lebih panjang dari header,
        # potong agar jumlah kolom sama.
        normalized_row = normalized_row[
            :len(headers)
        ]

        item = {}

        for i, header in enumerate(headers):

            value = normalized_row[i]

            item[header] = value

        result.append(item)

    return headers, result


# =====================================================
# UNIQUE VALUES
# =====================================================

def get_unique_values(
    data,
    header
):

    values = []

    for row in data:

        value = str(
            row.get(
                header,
                ""
            )
        ).strip()

        if value == "":

            continue

        if value not in values:

            values.append(value)

    values.sort()

    return values