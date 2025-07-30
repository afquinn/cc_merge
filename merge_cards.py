import pandas as pd
import yaml
import os
from glob import glob
import re
from datetime import datetime
import time
import unicodedata
import numpy
import openpyxl


def ingest_all_files(folder_path):
    """Find all CSV and XLSX files in a folder."""
    csv_files = glob(os.path.join(folder_path, "*.csv"))
    xlsx_files = glob(os.path.join(folder_path, "*.xlsx"))
    return csv_files + xlsx_files

def read_card_file(filepath, column_map):
    """Read a single CSV or XLSX file into a DataFrame and rename columns."""
    if filepath.endswith(".csv"):
        df = pd.read_csv(filepath)
    elif filepath.endswith(".xlsx"):
        df = pd.read_excel(filepath)
    else:
        raise ValueError(f"Unsupported file format: {filepath}")
    
    if column_map:
        df.rename(columns=column_map, inplace=True)
    
    return df

def load_yaml(path):
    with open(path, 'r') as f:
        return yaml.safe_load(f)

# def normalize_text(text):
#     if not isinstance(text, str):
#         return ""
#     text = unicodedata.normalize("NFKD", text)
#     text = text.encode("ascii", "ignore").decode("ascii")  # remove accents
#     return text.strip().lower()
# def normalize_text(s):
#     if not isinstance(s, str):
#         return ""
#     return s.strip().lower().replace("’", "'").replace("é", "e")


def load_category_map(path="category_map.yml"):
    with open(path, "r") as f:
        return yaml.safe_load(f) 

# def read_card_file(filepath):
#     ext = os.path.splitext(filepath)[1].lower()
#     if ext == ".csv":
#         df = pd.read_csv(filepath)
#     elif ext in [".xls", ".xlsx"]:
#         df = pd.read_excel(filepath)
#     else:
#         raise ValueError(f"Unsupported file type: {filepath}")
#     return df

def apply_category_mapping(df, category_map):
    print("\n🧭 Starting category mapping...")
    print("\n \n 🧪 TESTING 🧪 here are that columns i start with:")
    print(df.columns.tolist())
    print(df[0:10])


    # Check required columns
    if "Category" not in df.columns:
        print("⚠️  Missing 'Category' column — assigning 'N/A'")
        df["Category"] = "N/A"

    if "Description" not in df.columns:
        print("❌ Missing 'Description' column — cannot apply mapping")
        return df

    # Normalize input data
    df["Category"] = df["Category"].fillna("N/A").astype(str).str.strip()
    df["Description"] = df["Description"].fillna("").astype(str)

    print(f"🔍 Sample 'Category' values: {df['Category'].unique()[:5]}")
    print(f"🔍 Sample 'Description' values: {df['Description'].head(3).tolist()}")

    # Normalize the by_category map for lowercase matching
    by_category_map = {
        k.strip().lower(): v for k, v in category_map.get("by_category", {}).items()
    }

    df["Mapped Category"] = df["Category"].str.strip().str.lower().map(by_category_map)
    mapped_by_category = df["Mapped Category"].notna().sum()
    print(f"✅ Mapped {mapped_by_category} rows using 'by_category'")

    # Log a few unmapped rows for inspection
    print("🧪 Sample rows with no category match:")
    print(df[df["Mapped Category"].isna()][["Description", "Category"]].head(5))

    # Description-based mapping fallback
    desc_rules = category_map.get("by_description", [])
    desc_match_count = 0

    for rule in desc_rules:
        keyword = rule["match"].upper()
        category = rule["category"]
        print("🧿 Catagory Rule Check 🧿 ")
        print(category)
        print(keyword)

        mask = (
            df["Mapped Category"].isin(["Uncategorized", "N/A"])
            & df["Description"].str.upper().str.contains(keyword, na=False)
        )


        matched = mask.sum()
        if matched > 0:
            print(f"🔎 Word Matched 🔎 '{keyword}' → AUTOFILLS CATAGORY: '{category}' in {matched} rows")
            df.loc[mask, "Mapped Category"] = category
            desc_match_count += matched

        # DEGBUG CATAGORIES    
        # print("📋 Sample leftover descriptions for new rules:")
        # print(df[df["Category"] == "Uncategorized"]["Description"])
        df[df["Category"] == "Uncategorized"].to_csv("debug_uncategorized_rows.csv", index=False)
    

    print(f"✅ Total rows mapped using description: {desc_match_count}")


    print("\n \n 🧪🧶 TESTING 🧪🧶 here are that columns i mid way with with:")
    print(df.columns.tolist())
    print(df[0:10])




    # Fill anything left over
    unmapped = df["Mapped Category"].isna().sum()
    if unmapped > 0:
        print(f"⚠️ {unmapped} still unmapped — assigning 'Uncategorized'")
        df["Mapped Category"] = df["Mapped Category"].fillna("Uncategorized")

    # Final assignment
    df["Category"] = df["Mapped Category"]
    df.drop(columns=["Mapped Category"], inplace=True)

    print("✅ Category mapping complete.\n")
    print("\n \n 🧪🧽 🧶 TESTING 🧪🧽 🧶 here are that columns i END with with:")
    print(df.columns.tolist())
    print(df[0:10])



    return df


