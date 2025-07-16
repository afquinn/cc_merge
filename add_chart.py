import json
import yaml
import gspread
from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build

def load_config(path="google_config.yml"):
    with open(path, "r") as f:
        return yaml.safe_load(f)

def add_monthly_spending_chart():
    config = load_config()

    credentials = Credentials.from_service_account_file(
        config["google"]["credentials_path"],
        scopes=[
            "https://www.googleapis.com/auth/spreadsheets",
            "https://www.googleapis.com/auth/drive"
        ]
    )
    
    client = gspread.authorize(credentials)
    spreadsheet = client.open(config["google"]["spreadsheet_name"])
    worksheet = spreadsheet.worksheet(config["google"]["worksheet_name"])
    sheet_id = worksheet._properties["sheetId"]
    spreadsheet_id = spreadsheet.id

    # Dynamically calculate num_months
    values = worksheet.get_all_values()
    num_months = len(values) - 1  # Exclude header row

    chart_request = {
        "requests": [
            {
                "addChart": {
                    "chart": {
                        "spec": {
                            "title": "Monthly Spending",
                            "basicChart": {
                                "chartType": "COLUMN",
                                "legendPosition": "BOTTOM_LEGEND",
                                "axis": [
                                    {"position": "BOTTOM_AXIS", "title": "Month"},
                                    {"position": "LEFT_AXIS", "title": "Total Spent ($)"}
                                ],
                                "domains": [
                                    {
                                        "domain": {
                                            "sourceRange": {
                                                "sources": [
                                                    {
                                                        "sheetId": sheet_id,
                                                        "startRowIndex": 1,
                                                        "endRowIndex": num_months + 1,
                                                        "startColumnIndex": 0,
                                                        "endColumnIndex": 1
                                                    }
                                                ]
                                            }
                                        }
                                    }
                                ],
                                "series": [
                                    {
                                        "series": {
                                            "sourceRange": {
                                                "sources": [
                                                    {
                                                        "sheetId": sheet_id,
                                                        "startRowIndex": 1,
                                                        "endRowIndex": num_months + 1,
                                                        "startColumnIndex": 1,
                                                        "endColumnIndex": 2
                                                    }
                                                ]
                                            }
                                        },
                                        "targetAxis": "LEFT_AXIS"
                                    }
                                ]
                            }
                        },
                        "position": {
                            "overlayPosition": {
                                "anchorCell": {
                                    "sheetId": sheet_id,
                                    "rowIndex": 0,
                                    "columnIndex": 8
                                }
                            }
                        }
                    }
                }
            }
        ]
    }

    response = service.spreadsheets().batchUpdate(
        spreadsheetId=spreadsheet_id,
        body=chart_request
    ).execute()

    print("✅ Chart added to sheet!")

if __name__ == "__main__":
    add_monthly_spending_chart()
