import gspread
import yaml
import pandas as pd
import gspread
from gspread.exceptions import WorksheetNotFound
from gspread_formatting import *
from google.oauth2.service_account import Credentials
# import time


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
# DRY THIS UP AND COMBINE WITH THE ABOVE
def get_or_replace_worksheet(spreadsheet, title, rows=100, cols=10):
    try:
        # If worksheet exists, delete it
        existing_ws = spreadsheet.worksheet(title)
        spreadsheet.del_worksheet(existing_ws)
    except gspread.exceptions.WorksheetNotFound:
        pass  # No existing worksheet to delete

    # Add a fresh worksheet
    return spreadsheet.add_worksheet(title=title, rows=str(rows), cols=str(cols))


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
    worksheet.update_tab_color({"red": 1, "green": 0.5, "blue": 0.5})

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

    print("🧬 Applying Formatting")
    header = cellFormat(
    backgroundColor=color(1, 0.9, 0.9),
    textFormat=textFormat(bold=True, fontSize=12, foregroundColor=color(1, 0, 1)),
    horizontalAlignment='CENTER'
    )
    centered = cellFormat(
    horizontalAlignment='CENTER'
    )
    currency_format = CellFormat(
    numberFormat=NumberFormat(type='CURRENCY', pattern='[$$]#,##0.00')
    )

    format_cell_range(worksheet, 'A1:J1', header)
    format_cell_range(worksheet, 'C:F', centered)
    format_cell_range(worksheet, 'C:C', currency_format)
    # worksheet.update_tab_color(color(1, 0.9, 0.9))

    set_column_widths(worksheet, [ ('A', 75), ('B', 300), ('C', 90), ('D', 150), ('E', 150), ('F', 95), ('G', 150), ('H:', 50) ])

    
def spending_report(csv_path, config_path="google_config.yml"):
    
    # Google Sheets setup

    config = load_google_config(config_path)

    credentials = Credentials.from_service_account_file(
        config["google"]["credentials_path"],
        scopes=[
            "https://www.googleapis.com/auth/spreadsheets",
            "https://www.googleapis.com/auth/drive",
        ],
    )

    client = gspread.authorize(credentials)
    # scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
    # creds = ServiceAccountCredentials.from_json_keyfile_name("path/to/your/creds.json", scope)
    # client = gspread.authorize(creds)
    
    # Open spreadsheet and worksheet
    spreadsheet = client.open(config["google"]["spreadsheet_name"])
    source_tab = spreadsheet.worksheet(config["google"]["worksheet_name"])
    print(f"Source tab named: {source_tab}\n")
    print(f"Source tab title: {source_tab.title}\n")


    # ✅ Get or create the worksheet
    report_tab_name = config["google"]["worksheet_name"] + "-report2"
    print(f"Report tab named: {report_tab_name}")

    report_tab = get_or_create_worksheet(spreadsheet, report_tab_name)
    

    # --- Load data from source sheet
    print("lets take a 1 second brake for the api to catch up")
    # time.sleep(1)
    source_ws = spreadsheet.worksheet(source_tab.title)
    data = source_ws.get_all_records()
    
    df = pd.DataFrame(data)

    print("we got to Pandas")
    
    # --- Ensure Amount column is numeric
    df['Amount'] = pd.to_numeric(df['Amount'], errors='coerce')
    
    # --- Report Calculations
    
    # 1. Spending by Category
    spending_by_category = df.groupby('Category')['Amount'].sum().reset_index()
    spending_by_category = spending_by_category.sort_values(by='Amount', ascending=False)
    
    # 2. Total Spent (excluding payments)
    non_payment_df = df[~df['Category'].str.contains('payment', case=False, na=False)]
    total_spent = non_payment_df['Amount'].sum()
    
    # 3. 5 Largest Purchases
    largest_purchases = df.sort_values(by='Amount', ascending=False).head(5)
    
    # --- Format Report as list of lists
    report_data = []
    
    report_data.append(['Spending by Category'])
    report_data.append(['Category', 'Amount'])
    report_data += spending_by_category.values.tolist()
    report_data.append([])
    
    report_data.append(['Total Spent (excluding payments):', total_spent])
    report_data.append([])
    
    report_data.append(['5 Largest Purchases'])
    report_data.append(df.columns.tolist())
    report_data += largest_purchases.values.tolist()
    
    # --- Create or clear report worksheet
    try:
        report_ws = spreadsheet.worksheet(report_tab)
        spreadsheet.del_worksheet(report_ws)
    except gspread.exceptions.WorksheetNotFound:
        pass
    print(f"Here is the data I am passing to my crashing function:")
    print(f"Title : {report_tab}")
    print(f"Rows: {str(len(report_data) + 20)}")
    print(f"\n")
    # report_ws.clear()
    # report_ws = spreadsheet.update(title=report_tab.title, rows=str(len(report_data) + 20), cols="10")
    report_ws = get_or_replace_worksheet(spreadsheet, title=report_tab.title, rows=len(report_data) + 20, cols=10)

    
    # --- Upload the report
    report_ws.update('A1', report_data)
    

if __name__ == "__main__":
    upload_new_rows_to_sheet("final_output/all_cards.csv")
    # spending_report("final_output/all_cards.csv")