# def ingest_all_files(folder_path):
#     all_files = glob(os.path.join(folder_path, "*"))

#     dataframes = []
#     for file in all_files:
#         try:
#             df = read_card_file(file)
#             df['Source File'] = os.path.basename(file)
#             dataframes.append(df)
#         except Exception as e:
#             print(f"⚠️ Skipping {file}: {e}")

#     return pd.concat(dataframes, ignore_index=True)

# def merge_csvs_for_card(card_config, tracked_year):
#     card_info = card_config['card']
    
#     if tracked_year == 0:
#         folder = os.path.join(card_info['folder_path'], "test_data")
#     else:
#         folder = card_info['folder_path']
    
#     card_name = card_info['name'].replace(" ", "_")
#     column_map = card_info.get('column_map', {})
#     output_path = f"./merged_output/{card_name}.csv"

#     print(f"Merging files for {card_info['name']}...")
#     print(f"Folder Path: {folder}")

#     all_files = ingest_all_files(folder)
#     if not all_files:
#         print(f"No files found in {folder}.")
#         return

#     dfs = []
#     for filepath in all_files:
#         try:
#             df = read_card_file(filepath, column_map)
#             dfs.append(df)
#         except Exception as e:
#             print(f"⚠️ Failed to read {filepath}: {e}")

#     if not dfs:
#         print("❌ No data frames were loaded successfully.")
#         return

#     merged_df = pd.concat(dfs, ignore_index=True)
#     merged_df.to_csv(output_path, index=False)
#     print(f"✅ Merged data written to {output_path}")



