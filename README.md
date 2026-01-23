# Business Registry Web Scraper

A Python-based web scraper that extracts business data from the State Registry website (https://scraping-trial-test.vercel.app).

## Features

- **Automatic reCAPTCHA solving (FREE)**: Solves reCAPTCHA v2 automatically using audio challenge and speech recognition
- **Stealth mode**: Uses playwright-stealth to avoid bot detection
- **Proxy support**: Rotate IPs to avoid rate limiting
- **Pagination support**: Automatically iterates through all result pages
- **Comprehensive data extraction**: Extracts business name, registration ID, status, filing date, and agent details
- **Error handling**: Robust error handling with retry logic and exponential backoff
- **Logging**: Detailed logging to both console and log file (`scraper.log`)
- **Rate limiting**: Polite delays between requests to avoid overloading the server

## Requirements

- Python 3.8+ (including Python 3.13)
- Playwright
- FFmpeg and FLAC (for audio processing)
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

5. Install system dependencies (Linux):
   ```bash
   sudo apt-get install -y ffmpeg flac
   ```

   On macOS:
   ```bash
   brew install ffmpeg flac
   ```

## Usage

### Basic Usage

Run the scraper (opens a visible browser for manual CAPTCHA solving):

```bash
python scraper.py
```

This will:
1. Launch a visible browser with stealth mode
2. Attempt to auto-solve reCAPTCHA using audio challenge
3. If auto-solve fails, prompt you to solve the CAPTCHA manually
4. Scrape all businesses matching the default query ("llc")
5. Save results to `output.json`

### Headless Mode (Automatic CAPTCHA Solving)

For automated/server environments, use headless mode:

```bash
python scraper.py --headless
```

### Using a Proxy

To avoid rate limiting on the audio challenge, use a proxy:

```bash
python scraper.py --proxy "http://host:port"
# Or with authentication:
python scraper.py --proxy "http://user:pass@host:port"
# SOCKS5 proxy:
python scraper.py --proxy "socks5://host:port"
```

### Auto-Fetch Proxy

To automatically fetch a free proxy:

```bash
python scraper.py --auto-proxy
```

### Headless Mode on Server (No Display)

```bash
xvfb-run python scraper.py --headed
```

### Command Line Options

```bash
python scraper.py [OPTIONS]
```

| Option | Short | Default | Description |
|--------|-------|---------|-------------|
| `--query` | `-q` | `llc` | Search query to find businesses |
| `--output` | `-o` | `output.json` | Output file path |
| `--headless` | | False | Run browser in headless mode (default is headed/visible) |
| `--proxy` | `-p` | None | Proxy server URL (e.g., `http://host:port`) |
| `--auto-proxy` | | False | Auto-fetch a free proxy from free-proxy-list.net |

### Examples

Search for businesses containing "tech" with a proxy:
```bash
python scraper.py --query "tech" --proxy "http://proxy.example.com:8080"
```

Run in headless mode with auto-proxy:
```bash
python scraper.py --headless --auto-proxy
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

## How CAPTCHA Solving Works

The scraper uses a **free** method to solve reCAPTCHA v2:

1. Clicks the reCAPTCHA checkbox
2. Requests the audio challenge
3. Downloads the audio file
4. Transcribes it using Google Speech Recognition API (free)
5. Enters the transcribed text
6. Submits the response

**Note**: Google may rate-limit audio challenges from the same IP. Use proxy rotation for high-volume scraping.

## Libraries Used

| Library | Purpose |
|---------|---------|
| **Playwright** | Browser automation for handling dynamic content |
| **playwright-stealth** | Avoids bot detection by masking automation signals |
| **playwright-recaptcha** | Free reCAPTCHA solving via audio challenge |
| **SpeechRecognition** | Audio transcription using Google's free API |
| **pydub** | Audio format conversion |
| **standard-aifc** | Python 3.13+ compatibility shim |

## Architecture

The scraper follows a modular design:

```
scraper.py
├── BusinessScraper (main class)
│   ├── _simulate_human_behavior() - Mouse movements and scrolling
│   ├── solve_captcha()      - Automatic reCAPTCHA solving with retry
│   ├── get_session()        - Obtain session token
│   ├── search()             - Execute API searches
│   ├── get_business_details() - Fetch detailed business info
│   └── scrape_all()         - Main scraping loop
└── main()                   - CLI entry point
```

## Error Handling

The scraper handles various error scenarios:

- **Rate limiting**: Exponential backoff with jitter for retries
- **Network errors**: Logged and skipped, continues with next item
- **Missing elements**: Gracefully handles missing HTML elements
- **reCAPTCHA timeout**: Falls back to manual solving in headed mode
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

## Troubleshooting

### "The reCAPTCHA rate limit has been exceeded"
Google has rate-limited your IP for audio challenges. Solutions:
1. Use a proxy: `python scraper.py --proxy "http://host:port"`
2. Wait a few hours and retry
3. Use headed mode for manual solving

### "FLAC conversion utility not available"
Install FLAC: `sudo apt-get install flac` (Linux) or `brew install flac` (macOS)

### "No module named 'aifc'" (Python 3.13+)
Install the compatibility package: `pip install standard-aifc`

### Browser fails to launch on headless server
Use xvfb for headed mode: `xvfb-run python scraper.py --headed`

### "Session expired" errors
The session token may have expired. Restart the scraper to get a new session.

### No results found
Try different search queries or verify the website is accessible.

## License

This project is created for educational/trial purposes only.
