import os
import re
import sys
import time
import pickle
import base64
import smtplib
import yfinance as yf
import pandas as pd
from datetime import datetime
from email.mime.text import MIMEText
from yahoo_fin import stock_info as si
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request

# ----------------------------
# Ticker List Functions
# ----------------------------

def generate_ticker_list(filename="us_stocks.txt"):
    tickers_set = set()
    try:
        # Pull tickers from S&P 500, NASDAQ, and Dow lists via yahoo_fin
        sp500 = si.tickers_sp500()
        nasdaq = si.tickers_nasdaq()
        dow = si.tickers_dow()
        
        # Combine them into a single sorted list
        tickers_set.update(sp500)
        tickers_set.update(nasdaq)
        tickers_set.update(dow)
        tickers_list = sorted(list(tickers_set))
        
        # Write the list to a file
        with open(filename, "w") as f:
            for ticker in tickers_list:
                f.write(ticker + "\n")
        print(f"Generated and saved {len(tickers_list)} tickers to {filename}")
        return tickers_list
    except Exception as e:
        print(f"Error generating ticker list: {e}")
        return []

def load_tickers(filename="us_stocks.txt"):
    if not os.path.exists(filename):
        print(f"{filename} not found. Generating ticker list...")
        return generate_ticker_list(filename)
    try:
        with open(filename, "r") as f:
            tickers = [line.strip() for line in f if line.strip()]
        print(f"Loaded {len(tickers)} tickers from {filename}")
        return tickers
    except Exception as e:
        print(f"Error loading tickers: {e}")
        return []

def is_valid_ticker(ticker):
    return bool(re.search(r'[A-Za-z0-9]', ticker))

# ----------------------------
# Data Fetching and Screening
# ----------------------------

def fetch_stock_data(ticker, max_retries=3):
    """
    Fetches fundamental (info) and historical (hist) data for a given ticker using yfinance.
    Retries up to max_retries if rate limits are encountered.
    """
    retries = 0
    delay = 1  # initial delay in seconds
    while retries < max_retries:
        try:
            stock = yf.Ticker(ticker)
            info = stock.info
            hist = stock.history(period="3y")  # Historical data for the past 3 years
            return info, hist
        except Exception as e:
            error_message = str(e)
            if "Too Many Requests" in error_message or "401 Client Error" in error_message:
                print(f"Rate limit hit for {ticker}. Retrying in {delay} seconds...")
                time.sleep(delay)
                retries += 1
                delay *= 2  # exponential backoff
            else:
                raise e
    raise Exception(f"Failed to fetch data for {ticker} after {max_retries} retries.")

def stock_qualifies(info, hist):
    """
    Applies Walter Schloss-inspired screening criteria to a given stock's data:
    1. Excludes Financial, Real Estate, and Tobacco industries.
    2. Excludes OTC stocks (if exchange info is available).
    3. Requires Market Cap > 50M.
    4. Requires Debt to Equity < 0.4.
    5. Requires Price/Book < 1.2.
    6. Requires Net Margin > 0.
    7. Price must be within 35% above the 3-year low.
    8. Excludes penny stocks (price < 5).
    """
    industry = info.get("industry", "")
    if industry:
        lower_industry = industry.lower()
        if "financial" in lower_industry or "real estate" in lower_industry:
            return False
        if "tobacco" in lower_industry:
            return False

    # Exclude OTC stocks if the exchange is listed as "otc"
    exchange = info.get("exchange", "")
    if exchange and "otc" in exchange.lower():
        return False

    # Market Cap: > 50 million
    if info.get("marketCap", 0) < 50e6:
        return False

    # Debt to Equity: < 0.4
    if info.get("debtToEquity", 100) > 0.4:
        return False

    # Price/Book Ratio: < 1.2
    if info.get("priceToBook", 100) >= 1.2:
        return False

    # Net Margin > 0
    if info.get("profitMargins", 0) <= 0:
        return False

    # Historical price check: must be within 35% above the 3-year low
    if hist.empty:
        return False
    three_year_low = hist['Low'].min()
    current_price = info.get("regularMarketPrice")
    if current_price is None:
        return False

    # Exclude penny stocks: current price must be >= 5
    if current_price < 5:
        return False

    if (current_price - three_year_low) / three_year_low > 0.35:
        return False

    return True

def build_screener(tickers):
    """
    Screens a list of tickers using the above criteria, returning two lists:
    1. qualifying: Tickers that pass the criteria
    2. all_results: A log of all tickers processed with their statuses
    """
    qualifying = []
    all_results = []
    for ticker in tickers:
        if not is_valid_ticker(ticker):
            line = f"{ticker} - Skipped invalid ticker"
            print(f"\nSkipping invalid ticker: {ticker}")
            all_results.append(line)
            continue

        print(f"\nProcessing ticker: {ticker}")
        try:
            info, hist = fetch_stock_data(ticker)
            # Gather key metrics for logging
            industry = info.get("industry")
            market_cap = info.get("marketCap")
            debt_to_equity = info.get("debtToEquity")
            price_to_book = info.get("priceToBook")
            profit_margins = info.get("profitMargins")

            if hist.empty:
                three_year_low = "N/A"
                current_price = "N/A"
            else:
                three_year_low = hist['Low'].min()
                current_price = info.get("regularMarketPrice")

            print(f"Industry: {industry}")
            print(f"Market Cap: {market_cap}")
            print(f"Debt to Equity: {debt_to_equity}")
            print(f"Price/Book: {price_to_book}")
            print(f"Profit Margins: {profit_margins}")
            print(f"3-Year Low: {three_year_low}")
            print(f"Current Price: {current_price}")

            qualifies = stock_qualifies(info, hist)
            if qualifies:
                qualifying.append(ticker)
                result_line = f"{ticker} - Qualifies"
                print("=> Qualifies")
            else:
                result_line = f"{ticker} - Does not qualify"
                print("=> Does not qualify")
            all_results.append(result_line)
        except Exception as e:
            error_line = f"{ticker} - Error: {e}"
            print(error_line)
            all_results.append(error_line)

        # Small delay to reduce rate limiting
        time.sleep(1)

    return qualifying, all_results