# RETURN TO THIS
def merge_csvs_for_card(card_config, tracked_year):
    card_info = card_config['card']
    if tracked_year == 0:
        folder  = card_info['folder_path'] + "/test_data"
    else:
        folder = card_info['folder_path']
    card_name = card_info['name'].replace(" ", "_")
    column_map = card_info.get('column_map', {})
    output_path = f"./merged_output/{card_name}.csv"

    print(f"Merging files for {card_info['name']}...")
    print(f"Folder PAth : {folder}")

    # all_files = glob(os.path.join(folder, "*.csv"))
    all_files = []
    for ext in ("*.csv", "*.xlsx"):
        print(ext)
        all_files.extend(glob(os.path.join(folder, ext)))

    if not all_files:
        print(f"No CSV files found in {folder}.")
        return

    dfs = []
    for file in all_files:

        # df = pd.read_csv(file)
        if file.endswith(".csv"):
            df = pd.read_csv(file)
        elif file.endswith(".xlsx"):
            df = pd.read_excel(file, header=6, engine="openpyxl")  # More reliable than default engine
        else:
            print(f"⚠️ Skipping unsupported file: {file}")
            continue

        #Edit lines before entering them into Homoginized CSV

        if card_info.get("clean_description_using_city_state"):
            if "Appears On Your Statement As" in df.columns and "City/State" in df.columns:
            # print(f"Amex Row -- {df["Description"]} ----- {df["City/State"]}")
                df["Description"] = df.apply(clean_description, axis=1)

        if card_info.get("merge_credit_debit"):
            if "Debit" in df.columns and "Credit" in df.columns:
                df["Debit"] = pd.to_numeric(df["Debit"], errors="coerce").fillna(0)
                df["Credit"] = pd.to_numeric(df["Credit"], errors="coerce").fillna(0)
                df["Amount"] = df["Debit"] * -1 + df["Credit"]
            else:
                print(f"Missing Debit/Credit columns in {card_info['name']}")    
        print("Your column names are")
        print(df.columns.tolist())

        df = normalize_signs_by_card(df, card_info)


        # print("RENAME COLUMNS CHECK")
        column_map = card_info.get("column_map", {})
        df = df.rename(columns=column_map)
        # print("📌 After renaming, DataFrame columns are:")
        # print(df.columns.tolist())

        if "Date" in df.columns:
            df["Date"] = df["Date"].astype(str).str.strip()
            df["Date"] = pd.to_datetime(df["Date"], errors="coerce")
            df["Date"] = df["Date"].dt.strftime("%Y-%m-%d")
        else:
            print(f"🚨 No 'Date' column found for {card_info['name']} after column renaming.")




        # 🧼 Normalize Date column
        if card_info.get("reformat_date"):
            print("There is an issue with the Date Column -- Reformating")
            if "Date" in df.columns:
                df["Date"] = df["Date"].astype(str).str.strip()
                df["Date"] = pd.to_datetime(df["Date"], errors="coerce")
            
                if df["Date"].isna().any():
                    print(f"⚠️ Warning: {df['Card'].iloc[0]} has rows with invalid dates")
            
                # Format date to consistent output string
                df["Date"] = df["Date"].dt.strftime("%Y-%m-%d")
    

        # Rename columns using card-specific map
        df = df.rename(columns=column_map)

        for col in ["Date", "Description", "Amount", "Category"]:
            if col not in df.columns:
                print (col)
                df[col] = ""

        df["Card"] = card_info["name"]
        df["Card Owner"] = card_info["owner"]
        df["Source File"] = os.path.basename(file)


        # Select and order normalized columns
        normalized = df[["Date", "Description", "Amount", "Category", "Card", "Card Owner", "Source File"]]


        dfs.append(normalized)

    merged_df = pd.concat(dfs, ignore_index=True)

    # Deduplicate using Date, Description, Amount
    deduped_df = merged_df.drop_duplicates(subset=["Date", "Description", "Amount"])

    os.makedirs("merged_output", exist_ok=True)
    output_file = os.path.join("merged_output", f"{card_name}.csv")

    save_csv(deduped_df, output_file)


def load_category_map(path="category_map.yml"):
    with open(path, "r") as f:
        full_yaml = yaml.safe_load(f)
        return full_yaml["category_map"]


def clean_description(row):
    desc = str(row["Appears On Your Statement As"]).strip()
    city_state = str(row["City/State"]).strip()

    # Normalize whitespace and newlines
    desc_clean = re.sub(r"\s+", " ", desc)
    city_state_clean = re.sub(r"\s+", " ", city_state)

    # Remove leading zeros from city_state to match odd formatting like 00WEST NEWTON
    city_state_clean = re.sub(r"\b0+", "", city_state_clean)

    # Compare end of string, case-insensitive
    if desc_clean.lower().endswith(city_state_clean.lower()):
        return desc_clean[: -len(city_state_clean)].rstrip(" ,").strip()

    return desc_clean

def normalize_signs_by_card(df, card_info):
    reverse = card_info.get("reverse_sign", False)

    if reverse:
        # Ensure purchases are positive, refunds/payments negative
        def flip_sign(amount):
            if pd.isna(amount):
                return amount
            return amount  # Leave as-is (correct convention)
    else:
        def flip_sign(amount):
            if pd.isna(amount):
                return amount
            return -amount  # Flip sign if card does opposite

    df["Amount"] = df["Amount"].apply(flip_sign)
    # print(f"🔁 Normalized signs for {card_info['name']} (reverse_sign={reverse})")

    return df


