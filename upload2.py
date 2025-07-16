import gspread
import yaml
import pandas as pd
from gspread.exceptions import WorksheetNotFound
from google.oauth2.service_account import Credentials


def load_google_config(path="google_config.yml"):
    with open(path, "r") as f:
        return yaml.safe_load(f)


def get_or_create_worksheet(spreadsheet, worksheet_name, rows=5000, cols=10):
    try:
        worksheet = spreadsheet.worksheet(worksheet_name)
        print(f"📄 Worksheet '{worksheet_name}' found.")
    except WorksheetNotFound:
        print(f"🆕 Worksheet '{worksheet_name}' not found. Creating...")
        worksheet = spreadsheet.add_worksheet(title=worksheet_name, rows=str(rows), cols=str(cols))
        print(f"✅ Worksheet '{worksheet_name}' created.")
    return worksheet


def upload_new_rows_to_sheet(csv_path, config_path="google_config.yml"):
    config = load_google_config(config_path)

    credentials = Credentials.from_service_account_file(
        config["google"]["credentials_path"],
        scopes=[
            "https://www.googleapis.com/auth/spreadsheets",
            "https://www.googleapis.com/auth/drive",
        ],
    )

    client = gspread.authorize(credentials)

    # ✅ OPEN the spreadsheet properly
    spreadsheet = client.open(config["google"]["spreadsheet_name"])

    # ✅ Get or create the worksheet
    worksheet = get_or_create_worksheet(
        spreadsheet, config["google"]["worksheet_name"]
    )

    # Load local CSV
    print("📥 Reading master CSV...")
    df = pd.read_csv(csv_path)

    # Get existing records
    print("📄 Fetching existing sheet data...")
    try:
        existing = pd.DataFrame(worksheet.get_all_records())
    except Exception:
        existing = pd.DataFrame()

    print(f"🔎 Existing rows: {len(existing)} | New rows: {len(df)}")

    # Drop duplicates based on full row content
    combined = pd.concat([existing, df], ignore_index=True)
    combined = combined.drop_duplicates()

    print(f"✅ Final row count (deduplicated): {len(combined)}")

    # Upload new content
    worksheet.clear()
    # ✅ Replace NaNs with empty strings (critical for Sheets API)
    combined = combined.fillna("")

    worksheet.update([combined.columns.values.tolist()] + combined.values.tolist())
    print("✅ Upload complete.")


if __name__ == "__main__":
    upload_new_rows_to_sheet("final_output/all_cards.csv")
