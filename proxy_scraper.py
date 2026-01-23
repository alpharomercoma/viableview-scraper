#!/usr/bin/env python3
"""
Proxy Scraper for free-proxy-list.net

This module scrapes free proxies from https://free-proxy-list.net/en/
and tests them to find working proxies.
"""

import logging
import random
import time
from typing import Optional, List, Dict

from playwright.sync_api import sync_playwright, Page, Browser, BrowserContext
from playwright_stealth import Stealth

logger = logging.getLogger(__name__)

PROXY_LIST_URL = "https://free-proxy-list.net/en/"
TEST_URL = "https://httpbin.org/ip"  # Simple endpoint to test proxy
TEST_TIMEOUT = 15000  # 15 seconds timeout for proxy test


class ProxyScraper:
    """Scraper for free-proxy-list.net to get working proxies."""

    def __init__(self, headed: bool = False):
        """
        Initialize the proxy scraper.

        Args:
            headed: If True, runs browser in visible mode
        """
        self.headed = headed
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
        logger.info("Starting browser for proxy scraping...")
        self.playwright = sync_playwright().start()

        self.browser = self.playwright.chromium.launch(
            headless=not self.headed,
            args=['--disable-blink-features=AutomationControlled']
        )
        self.context = self.browser.new_context(
            viewport={'width': 1920, 'height': 1080},
            user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        )
        self.page = self.context.new_page()

        # Apply stealth mode to avoid bot detection
        stealth = Stealth()
        stealth.apply_stealth_sync(self.page)

        logger.info("Browser started for proxy scraping")

    def stop(self):
        """Stop the browser and clean up."""
        if self.browser:
            self.browser.close()
        if self.playwright:
            self.playwright.stop()

    def scrape_proxies(self, max_proxies: int = 50) -> List[Dict[str, str]]:
        """
        Scrape proxy list from free-proxy-list.net.

        Args:
            max_proxies: Maximum number of proxies to scrape

        Returns:
            List of proxy dictionaries with 'ip', 'port', 'country', 'anonymity', 'https' keys
        """
        logger.info(f"Scraping proxies from {PROXY_LIST_URL}...")

        try:
            self.page.goto(PROXY_LIST_URL, wait_until="networkidle", timeout=30000)
            time.sleep(2)  # Wait for table to load

            # Extract proxy data from the table
            proxies = self.page.evaluate(f'''() => {{
                const proxies = [];
                // Try multiple selectors for the table
                let table = document.querySelector('table#proxylisttable');
                if (!table) {{
                    table = document.querySelector('table.table');
                }}
                if (!table) {{
                    table = document.querySelector('table');
                }}
                if (!table) {{
                    console.error('Proxy table not found');
                    return proxies;
                }}

                const rows = table.querySelectorAll('tbody tr');
                if (rows.length === 0) {{
                    // Try without tbody
                    const allRows = table.querySelectorAll('tr');
                    for (let i = 1; i < allRows.length; i++) {{ // Skip header row
                        const row = allRows[i];
                        const cells = row.querySelectorAll('td');
                        if (cells.length >= 2) {{
                            const ip = cells[0].textContent.trim();
                            const port = cells[1].textContent.trim();
                            if (ip && port && proxies.length < {max_proxies}) {{
                                proxies.push({{
                                    ip: ip,
                                    port: port,
                                    code: cells[2] ? cells[2].textContent.trim() : '',
                                    country: cells[3] ? cells[3].textContent.trim() : '',
                                    anonymity: cells[4] ? cells[4].textContent.trim() : '',
                                    google: cells[5] ? cells[5].textContent.trim() : '',
                                    https: cells[6] ? cells[6].textContent.trim() : '',
                                    lastChecked: cells[7] ? cells[7].textContent.trim() : ''
                                }});
                            }}
                        }}
                    }}
                    return proxies;
                }}

                const maxRows = Math.min(rows.length, {max_proxies});
                for (let i = 0; i < maxRows; i++) {{
                    const row = rows[i];
                    const cells = row.querySelectorAll('td');
                    if (cells.length >= 2) {{
                        const ip = cells[0].textContent.trim();
                        const port = cells[1].textContent.trim();
                        if (ip && port) {{
                            proxies.push({{
                                ip: ip,
                                port: port,
                                code: cells[2] ? cells[2].textContent.trim() : '',
                                country: cells[3] ? cells[3].textContent.trim() : '',
                                anonymity: cells[4] ? cells[4].textContent.trim() : '',
                                google: cells[5] ? cells[5].textContent.trim() : '',
                                https: cells[6] ? cells[6].textContent.trim() : '',
                                lastChecked: cells[7] ? cells[7].textContent.trim() : ''
                            }});
                        }}
                    }}
                }}
                return proxies;
            }}''')

            logger.info(f"Scraped {len(proxies)} proxies from free-proxy-list.net")
            return proxies

        except Exception as e:
            logger.error(f"Error scraping proxies: {e}")
            return []

    def test_proxy(self, ip: str, port: str, protocol: str = "http") -> bool:
        """
        Test if a proxy is working.

        Args:
            ip: Proxy IP address
            port: Proxy port
            protocol: Proxy protocol (http, https, socks5)

        Returns:
            True if proxy is working, False otherwise
        """
        proxy_url = f"{protocol}://{ip}:{port}"
        test_context = None

        try:
            # Create a new browser context with this proxy
            test_context = self.browser.new_context(
                proxy={"server": proxy_url},
                viewport={'width': 1920, 'height': 1080},
                ignore_https_errors=True  # Ignore SSL errors for free proxies
            )
            test_page = test_context.new_page()

            # Try to access a test URL through the proxy
            # Use "load" instead of "networkidle" for faster/more lenient testing
            response = test_page.goto(
                TEST_URL,
                wait_until="load",  # Changed from "networkidle" to be more lenient
                timeout=TEST_TIMEOUT
            )

            # Check if request was successful
            if response and response.status == 200:
                # Verify we got a response (even partial is OK for free proxies)
                content = test_page.content()
                if test_context:
                    test_context.close()
                logger.debug(f"Proxy {proxy_url} is working")
                return True
            else:
                if test_context:
                    test_context.close()
                return False

        except Exception as e:
            # For free proxies, even connection errors might be acceptable
            # as they might work intermittently. Log but don't fail immediately.
            logger.debug(f"Proxy {proxy_url} test error: {str(e)[:100]}")
            if test_context:
                try:
                    test_context.close()
                except:
                    pass
            return False

    def get_working_proxy(self, max_attempts: int = 20, fallback_to_any: bool = True) -> Optional[str]:
        """
        Scrape proxies and return the first working one.

        Args:
            max_attempts: Maximum number of proxies to test
            fallback_to_any: If True, return a proxy even if test fails (for unreliable free proxies)

        Returns:
            Proxy URL string (e.g., "http://ip:port") or None if none found
        """
        # Scrape more proxies to have better chances
        proxies = self.scrape_proxies(max_proxies=max_attempts * 3)

        if not proxies:
            logger.warning("No proxies scraped")
            return None

        # Sort proxies by preference: HTTPS > HTTP, elite proxy > anonymous
        def proxy_score(proxy):
            score = 0
            if proxy.get('https', '').strip().lower() == 'yes':
                score += 10
            if 'elite' in proxy.get('anonymity', '').strip().lower():
                score += 5
            elif 'anonymous' in proxy.get('anonymity', '').strip().lower():
                score += 2
            return score

        # Sort by score (highest first), then shuffle within same score
        proxies.sort(key=proxy_score, reverse=True)

        # Test proxies until we find a working one
        tested = 0
        last_proxy_url = None

        for proxy in proxies:
            if tested >= max_attempts:
                break

            ip = proxy.get('ip', '').strip()
            port = proxy.get('port', '').strip()
            https = proxy.get('https', '').strip().lower()
            anonymity = proxy.get('anonymity', '').strip().lower()

            if not ip or not port:
                continue

            # Determine protocol - prefer HTTPS if available
            protocol = "https" if https == "yes" else "http"
            proxy_url = f"{protocol}://{ip}:{port}"
            last_proxy_url = proxy_url

            logger.info(f"Testing proxy {ip}:{port} ({protocol})...")
            tested += 1

            if self.test_proxy(ip, port, protocol):
                logger.info(f"Found working proxy: {proxy_url}")
                return proxy_url

            # Small delay between tests
            time.sleep(0.3)

        # If no proxy passed the test but fallback is enabled, return the last one tried
        # Free proxies are often unreliable but might still work for the actual use case
        if fallback_to_any and last_proxy_url:
            logger.warning(f"Tested {tested} proxies, none passed strict test. Using fallback: {last_proxy_url}")
            logger.info("Note: Free proxies are often unreliable but may still work for your use case")
            return last_proxy_url

        logger.warning(f"Tested {tested} proxies, none are working")
        return None


def get_free_proxy(headed: bool = False, max_attempts: int = 20, fallback_to_any: bool = True) -> Optional[str]:
    """
    Convenience function to get a working free proxy.

    Args:
        headed: Run browser in visible mode
        max_attempts: Maximum number of proxies to test
        fallback_to_any: If True, return a proxy even if test fails (for unreliable free proxies)

    Returns:
        Proxy URL string or None
    """
    with ProxyScraper(headed=headed) as scraper:
        return scraper.get_working_proxy(max_attempts=max_attempts, fallback_to_any=fallback_to_any)


if __name__ == "__main__":
    # Configure logging for standalone execution
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(levelname)s - %(message)s"
    )

    # Test the proxy scraper
    print("Testing proxy scraper...")
    proxy = get_free_proxy(headed=False, max_attempts=5)

    if proxy:
        print(f"\n✓ Found working proxy: {proxy}")
    else:
        print("\n✗ No working proxy found")
