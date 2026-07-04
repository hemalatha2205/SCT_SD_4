# Smart Product Information Extractor

A polished Python + Flask web app that scrapes public product information from supported sites such as Books to Scrape, displays it in a responsive dashboard, and exports it to CSV, JSON, or Excel.

## Features
- Enter a website URL or use a built-in sample site
- Extract product name, price, rating, and image
- Filter and search the extracted results
- View dashboard statistics
- Export data as CSV, JSON, or Excel

## Installation
1. Clone or open the project folder.
2. Install dependencies:
   ```bash
   python -m pip install -r requirements.txt
   ```
3. Run the app:
   ```bash
   python app.py
   ```
4. Open http://127.0.0.1:5000

## Example URL
- Example input: https://books.toscrape.com/

## Notes
- The app is designed for public and practice pages such as Books to Scrape.
- Some websites may block automated requests, so the scraper gracefully surfaces an error.

