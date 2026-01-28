# Business Registry Web Scraper

A Python-based web scraper that extracts business data from the State Registry website (https://scraping-trial-test.vercel.app).

## Features

- **reCAPTCHA handling**: Supports both manual captcha solving (headed mode) and attempts automatic solving
- **Pagination support**: Automatically iterates through all result pages
- **Comprehensive data extraction**: Extracts business name, registration ID, status, filing date, and agent details
- **Error handling**: Robust error handling with retry logic for network issues
- **Logging**: Detailed logging to both console and log file (`scraper.log`)
- **Rate limiting**: Polite delays between requests to avoid overloading the server

## Requirements

- Python 3.8+
- Playwright
- Internet connection

## Installation

1. Clone this repository:
   ```bash
   git clone <repository-url>
   cd viableview-scraper
   ```

2. Create a virtual environment (recommended):
   ```bash
   python3 -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

4. Install Playwright browsers:
   ```bash
   python -m playwright install chromium
   ```

## Usage

### Basic Usage

Run the scraper with default settings:

```bash
python scraper.py --headed
```

This will:
1. Open a browser window
2. Wait for you to solve the reCAPTCHA
3. Scrape all businesses matching the default query ("llc")
4. Save results to `output.json`

### Command Line Options

```bash
python scraper.py [OPTIONS]
```

| Option | Short | Default | Description |
|--------|-------|---------|-------------|
| `--query` | `-q` | `llc` | Search query to find businesses |
| `--output` | `-o` | `output.json` | Output file path |
| `--headed` | | False | Run browser in visible mode for captcha solving |

### Examples

Search for businesses containing "tech":
```bash
python scraper.py --query "tech" --headed
```

Save output to a custom file:
```bash
python scraper.py --output my_results.json --headed
```

## Output Format

The scraper outputs JSON with the following structure:

```json
[
  {
    "business_name": "ABC COMPANY LLC",
    "registration_id": "123456",
    "status": "Active",
    "filing_date": "2023-05-14",
    "agent_name": "Sara Davis",
    "agent_address": "699 Broadway Ave",
    "agent_email": "sara.davis.e71f523a99c3@example.com"
  }
]
```

### Fields

| Field | Description |
|-------|-------------|
| `business_name` | The registered business name |
| `registration_id` | Unique registration/entity number |
| `status` | Current business status (Active, Inactive, etc.) |
| `filing_date` | Date the business was filed |
| `agent_name` | Registered agent's name |
| `agent_address` | Registered agent's address |
| `agent_email` | Registered agent's email |

## Libraries Used

| Library | Purpose |
|---------|---------|
| **Playwright** | Browser automation for handling dynamic content and reCAPTCHA |
| **argparse** | Command-line argument parsing (standard library) |
| **logging** | Structured logging to file and console (standard library) |
| **json** | JSON serialization for output (standard library) |

### Why Playwright?

1. **JavaScript rendering**: The target website is a Next.js application with client-side rendering
2. **reCAPTCHA support**: Playwright can interact with reCAPTCHA widgets
3. **Modern web support**: Handles modern JavaScript frameworks effectively
4. **Session management**: Maintains browser context for authenticated requests

## Architecture

The scraper follows a modular design:

```
scraper.py
├── BusinessScraper (main class)
│   ├── solve_captcha()      - Handle reCAPTCHA verification
│   ├── get_session()        - Obtain session token
│   ├── search()             - Execute API searches
│   ├── get_business_details() - Fetch detailed business info
│   └── scrape_all()         - Main scraping loop
└── main()                   - CLI entry point
```

## Error Handling

The scraper handles various error scenarios:

- **Network errors**: Logged and skipped, continues with next item
- **Missing elements**: Gracefully handles missing HTML elements
- **reCAPTCHA timeout**: Reports error if captcha not solved within 5 minutes
- **API errors**: Logs error details and continues processing

## Logging

All operations are logged to both:
- **Console**: Real-time progress updates
- **scraper.log**: Persistent log file for debugging

Log format:
```
2024-01-15 10:30:45 - INFO - Searching for 'llc' - page 1
2024-01-15 10:30:46 - INFO - Found 150 total businesses across 15 pages
```

## Limitations

1. **reCAPTCHA**: Requires manual solving in headed mode; automatic solving may not always work
2. **Rate limiting**: The script includes delays, but aggressive usage may be blocked
3. **Website changes**: The scraper depends on the current website structure
4. **Session expiry**: Long-running scrapes may need re-authentication

## Troubleshooting

### "Cannot solve captcha in headless mode"
Run the scraper with the `--headed` flag to solve the captcha manually.

### "Session expired" errors
The session token may have expired. Restart the scraper to get a new session.

### No results found
Try different search queries or verify the website is accessible.

## License

This project is created for educational/trial purposes only.
