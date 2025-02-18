# Schloss Stock Screener

A Python-based stock screener that runs on your computer to scan for stocks meeting Walter Schloss's investment criteria. The screener is designed to run daily (Monday–Friday), saving a log of all stocks processed and a separate, timestamped file with only the recommended stocks. It also includes an option to send the recommendations via email using Gmail OAuth2.

## Table of Contents

- [Introduction](#introduction)
- [Walter Schloss Investment Philosophy](#walter-schloss-investment-philosophy)
- [Factors & Guidelines Needed to Make Money in the Stock Market](#factors--guidelines-needed-to-make-money-in-the-stock-market)
- [Buying Guidelines](#buying-guidelines)
- [Stock Selection Criteria (All-In-One Screener)](#stock-selection-criteria-all-in-one-screener)
- [Installation](#installation)
- [Usage](#usage)
- [Test Email Mode](#test-email-mode)
- [License](#license)

## Introduction

This project implements a stock screener based on the investment philosophy and criteria of Walter Schloss, a renowned value investor. The screener uses quantitative measures (e.g., book value, debt ratios, price-to-book, profitability) and qualitative filters (excludes financials, real estate, tobacco, OTC, and penny stocks) to generate a list of recommended stocks. The results are saved locally for review and can optionally be emailed automatically.

## Walter Schloss Investment Philosophy

- **Buy value, diversify adequately (but not excessively), be patient.**
- **Rarely talked to management; invested only on the numbers.**
- **Look at assets (book value) more than the income statement.**
- **"Asset values fluctuate more slowly than earnings do."**
- **Bought at low price-to-book ratios.**
- **When he did look at earnings, he liked low prices to normalized earnings.**
- **He liked stocks with long (15–20 year) histories and track records.**
- **Diversified, cheap basket of stocks was his strategy for risk.**
- **Often owned 60–100 stocks or more at a time.**
- **Max concentration of 10% toward any 1 stock.**
- **Average holding period was 4 years.**

## Factors & Guidelines Needed to Make Money in the Stock Market

1. **Price is the most important factor** to use in relation to value.
2. **Try to establish the value of the company.** A share of stock represents part of a business, not just a piece of paper.
3. **Use book value as a starting point.** Ensure that debt does not equal 100% of equity.
4. **Have patience.** Stocks don’t go up immediately.
5. **Don’t buy on tips or for a quick move.** Let professionals do that. Don’t sell on bad news.
6. **Don’t be afraid to be a loner,** but ensure you are correct in your judgment. Look for weaknesses in your thinking. Buy on a scale and sell on a scale-up.
7. **Have the courage of your convictions** once you have made a decision.
8. **Have a philosophy of investment and try to follow it.**

## Buying Guidelines

- Preferably **½ - 2/3 of book value**.
- Would pay up to book value or slightly over.
- **NEVER paid 2x book.**
- Sought “unloved” areas of the market.
- Did not buy financials or tobacco.
- Averaged in (did not take full position immediately).
- “Don’t know a stock until you own it.”
- Up to **10% in any 1 position**.
- Looked for prices near **3-year lows**.
- Never disclosed holdings to limited partners.

## Stock Selection Criteria (All-In-One Screener)

- **Fundamental Tab:**
  - **Industry:** Exclude financials and REITs.
  - **Market Cap:** > $50 million (optional).
  - **Debt to Equity:** < 0.4.
  - **OTC Stocks:** Exclude.
- **Valuation Ratio Tab:**
  - **P/B (Price to Book):** < 1.2.
- **Profitability Tab:**
  - **Net Margin:** > 0.
- **Historical Valuation Tab:**
  - **Max % Above 3-Year Low:** 35%.
- **Additional Condition:**
  - Exclude penny stocks (current price must be above $5).

## Installation

**Clone the repository:**

   ```bash
   git clone https://github.com/your_username/schloss-stock-screener.git
   cd schloss-stock-screener
   ```
    

**Create a virtual environment (optional but recommended):**

   ```bash
   Copy
   python -m venv venv
   source venv/bin/activate  # On Windows, use: venv\Scripts\activate
```

**Install the required packages:**

   ```bash
   Copy
   pip install -r requirements.txt
```

**Example requirements.txt:**
  - **nginx**
  - **Copy**
  - **yfinance**
  - **pandas**
  - **yahoo_fin**
  - **google-auth-oauthlib**
  - **google-auth**
  - **requests**

**Obtain Gmail OAuth2 Credentials:**

Create a project in the Google Cloud Console.
Enable the Gmail API.
Create OAuth 2.0 credentials for a Desktop App.
Download the client_secret.json file and place it in the root of the repository.
Usage

**To run the full stock screener:**

   ```bash
   Copy
   python stock_screener.py
   ```

**This will:**
Load or generate a list of U.S. stock tickers.
Process each ticker based on the criteria.
Append a log of all stocks processed to all_stocks_results.txt.
Save the recommended stocks (qualifiers) to a timestamped file in the results folder (keeping only the latest 7 runs).

**Test Email Mode**
To test the email functionality without running the full screening process:

   ```bash
   Copy
   python stock_screener.py --test-email
   ```

This sends a test email using dummy stock data. Make sure to update the email placeholder in the code (e.g., "your_email@gmail.com") with your actual email address if you intend to send real emails.

**License**
This project is licensed under the MIT License. See the LICENSE file for details.

## Disclaimer

This project is provided for educational purposes only. The author is not responsible for any financial losses or damages resulting from the use of this software. Always conduct your own research and consider seeking professional financial advice before making any investment decisions.
