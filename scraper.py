#!/usr/bin/env python3
"""
Business Registry Web Scraper

This script scrapes business data from the target website. It handles:
- reCAPTCHA verification (automatic via audio challenge - FREE)
- Pagination through all result pages
- Extraction of business details including agent information
- Error handling and logging
- Output to JSON format
- Proxy support for IP rotation

Usage:
    python scraper.py [--query QUERY] [--output OUTPUT] [--headed] [--proxy PROXY]

Arguments:
    --query   Search query (default: searches for all businesses with "llc")
    --output  Output file path (default: output.json)
    --headed  Run browser in headed mode (visible) for manual captcha solving
    --proxy   Proxy server URL (e.g., http://user:pass@host:port or socks5://host:port)
"""

import argparse
import json
import logging
import os
import random
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Optional

from playwright.sync_api import sync_playwright, Page, Browser, BrowserContext
from playwright_stealth import Stealth
from playwright_recaptcha import recaptchav2

# Configure logging
LOG_FILE = "scraper.log"
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler(LOG_FILE),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

# Constants
BASE_URL = "https://scraping-trial-test.vercel.app"
SEARCH_PAGE = f"{BASE_URL}/search"
RESULTS_PAGE = f"{BASE_URL}/search/results"
API_SEARCH = f"{BASE_URL}/api/search"
DEFAULT_QUERY = "llc"  # Default search term
REQUEST_DELAY = 1.0  # Delay between requests in seconds


class ScraperError(Exception):
    """Custom exception for scraper errors."""
    pass


