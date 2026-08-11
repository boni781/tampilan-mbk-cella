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


creds = Credentials.from_service_account_file(

    "credentials.json",

    scopes=SCOPES

)


client = gspread.authorize(
    creds
)

# =====================================================
# CONNECT
# =====================================================

def connect(
    spreadsheet_url
):

    spreadsheet = client.open_by_url(

        spreadsheet_url

    )

    return spreadsheet

# =====================================================
# WORKSHEET
# =====================================================

def get_sheet_names(
    spreadsheet_url
):

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

    headers = values[
        header_row - 1
    ]

    # Ganti header kosong

    for i in range(len(headers)):

        if headers[i].strip() == "":

            headers[i] = f"Kolom_{i+1}"

    # ======================================
    # Data
    # ======================================

    result = []

    for row in values[header_row:]:

        # jumlah kolom disamakan

        normalized_row = row + [""] * max(0, len(headers) - len(row))

        item = {}

        for i, header in enumerate(headers):

            # Nilai kosong dipertahankan apa adanya dari spreadsheet.
            # Tidak lagi menyalin nilai dari baris sebelumnya.
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

        value = row.get(

            header,

            ""

        ).strip()

        if value == "":

            continue

        if value not in values:

            values.append(value)

    values.sort()

    return values
