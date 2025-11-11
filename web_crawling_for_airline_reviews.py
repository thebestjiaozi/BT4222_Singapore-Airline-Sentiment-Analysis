import re, time, csv
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

opts = Options()
# keep visible while testing (headless often gets blocked)
# opts.add_argument("--headless=new")
opts.add_argument("--window-size=1280,900")
opts.add_argument("--disable-blink-features=AutomationControlled")
opts.add_argument("--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123 Safari/537.36")
driver = webdriver.Chrome(options=opts)

def scrape_page(page):
    url = f"https://www.airlinequality.com/airline-reviews/singapore-airlines/page/{page}/?sortby=post_date%3Adesc&pagesize=10"
    driver.get(url)
    time.sleep(8)  # allow PoW/JS to finish

    # wait for at least one review body
    try:
        WebDriverWait(driver, 12).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "div.text_content[itemprop='reviewBody']"))
        )
    except:
        return []

    rows = []
    # iterate over review blocks by the 'body' container
    blocks = driver.find_elements(By.CSS_SELECTOR, "div.body[id^='anchor']")
    for b in blocks:
        # title
        title = None
        t = b.find_elements(By.CSS_SELECTOR, "h2.text_header")
        if t: title = t[0].text.strip()

        # body text
        body = None
        ps = b.find_elements(By.CSS_SELECTOR, "div.text_content[itemprop='reviewBody'] p")
        if ps:
            body = " ".join(p.text.strip() for p in ps if p.text.strip())
        else:
            # sometimes body text is directly inside the div
            d = b.find_elements(By.CSS_SELECTOR, "div.text_content[itemprop='reviewBody']")
            if d: body = d[0].text.strip()

        # date (meta sibling before the 'body' div)
        date = None
        try:
            date_meta = b.find_element(By.XPATH, "./preceding-sibling::meta[@itemprop='datePublished']")
            date = date_meta.get_attribute("content")
        except:
            pass

        # ratingValue / bestRating inside the 'reviewRating' block before the body
        rating_value = None
        try:
            rr = b.find_element(By.XPATH, "./preceding-sibling::div[@itemprop='reviewRating']")
            rv = rr.find_elements(By.CSS_SELECTOR, "span[itemprop='ratingValue']")
            if rv: rating_value = int(rv[0].text.strip())
        except:
            pass

        # normalize to 1–5 if you want
        rating_out_of_5 = None
        if rating_value is not None:
            rating_out_of_5 = round(rating_value, 1)

        if title or body:
            rows.append({
                "date_published": date,
                "rating_value_10": rating_value,
                "rating_value_5": rating_out_of_5,
                "title": title,
                "body": body,
            })
    return rows

all_rows = []
for p in range(0, 168):
    page_rows = scrape_page(p)
    print(f"Page {p}: {len(page_rows)} reviews")
    if not page_rows and p == 1:
        print(driver.page_source[:1500])  # debug: are you still on bot page?
    if not page_rows:
        break
    all_rows.extend(page_rows)

driver.quit()

if all_rows:
    with open("skytrax_reviews4.csv", "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=all_rows[0].keys())
        writer.writeheader()
        writer.writerows(all_rows)
    print(f"✅ Saved {len(all_rows)} reviews.")
else:
    print("⚠️ No reviews scraped.")