def combine_all_merged_csvs(config, output_dir="merged_output", combined_file=None):
    year = config.get("tracked_year")
    month = config.get("tracked_month")
    day = config.get("tracked_day")

    if combined_file is None:
        timestamp = datetime.now().strftime("-%H-%M-%S")
        # DEGUGGING LINE
        # combined_file = f"final_output/all_cards_{timestamp}.csv"
        combined_file = f"final_output/all_cards.csv"

    all_csvs = glob(os.path.join(output_dir, "*.csv"))
    all_csvs = [f for f in all_csvs if not f.endswith("all_cards.csv")]

    combined_dfs = []
    for csv_file in all_csvs:
        print(f"\n📂 Reading: {csv_file}")
        df = pd.read_csv(csv_file)
        print(f"    ✅ Rows before cleaning: {len(df)}")
        print(f"    🔢 Date range: {df['Date'].min()} to {df['Date'].max()}")
        print(f"    📄 Card column unique: {df['Card'].unique()}")
        combined_dfs.append(df)
    
    if combined_dfs:


        master_df = pd.concat(combined_dfs, ignore_index=True)
        print(f"\n🧩 Total combined rows before dropna: {len(master_df)}")

        print(f"HOMOGENIZING COLUMNS")
        category_map = load_category_map()
        master_df = apply_category_mapping(master_df, category_map)


        # Try to parse dates -- CAUSED ISSUES WITH CAPITAL ONE
        master_df["Date"] = pd.to_datetime(master_df["Date"], errors="coerce")
        master_df = master_df.dropna(subset=["Date"])

        print(f"📆 Total rows after valid Date parsing: {len(master_df)}")

        # Sort chronologically
        master_df = master_df.sort_values(by="Date")

        # Format date back to string -- CAUSED ISSUES WITH CAPITAL ONE
        master_df["Date"] = master_df["Date"].dt.strftime("%Y-%m-%d")

        # Deduplicate
        master_df = master_df.drop_duplicates(subset=["Date", "Description", "Amount"])

        print(f"✅ Final row count after deduplication: {len(master_df)}")
        print("\n")
        print("\n")

        # Ensure Date column is datetime
        master_df["Date"] = pd.to_datetime(master_df["Date"], errors="coerce")
        master_df = master_df.dropna(subset=["Date"])
        
        # Apply flexible date filtering
        if year:
            master_df = master_df[master_df["Date"].dt.year == int(year)]
        if month:
            master_df = master_df[master_df["Date"].dt.month == int(month)]
        if day:
            master_df = master_df[master_df["Date"].dt.day == int(day)]
        print(f"🚧Filtering to specified date range🚧")
        print(f"    📆 Filtered to Y:{year or '*'} M:{month or '*'} D:{day or '*'}")
        print(f"    📉 Rows after filtering: {len(master_df)}\n")
        
        save_csv(master_df, combined_file)

        print(f"\n📝 Combined and sorted data saved to: {combined_file}")

        print("\n📊 Final row counts by card:\n")
        print(master_df["Card"].value_counts())
        print(f"\n📝 Total row counts by card: {len(master_df)}\n")


    else:
        print("⚠️ No individual card CSVs found to combine.")
    print("⚠️TESTING⚠️ -- 1st 10 rows\n")
    # print(len(df))
    # print(df[95:100])    

def save_csv(df, output_path):
    # If the file already exists, delete it
    if os.path.exists(output_path):
        os.remove(output_path)
        print(f"🗑️ Removed old file: {output_path}")
    
    df.to_csv(output_path, index=False)
    print(f"✅ Saved merged file to {output_path}")

def main():
    config = load_yaml("config.yml")
    for card_yaml in config["cards"]:

        tracked_year = str(config["tracked_year"])
        card_config = load_yaml(card_yaml)
        # print(f"Loading {str(card_config["card"]["name"])}")
        merge_csvs_for_card(card_config, tracked_year)
    combine_all_merged_csvs(config)    

if __name__ == "__main__":
    main()
