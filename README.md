# Business Registry Web Scraper

A Python-based web scraper that extracts business data from the State Registry website (https://scraping-trial-test.vercel.app).

## Features

- **Automatic reCAPTCHA Solving**: Uses the `playwright-recaptcha` library to automatically solve reCAPTCHA v2 via audio challenges - no API key required!
- **Full-Crawl Mode**: Scrapes ALL businesses by searching multiple entity types (LLC, Inc, Corp, Company, etc.) in a single run
- **Pagination Support**: Automatically iterates through all result pages
- **Comprehensive Data Extraction**: Extracts business name, registration ID, status, filing date, and agent details
- **Deduplication**: Automatically removes duplicate businesses when using full-crawl mode
- **Error Handling**: Robust error handling with logging for debugging
- **Logging**: Detailed logging to both console and log file (`scraper.log`)
- **Rate Limiting**: Polite delays between requests to avoid overloading the server

## Requirements

- Python 3.8+
- Playwright
- FFmpeg (for audio captcha solving)
- Internet connection

## Installation

1. Clone this repository:
   ```bash
   git clone <repository-url>
   cd viableview-scraper
   ```

2. Install FFmpeg (required for audio captcha solving):
   ```bash
   # Ubuntu/Debian
   sudo apt-get install ffmpeg

   # macOS
   brew install ffmpeg

   # Windows
   winget install ffmpeg
   ```

3. Create a virtual environment (recommended):
   ```bash
   python3 -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

4. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

5. Install Playwright browsers:
   ```bash
   python -m playwright install chromium
   ```

## Usage

### Full Crawl (Recommended)

Scrape ALL businesses from the registry in a single run:

```bash
python scraper.py --full-crawl
```

This will:
1. Automatically solve the reCAPTCHA using audio recognition
2. Search for multiple entity types (LLC, Inc, Corp, Company, etc.)
3. Deduplicate results and save all unique businesses to `output.json`

### Basic Usage

Scrape businesses matching a specific query:

```bash
python scraper.py --query "llc"
```

### Command Line Options

```bash
python scraper.py [OPTIONS]
```

| Option | Short | Default | Description |
|--------|-------|---------|-------------|
| `--query` | `-q` | `llc` | Search query to find businesses |
| `--output` | `-o` | `output.json` | Output file path |
| `--headed` | | False | Run browser in visible mode (for debugging or manual captcha fallback) |
| `--full-crawl` | | False | **Scrape ALL businesses** by searching multiple entity types |

### Examples

**Full crawl with custom output file:**
```bash
python scraper.py --full-crawl --output all_businesses.json
```

**Search for specific businesses:**
```bash
python scraper.py --query "tech" --output tech_companies.json
```

**Debug mode with visible browser:**
```bash
python scraper.py --full-crawl --headed
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
| **playwright-recaptcha** | Automatic reCAPTCHA v2 solving using audio challenges |
| **pydub** | Audio processing for captcha audio files |
| **SpeechRecognition** | Transcribes audio using Google's free Speech-to-Text API |
| **argparse** | Command-line argument parsing (standard library) |
| **logging** | Structured logging to file and console (standard library) |
| **json** | JSON serialization for output (standard library) |

### Why These Libraries?

1. **Playwright**: The target website is a Next.js application with client-side rendering and reCAPTCHA protection
2. **playwright-recaptcha**: Provides automatic audio captcha solving without requiring paid API keys
3. **SpeechRecognition**: Uses Google's free speech recognition API - no API key needed!

## Architecture

The scraper follows a modular design:

```
scraper.py
├── BusinessScraper (main class)
│   ├── solve_captcha()        - Automatic reCAPTCHA solving via audio recognition
│   ├── get_session()          - Obtain session token
│   ├── search()               - Execute API searches
│   ├── get_business_details() - Fetch detailed business info
│   ├── scrape_all()           - Scrape all pages for a query
│   └── full_crawl()           - Full database crawl (multi-query)
└── main()                     - CLI entry point
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

1. **reCAPTCHA**: Audio solving requires FFmpeg to be installed; falls back to manual solving in headed mode if audio fails
2. **Rate limiting**: The script includes delays, but aggressive usage may be blocked
3. **Website changes**: The scraper depends on the current website structure
4. **Session expiry**: Long-running scrapes may need re-authentication

## Troubleshooting

### "Cannot solve captcha automatically"
Ensure FFmpeg is installed and in your PATH. If audio solving fails, run with `--headed` flag for manual fallback.

### "Session expired" errors
The session token may have expired. Restart the scraper to get a new session.

### No results found
Try different search queries or verify the website is accessible.

## License

This project is created for educational/trial purposes only.
