"""
MarketBeat Analyst Ratings Scraper

This script scrapes analyst ratings, price targets, and Upside/Downside 
percentages from MarketBeat for a given stock symbol.

Dependencies:
- playwright, playwright-stealth, pandas, beautifulsoup4, lxml

Usage:
    python scrape_marketbeat.py
"""

from bs4 import BeautifulSoup
import json
import pandas as pd
from playwright.sync_api import sync_playwright
from playwright_stealth import Stealth

    
def get_marketbeat_data(symbol):
    url = f"https://www.marketbeat.com/stocks/NASDAQ/{symbol}/forecast/"

    with sync_playwright() as p:
        browser = p.chromium.launch(
            headless=True,
            args=["--disable-blink-features=AutomationControlled"]
        )

        stealth = Stealth()
        context = browser.new_context(
            viewport={"width":1920,"height":1080},
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0 Safari/537.36"
        )

        stealth.apply_stealth_sync(context)
        page = context.new_page()

        try:
            page.goto(url, wait_until="networkidle", timeout=60000)
            page.wait_for_timeout(2000)

            return page.content()

        except Exception as e:
            print(e)
            return None

        finally:
            browser.close()


def extract_tables(html): 
    soup = BeautifulSoup(html, "lxml")
    tables = soup.find_all("table")
    return [str(t) for t in tables]


def find_target_table(tables):
    for table in tables:
        text = BeautifulSoup(table, "lxml").get_text(" ", strip=True).lower()
        if "price target" in text and "analyst" in text:
            return table

    return None


def parse_marketbeat_table(table_html):
    soup = BeautifulSoup(table_html, "lxml")
    headers = [th.get_text(" ", strip=True) for th in soup.select("thead th")]
    rows_json = []

    for tr in soup.select("tbody tr"):
        row = {}
        cells = tr.find_all("td")

        for i, cell in enumerate(cells):
            header = headers[i] if i < len(headers) else f"col_{i}"
            # Prefer structured attributes
            if cell.has_attr("data-clean"):
                value = cell["data-clean"]
            elif cell.has_attr("data-sort-value"):
                value = cell["data-sort-value"]
            else:
                value = cell.get_text(" ", strip=True)

            row[header] = value

        rows_json.append(row)

    return rows_json


def clean_marketbeat_json(jsontables):
    cleaned_tables = []
    for table in jsontables:
        cleaned_rows = []
        for row in table:
            new_row = row.copy()

            # Split and keep only first part for Brokerage and Analyst
            if 'Brokerage' in new_row and '|' in new_row['Brokerage']:
                new_row['Brokerage'] = new_row['Brokerage'].split('|', 1)[0].strip()
            if 'Analyst' in new_row and '|' in new_row['Analyst']:
                new_row['Analyst'] = new_row['Analyst'].split('|', 1)[0].strip()

            # Split Rating into old_rating and rating
            if 'Rating' in new_row and '|' in new_row['Rating']:
                old, new = new_row['Rating'].split('|', 1)
                new_row['Old Rating'] = old.strip()
                new_row['Rating'] = new.strip()
            elif 'Rating' in new_row:
                new_row['Old Rating'] = ''
                new_row['Rating'] = new_row['Rating']

            # Split Price Target into old_price_target and price_target
            if 'Price Target' in new_row and '|' in new_row['Price Target']:
                old, new = new_row['Price Target'].split('|', 1)
                new_row['Old Price Target'] = old.strip()
                new_row['Price Target'] = new.strip()
            elif 'Price Target' in new_row:
                new_row['Old Price Target'] = ''
                new_row['Price Target'] = new_row['Price Target']

            cleaned_rows.append(new_row)
        cleaned_tables.append(cleaned_rows)
    return cleaned_tables


def scrape_marketbeat(symbol: str) -> list[dict]:
    """
    Scrape MarketBeat analyst ratings for a given symbol and return JSON.    
    Returns a dictionary with:
    - data: list of dictionaries with keys:
        - Date: str (YYYY-MM-DD)
        - Brokerage: str
        - Analyst: str
        - Action: str
        - Old Rating: str
        - Rating: str
        - Old Price Target: str
        - Price Target: str
        - Report Date Upside/Downside: str (percentage, e.g. "12%")
    - price_target_summary: dictionary with keys:
        - avg: float
        - median: float
        - high: float
        - low: float
        """

    content = get_marketbeat_data(symbol)
    
    tables = extract_tables(content)
    tables = find_target_table(tables)
    
    jsontables = parse_marketbeat_table(tables)
    cleantables = clean_marketbeat_json([jsontables])
    
    cleantables = [item for sublist in cleantables for item in sublist if isinstance(item, dict)]
    clean_rows = [r for r in cleantables if isinstance(r, dict) and 'Brokerage' in r]
    
    df = pd.DataFrame(clean_rows)
    df['Date'] = pd.to_datetime(df['Date'], format='%Y%m%d%H%M%S', errors='coerce')
    df['Date'] = df['Date'].dt.date
    
    #Reposition some columns
    cols = df.columns.tolist()
    cols.remove('Old Rating')
    cols.remove('Old Price Target')
    cols.insert(cols.index('Rating'), 'Old Rating')
    cols.insert(cols.index('Price Target'), 'Old Price Target')
    
    # reorder DataFrame
    df = df[cols]
    
    # Convert Upside/Downside to %
    df['Report Date Upside/Downside'] = (df['Report Date Upside/Downside'].astype(float) * 100).round(0).astype(int).astype(str) + '%'
    
    # For calculatons, make temp df, ignore zero values
    price_targets = df['Price Target'].replace('[\$,]', '', regex=True).astype(float)
    price_targets = price_targets[price_targets > 0]
    
    trgt_summary = {
        "avg": round(price_targets.mean(), 1),
        "median": round(price_targets.median(), 1),
        "high": round(price_targets.max(), 1),
        "low": round(price_targets.min(), 1)
    }
    
    #print(f"Target Average: {avg_target:.1f}, Median: {median_target:.1f}, High: {high:.1f}, Low: {low:.1f}")
    #print(df.to_string(index=False))
    data = df.to_dict(orient='records')
    return {"data": data, "price_target_summary": trgt_summary}
    

def main():
    symbol = "NVDA"
    data = scrape_marketbeat(symbol)
    print(json.dumps(data, indent=2, default=str))

if __name__ == "__main__":
    main()