class BusinessScraper:
    """
    Scraper for extracting business data from the State Registry website.

    This scraper handles reCAPTCHA verification and pagination to extract
    all business records matching a search query.
    """

    def __init__(self, headed: bool = False, proxy: Optional[str] = None):
        """
        Initialize the scraper.

        Args:
            headed: If True, runs browser in visible mode for captcha solving
            proxy: Optional proxy URL (e.g., http://user:pass@host:port)
        """
        self.headed = headed
        self.proxy = proxy
        self.session_token: Optional[str] = None
        self.playwright = None
        self.browser: Optional[Browser] = None
        self.context: Optional[BrowserContext] = None
        self.page: Optional[Page] = None

    def __enter__(self):
        """Context manager entry."""
        self.start()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.stop()

    def start(self):
        """Start the browser."""
        logger.info("Starting browser...")
        self.playwright = sync_playwright().start()

        # Configure proxy if provided
        proxy_config = None
        if self.proxy:
            logger.info(f"Using proxy: {self.proxy.split('@')[-1] if '@' in self.proxy else self.proxy}")
            proxy_config = {"server": self.proxy}

        self.browser = self.playwright.chromium.launch(
            headless=not self.headed,
            args=['--disable-blink-features=AutomationControlled'],
            proxy=proxy_config
        )
        self.context = self.browser.new_context(
            viewport={'width': 1920, 'height': 1080},
            user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        )
        self.page = self.context.new_page()

        # Apply stealth mode to avoid bot detection
        stealth = Stealth()
        stealth.apply_stealth_sync(self.page)

        logger.info("Browser started successfully (stealth mode enabled)")

    def stop(self):
        """Stop the browser and clean up."""
        logger.info("Closing browser...")
        if self.browser:
            self.browser.close()
        if self.playwright:
            self.playwright.stop()
        logger.info("Browser closed")

    def _simulate_human_behavior(self):
        """Simulate human-like mouse movements and scrolling."""
        try:
            # Random mouse movements
            for _ in range(random.randint(2, 4)):
                x = random.randint(100, 800)
                y = random.randint(100, 600)
                self.page.mouse.move(x, y)
                time.sleep(random.uniform(0.1, 0.3))

            # Random scroll
            self.page.mouse.wheel(0, random.randint(50, 150))
            time.sleep(random.uniform(0.2, 0.5))
        except Exception:
            pass  # Ignore errors in human simulation

    def solve_captcha(self, max_retries: int = 3) -> str:
        """
        Navigate to search page and solve captcha automatically using audio challenge.

        Uses playwright-recaptcha library which solves reCAPTCHA v2 for FREE by:
        1. Clicking the audio challenge button
        2. Downloading the audio file
        3. Using Google Speech Recognition API to transcribe it
        4. Entering the transcribed text

        Args:
            max_retries: Number of retry attempts for rate-limited requests

        Returns:
            The reCAPTCHA response token

        Raises:
            ScraperError: If captcha cannot be solved
        """
        logger.info("Navigating to search page for captcha...")
        self.page.goto(SEARCH_PAGE, wait_until="networkidle")

        # Simulate human-like behavior before interacting with CAPTCHA
        self._simulate_human_behavior()
        self.page.wait_for_timeout(random.randint(1500, 3000))

        # Check if captcha is present
        captcha_wrap = self.page.query_selector('.captcha-wrap')
        if not captcha_wrap:
            logger.warning("No captcha wrapper found on page")

        logger.info("Solving reCAPTCHA using audio challenge (FREE method)...")

        last_error = None
        for attempt in range(max_retries):
            if attempt > 0:
                # Exponential backoff with jitter for retries
                wait_time = (2 ** attempt) + random.uniform(1, 3)
                logger.info(f"Retry {attempt + 1}/{max_retries} after {wait_time:.1f}s wait...")
                time.sleep(wait_time)

                # Reload page for fresh CAPTCHA
                self.page.reload(wait_until="networkidle")
                self._simulate_human_behavior()
                self.page.wait_for_timeout(random.randint(1000, 2000))

            try:
                # Use playwright-recaptcha to solve the CAPTCHA automatically
                with recaptchav2.SyncSolver(self.page) as solver:
                    token = solver.solve_recaptcha()
                    logger.info("CAPTCHA solved successfully!")
                    return token

            except Exception as e:
                last_error = str(e)
                logger.warning(f"Attempt {attempt + 1} failed: {last_error}")

                if "rate limit" not in last_error.lower():
                    # If it's not a rate limit error, don't retry
                    break

        # All automatic attempts failed - fall back to manual in headed mode
        if self.headed:
            logger.info("=" * 50)
            logger.info("AUTO-SOLVE FAILED - MANUAL VERIFICATION REQUIRED")
            logger.info("Please solve the reCAPTCHA in the browser window")
            logger.info("The script will continue automatically after verification")
            logger.info("=" * 50)

            max_wait = 300  # 5 minutes max
            start_time = time.time()

            while time.time() - start_time < max_wait:
                token = self.page.evaluate(
                    "() => document.querySelector('#g-recaptcha-response')?.value || ''"
                )
                if token:
                    logger.info("Captcha solved manually!")
                    return token
                time.sleep(1)

            raise ScraperError("Timeout waiting for captcha to be solved")
        else:
            raise ScraperError(
                f"Cannot solve captcha automatically after {max_retries} attempts: {last_error}. "
                "Options: 1) Wait and retry later, 2) Use --headed flag for manual solving, "
                "3) Use a proxy to rotate IP address."
            )

    def get_session(self, captcha_token: str, query: str) -> str:
        """
        Get a session token by making an authenticated API request.

        Args:
            captcha_token: The reCAPTCHA response token
            query: The search query

        Returns:
            Session token for subsequent requests
        """
        logger.info("Getting session token...")

        # Make API request with captcha token
        result = self.page.evaluate(f'''async () => {{
            const response = await fetch('/api/search?q={query}&page=1', {{
                headers: {{
                    'x-recaptcha-token': '{captcha_token}'
                }}
            }});
            return await response.json();
        }}''')

        if 'error' in result:
            raise ScraperError(f"Failed to get session: {result['error']}")

        session = result.get('session')
        if session:
            logger.info("Session token obtained successfully")
            self.session_token = session
            return session
        else:
            logger.warning("No session token in response, using captcha token")
            self.session_token = captcha_token
            return captcha_token

    def search(self, query: str, page: int = 1) -> dict:
        """
        Execute a search query.

        Args:
            query: Search query string
            page: Page number (1-indexed)

        Returns:
            API response containing results, total, page, totalPages
        """
        if not self.session_token:
            raise ScraperError("No session token. Call solve_captcha first.")

        logger.info(f"Searching for '{query}' - page {page}")

        result = self.page.evaluate(f'''async () => {{
            const response = await fetch('/api/search?q={query}&page={page}', {{
                headers: {{
                    'x-search-session': '{self.session_token}'
                }}
            }});
            return await response.json();
        }}''')

        if 'error' in result:
            # Try with captcha token as fallback
            logger.warning(f"Session failed, error: {result['error']}")
            raise ScraperError(f"Search failed: {result['error']}")

        return result

    def get_business_details(self, business_id: str) -> dict:
        """
        Get detailed information for a specific business.

        Args:
            business_id: The business ID

        Returns:
            Business details including agent information
        """
        logger.info(f"Getting details for business {business_id}")

        url = f"{BASE_URL}/business/{business_id}"
        self.page.goto(url, wait_until="networkidle")
        self.page.wait_for_timeout(500)

        # Extract data from the page
        details = {}

        # Check if business was found
        content = self.page.content()
        if "Not Found" in content or "No business found" in content:
            logger.warning(f"Business {business_id} not found")
            return None

        # Extract business details from the page
        # The page uses a card-based layout with .card divs and .small.muted labels
        try:
            details = self.page.evaluate('''() => {
                const data = {};

                // Get business name from h2
                const h2 = document.querySelector('h2');
                if (h2) data.businessName = h2.textContent.trim();

                // Find all cards and extract data based on their labels
                const cards = document.querySelectorAll('.card');
                cards.forEach(card => {
                    const label = card.querySelector('.small.muted');
                    if (!label) return;

                    const labelText = label.textContent.trim();

                    if (labelText === 'Status') {
                        const statusSpan = card.querySelector('.status');
                        if (statusSpan) data.status = statusSpan.textContent.trim();
                    }
                    else if (labelText === 'Filing Date') {
                        const valueDiv = label.nextElementSibling;
                        if (valueDiv) data.filingDate = valueDiv.textContent.trim();
                    }
                    else if (labelText === 'Address') {
                        const valueDiv = label.nextElementSibling;
                        if (valueDiv) data.address = valueDiv.textContent.trim();
                    }
                    else if (labelText === 'Registered Agent') {
                        // Agent card has: label, name div, address div (muted), email div (muted)
                        const children = card.querySelectorAll('div');
                        let foundName = false;
                        children.forEach(child => {
                            const text = child.textContent.trim();
                            // Skip the label itself
                            if (text === 'Registered Agent') return;

                            // The name is in a div with font-weight:600 (not muted after the label)
                            if (!child.classList.contains('muted') && !foundName && text) {
                                data.agentName = text;
                                foundName = true;
                            }
                            // Address is in a muted div without "Email:"
                            else if (child.classList.contains('muted') && !text.startsWith('Email:') && text !== 'Registered Agent') {
                                data.agentAddress = text;
                            }
                            // Email is in a div starting with "Email:"
                            else if (text.startsWith('Email:')) {
                                const code = child.querySelector('code');
                                data.agentEmail = code ? code.textContent.trim() : text.replace('Email:', '').trim();
                            }
                        });
                    }
                });

                return data;
            }''')
        except Exception as e:
            logger.error(f"Error extracting details: {e}")

        return details

    def scrape_all(self, query: str) -> list:
        """
        Scrape all business records matching a query.

        Args:
            query: Search query string

        Returns:
            List of all business records with details
        """
        all_businesses = []

        # Get first page to determine total pages
        first_page = self.search(query, page=1)
        total_pages = first_page.get('totalPages', 1)
        total_results = first_page.get('total', 0)

        logger.info(f"Found {total_results} total businesses across {total_pages} pages")

        # Process first page results
        for business in first_page.get('results', []):
            business_data = self._process_business(business)
            all_businesses.append(business_data)

        # Process remaining pages
        for page_num in range(2, total_pages + 1):
            time.sleep(REQUEST_DELAY)  # Polite delay

            try:
                page_data = self.search(query, page=page_num)
                for business in page_data.get('results', []):
                    business_data = self._process_business(business)
                    all_businesses.append(business_data)
            except ScraperError as e:
                logger.error(f"Error fetching page {page_num}: {e}")
                continue

        logger.info(f"Scraped {len(all_businesses)} businesses total")
        return all_businesses

    def _process_business(self, business: dict) -> dict:
        """
        Process a business record from search results.

        Args:
            business: Raw business data from API

        Returns:
            Processed business record
        """
        business_id = business.get('id', '')

        # Try to get additional details from detail page
        details = None
        if business_id:
            time.sleep(REQUEST_DELAY / 2)  # Shorter delay for details
            try:
                details = self.get_business_details(business_id)
            except Exception as e:
                logger.warning(f"Could not get details for {business_id}: {e}")

        # Combine search results with detail page data
        # Output format per spec: business_name, registration_id, status, filing_date, agent_name, agent_address, agent_email
        record = {
            "business_name": business.get('businessName', ''),
            "registration_id": business.get('registrationId', ''),
            "status": business.get('status', ''),
            "filing_date": business.get('filingDate', ''),
            "agent_name": "",
            "agent_address": "",
            "agent_email": "",
        }

        # Add agent details from detail page if available
        if details:
            record["agent_name"] = details.get('agentName', '')
            record["agent_address"] = details.get('agentAddress', '')
            record["agent_email"] = details.get('agentEmail', '')
        else:
            # Use data from search results if available
            record["agent_name"] = business.get('agentName', '')
            record["agent_address"] = business.get('agentAddress', '')
            record["agent_email"] = business.get('agentEmail', '')

        return record