# ----------------------------
# Saving Results
# ----------------------------

from datetime import datetime

def save_all_results(all_results, filename="all_stocks_results.txt"):
    """
    Appends a timestamped log of every processed ticker to one file.
    """
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    with open(filename, "a") as f:
        f.write(f"Run at {timestamp}\n")
        for line in all_results:
            f.write(line + "\n")
        f.write("\n")
    print(f"All stock results appended to {filename}")

def save_recommended_results(qualifying, folder="results"):
    """
    Saves a timestamped file of only the qualifying tickers.
    Keeps the last 7 runs by removing older files.
    """
    if not os.path.exists(folder):
        os.makedirs(folder)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = os.path.join(folder, f"results_{timestamp}.txt")
    with open(filename, "w") as f:
        f.write("Stocks meeting Walter Schloss criteria:\n")
        for stock in qualifying:
            f.write(stock + "\n")
    print(f"Recommended results saved to {filename}")

    prune_old_results(folder, max_files=7)

def prune_old_results(folder, max_files=7):
    """
    Removes older files so that only the newest 7 remain.
    """
    files = [os.path.join(folder, f) for f in os.listdir(folder)
             if f.startswith("results_") and f.endswith(".txt")]
    if len(files) > max_files:
        files.sort(key=lambda x: os.path.getmtime(x))
        for file in files[:-max_files]:
            os.remove(file)
            print(f"Removed old result file: {file}")

# ----------------------------
# Email via Gmail OAuth2 (Generic)
# ----------------------------

SCOPES = ['https://mail.google.com/']

def get_credentials():
    """
    Gets valid user credentials from storage or runs the OAuth2 flow.
    Expects a file named 'client_secret.json' in the current directory.
    """
    creds = None
    token_pickle = 'token.pickle'
    if os.path.exists(token_pickle):
        with open(token_pickle, 'rb') as token:
            creds = pickle.load(token)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file('client_secret.json', SCOPES)
            creds = flow.run_local_server(port=0)
        with open(token_pickle, 'wb') as token:
            pickle.dump(creds, token)
    return creds

def generate_oauth2_string(username, access_token):
    """
    Creates the OAuth2 authentication string for Gmail SMTP.
    """
    auth_string = f'user={username}\1auth=Bearer {access_token}\1\1'
    return base64.b64encode(auth_string.encode()).decode()

def send_email_via_gmail_oauth2(qualifying, gmail_user="your_email@gmail.com"):
    """
    Sends an email to 'gmail_user' using Gmail OAuth2 authentication,
    listing the qualifying stocks. Replace 'your_email@gmail.com' with your actual address.
    """
    creds = get_credentials()
    access_token = creds.token
    auth_string = generate_oauth2_string(gmail_user, access_token)

    body = "Stocks meeting Walter Schloss criteria:\n" + "\n".join(qualifying)
    msg = MIMEText(body)
    msg["Subject"] = "Daily Walter Schloss Stock Screener Results"
    msg["From"] = gmail_user
    msg["To"] = gmail_user  # Sending to self for testing

    smtp_server = "smtp.gmail.com"
    smtp_port = 587
    server = smtplib.SMTP(smtp_server, smtp_port)
    server.ehlo()
    server.starttls()
    server.ehlo()
    server.docmd('AUTH', 'XOAUTH2 ' + auth_string)
    server.sendmail(gmail_user, [gmail_user], msg.as_string())
    server.quit()
    print("Test email sent successfully via Gmail OAuth2.")

# ----------------------------
# Main Execution
# ----------------------------

def main():
    # Check for test email flag
    if "--test-email" in sys.argv:
        # Dummy list for demonstration
        dummy_qualifying = ["AAPL", "MSFT", "GOOGL"]
        send_email_via_gmail_oauth2(dummy_qualifying, gmail_user="your_email@gmail.com")
        return

    # Load or generate tickers
    tickers = load_tickers("us_stocks.txt")
    if not tickers:
        print("No tickers loaded. Exiting.")
        return

    # Build the screener
    qualifying_stocks, all_results = build_screener(tickers)

    # Print any qualifying stocks
    if qualifying_stocks:
        print("\nStocks meeting Walter Schloss criteria:")
        for stock in qualifying_stocks:
            print(stock)
    else:
        print("\nNo stocks met the criteria.")

    # Save all processed results (append to one file)
    save_all_results(all_results)

    # Save only recommended stocks (timestamped) and prune old files
    save_recommended_results(qualifying_stocks)

    # Uncomment to send email after full screening:
    # send_email_via_gmail_oauth2(qualifying_stocks, gmail_user="your_email@gmail.com")

if __name__ == "__main__":
    main()

