from playwright.sync_api import sync_playwright
import pandas as pd
import time
import re


QUERY = "outfitidea"          # keyword 
TARGET_COUNT = 20      
SCROLL_ROUNDS = 15      
MIN_LIKES = 50000      
#=========================================


def parse_number(text):
    if not text:
        return 0
    text = text.replace(",", "").strip()
    if "M" in text:
        return int(float(text.replace("M", "")) * 1_000_000)
    if "K" in text:
        return int(float(text.replace("K", "")) * 1_000)
    digits = re.sub(r"\D", "", text)
    return int(digits) if digits else 0


results = []
seen_urls = set()

print("SCRIPT STARTED")

with sync_playwright() as p:
    browser = p.chromium.launch(headless=False)
    page = browser.new_page()
    page.set_viewport_size({"width": 1280, "height": 800})

    
    search_url = f"https://www.tiktok.com/search?q={QUERY}"
    print("Opening:", search_url)
    page.goto(search_url, timeout=60000)


    
    urls = []

    for i in range(SCROLL_ROUNDS):
        print(f"SEARCH SCROLL {i + 1}")

        page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
        time.sleep(3)

        links = page.query_selector_all("a[href*='/video/']")

        if len(links) == 0:
            time.sleep(3)
            links = page.query_selector_all("a[href*='/video/']")

        print("Links found:", len(links))

        for a in links:
            href = a.get_attribute("href")
            if not href:
                continue

            full_url = (
                f"https://www.tiktok.com{href}"
                if href.startswith("/")
                else href
            )

            if full_url not in seen_urls:
                seen_urls.add(full_url)
                urls.append(full_url)

        if len(urls) >= TARGET_COUNT * 2:
            break

    print(f"Collected {len(urls)} URLs. Visiting videos")

    
    for idx, url in enumerate(urls):
        if len(results) >= TARGET_COUNT:
            break

        print(f"[{idx + 1}] Opening video")
        page.goto(url, timeout=60000)
        time.sleep(5)

        try:
            like_el = page.query_selector("strong[data-e2e='like-count']")
            comment_el = page.query_selector("strong[data-e2e='comment-count']")

            likes = parse_number(like_el.inner_text()) if like_el else 0
            comments = parse_number(comment_el.inner_text()) if comment_el else 0

            print("Likes:", likes, "| Comments:", comments)

            if likes >= MIN_LIKES:
                results.append({
                    "url": url,
                    "likes": likes,
                    "comments": comments
                })

        except:
            print("Skipped")
            continue

    browser.close()

if results:
    df = pd.DataFrame(results)
    df = df.sort_values("likes", ascending=False)

    out_file = f"{QUERY}_top_videos.csv"
    df.to_csv(out_file, index=False)

    print(f"DONE")
else:
    print("None")


