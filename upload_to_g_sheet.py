import pandas as pd
import gspread
import yaml
from oauth2client.service_account import ServiceAccountCredentials

from gspread_formatting import (
    set_frozen,
    format_cell_range,
    CellFormat,
    Color,
    TextFormat,
    NumberFormat
)

def stylize_sheet(worksheet):
    print("🎨 Applying styles to Google Sheet...")

    # 1️⃣ Freeze the top header row
    set_frozen(worksheet, rows=1)

    # 2️⃣ Format header row: bold, colored background, white text
    header_format = CellFormat(
        textFormat=TextFormat(bold=True, foregroundColor=Color(1, 1, 1)),
        backgroundColor=Color(0.2, 0.4, 0.8),  # A nice blue
        horizontalAlignment='CENTER'
    )
    format_cell_range(worksheet, '1:1', header_format)

    # # 3️⃣ Center-align all data
    center_format = CellFormat(horizontalAlignment='CENTER')
    format_cell_range(worksheet, 'A2:Z1000', center_format)

    # 4️⃣ Format Amount column as currency
    # Find the index of the "Amount" column
    headers = worksheet.row_values(1)
    if "Amount" in headers:
        amount_col_letter = chr(ord('A') + headers.index("Amount"))
        currency_format = CellFormat(
            numberFormat=NumberFormat(type='NUMBER', pattern='$#,##0.00'),
            horizontalAlignment='RIGHT'
        )
        format_cell_range(worksheet, f"{amount_col_letter}2:{amount_col_letter}5000", currency_format)
        print(f"💵 Formatted 'Amount' column as currency: {amount_col_letter}")

    # print("✅ Styling complete.")


def load_google_config(config_path="./google_config.yml"):
    with open(config_path, "r") as f:
        return yaml.safe_load(f)["google"]

def get_worksheet(config):
    scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
    creds = ServiceAccountCredentials.from_json_keyfile_name(config["credentials_path"], scope)
    client = gspread.authorize(creds)

    spreadsheet = client.open(config["spreadsheet_name"])
    worksheet = spreadsheet.worksheet(config["worksheet_name"])
    return worksheet

def get_or_create_worksheet(spreadsheet, worksheet_name, rows=5000, cols=10):
    try:
        worksheet = spreadsheet.worksheet(worksheet_name)
        print(f"📄 Worksheet '{worksheet_name}' found.")
    except gspread.exceptions.WorksheetNotFound:
        print(f"🆕 Worksheet '{worksheet_name}' not found. Creating...")
        worksheet = spreadsheet.add_worksheet(title=worksheet_name, rows=str(rows), cols=str(cols))
        print(f"✅ Worksheet '{worksheet_name}' created.")
    return worksheet

def upload_new_rows_to_sheet(csv_path, config_path="google_config.yml"):
    config = load_google_config(config_path)
    print(config["spreadsheet_name"])
    print(config["worksheet_name"])
    print(config)

    # worksheet = spreadsheet.worksheet(config["google"]["worksheet_name"])

    # worksheet = get_worksheet(config)
    worksheet = get_or_create_worksheet(config["spreadsheet_name"],config["worksheet_name"])

    print("📥 Reading master CSV...")
    df_new = pd.read_csv(csv_path)

    print("📄 Fetching existing sheet data...")
    existing_records = worksheet.get_all_records()
    df_existing = pd.DataFrame(existing_records)

    print(f"🔎 Existing rows: {len(df_existing)} | New rows: {len(df_new)}")

    # Merge and remove duplicates
    combined = pd.concat([df_existing, df_new], ignore_index=True)
    combined = combined.drop_duplicates(subset=["Date", "Description", "Amount", "Card"])
    combined = combined.fillna("N/A")
    print(f"✅ Final row count (deduplicated): {len(combined)}")

    # Clear sheet and re-upload everything (simplest method)
    worksheet.clear()
    worksheet.update([combined.columns.values.tolist()] + combined.values.tolist())
    print("📤 Upload complete.")

# Example usage

upload_new_rows_to_sheet("final_output/all_cards.csv")
stylize_sheet(get_worksheet(load_google_config()))