def save_output(data: list, output_file: str):
    """
    Save scraped data to output file.

    Args:
        data: List of business records
        output_file: Output file path
    """
    logger.info(f"Saving {len(data)} records to {output_file}")

    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

    logger.info(f"Data saved successfully to {output_file}")


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Scrape business data from State Registry website"
    )
    parser.add_argument(
        '--query', '-q',
        default=DEFAULT_QUERY,
        help=f"Search query (default: {DEFAULT_QUERY})"
    )
    parser.add_argument(
        '--output', '-o',
        default='output.json',
        help="Output file path (default: output.json)"
    )
    parser.add_argument(
        '--headed',
        action='store_true',
        help="Run browser in headed mode (visible) for captcha solving"
    )
    parser.add_argument(
        '--proxy', '-p',
        default=None,
        help="Proxy server URL (e.g., http://user:pass@host:port or socks5://host:port)"
    )

    args = parser.parse_args()

    logger.info("=" * 60)
    logger.info("Business Registry Scraper Starting")
    logger.info(f"Query: {args.query}")
    logger.info(f"Output: {args.output}")
    logger.info(f"Mode: {'Headed' if args.headed else 'Headless'}")
    logger.info(f"Proxy: {args.proxy if args.proxy else 'None'}")
    logger.info("=" * 60)

    try:
        with BusinessScraper(headed=args.headed, proxy=args.proxy) as scraper:
            # Step 1: Solve captcha
            captcha_token = scraper.solve_captcha()

            # Step 2: Get session token
            scraper.get_session(captcha_token, args.query)

            # Step 3: Scrape all pages
            businesses = scraper.scrape_all(args.query)

            # Step 4: Save output
            save_output(businesses, args.output)

        logger.info("Scraping completed successfully!")
        return 0

    except ScraperError as e:
        logger.error(f"Scraper error: {e}")
        return 1
    except Exception as e:
        logger.exception(f"Unexpected error: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
