# 💳 Credit Card Activity Merger & Categorizer

This Python project merges multiple credit card CSV exports into a unified dataset, applies category mappings (by card issuer and transaction description), filters by date, and uploads the result to a specified Google Sheet.

---

## 🧰 Features

- 📁 Merges multiple credit card CSVs (across years, cards, folders)
- 🗂️ Applies standardized categories (via `category_map.yml`)
- 🔍 Supports both category-based and description-based mapping
- 📅 Filters data by year/month/day via `config.yml`
- 🧼 De-duplicates and sorts transactions chronologically
- 📤 Uploads clean data to a specified tab in a Google Sheet
- ✅ Skips rows already uploaded (prevents duplicates)
- 🪵 Rich emoji-based CLI logging

---

## 📂 Project Structure

```bash
.
├── merge_cards.py             # Main script to merge and categorize transactions
├── upload_to_g_sheet.py      # Script to upload merged data to Google Sheets
├── config.yml                # User config (year, sheet name, etc.)
├── category_map.yml          # Category rules: by category + by description
├── final_output/
│   └── all_cards.csv         # Output of merged and categorized data
├── card_data/
│   ├── Amex/
│   │   └── 2024/...
│   └── Chase/
│       └── 2025/...
└── credentials.yml           # Google API credentials (excluded via .gitignore)
```




⚙️ Setup
Clone this repo:

```
git clone https://github.com/your-username/cc-merge.git
cd cc-merge
```


Create a virtual environment:

```
python3 -m venv cc_merge
source bin/activate
```
Install dependencies:

```
pip install -r requirements.txt
```
Set up your configuration:

config.yml for year/month/day filters and Google Sheet details

category_map.yml to control how categories are simplified

credentials.yml for Google Sheets access (OAuth2)


📝 License
MIT License

