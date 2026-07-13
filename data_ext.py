import pandas as pd
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin
import os
import re
from datetime import datetime   # ✅ timestamp for file names

# ---------------- CONFIG ---------------- #
REGULAR_PRICE_CLASSES = [ "money","money buckscc-money"
    ]

DISCOUNT_PRICE_CLASSES = [
    "money"
]
# ----------------------------------------- #

def is_regular_price_class(class_name: str) -> bool:
    return any(keyword in class_name.lower() for keyword in REGULAR_PRICE_CLASSES)

def is_discount_price_class(class_name: str) -> bool:
    return any(keyword in class_name.lower() for keyword in DISCOUNT_PRICE_CLASSES)

def extract_prices(container):
    price_candidates = []
    for tag in container.find_all(['span', 'div', 'dd', 'p', 's', 'del', 'ins', 'strong', 'small']):
        text = tag.get_text(strip=True)
        if not text or not re.search(r'\d', text):
            continue
        classes = " ".join(tag.get("class", [])).lower()
        price_candidates.append({'tag': tag, 'classes': classes, 'text': text})

    regular = ""
    discounted = ""

    for pc in price_candidates:
        cl = pc['classes']
        txt = pc['text']
        if is_regular_price_class(cl):
            regular = txt
        if is_discount_price_class(cl):
            discounted = txt

    # if not regular:
    #     for pc in price_candidates:
    #         if pc['tag'].name in ['s', 'del', 'strike']:
    #             regular = pc['text']
    #             break
    #         if pc['tag'].find_parent(['s', 'del', 'strike']):
    #             regular = pc['text']
    #             break

    # def extract_number(txt):
    #     num = re.sub(r'[^\d.,]', '', txt)
    #     if not num:
    #         return None
    #     num = num.replace(',', '')
    #     try:
    #         return float(num)
    #     except:
    #         try:
    #             return float(num.replace(',', '.'))
    #         except:
    #             return None

    # if (not regular or not discounted) and price_candidates:
    #     numbers = []
    #     for pc in price_candidates:
    #         val = extract_number(pc['text'])
    #         if val is not None:
    #             numbers.append((pc, val))
    #     if len(numbers) >= 2:
    #         numbers_sorted = sorted(numbers, key=lambda x: x[1], reverse=True)
    #         if not regular:
    #             regular = numbers_sorted[0][0]['text']
    #         if not discounted:
    #             for item in numbers_sorted[1:]:
    #                 if item[0]['text'] != regular:
    #                     discounted = item[0]['text']
    #                     break
    #     elif len(numbers) == 1:
    #         if not discounted:
    #             discounted = numbers[0][0]['text']

    # if not regular:
    #     regular = "NA"
    # if not discounted:
    #     discounted = "NA"

    return regular, discounted


def scrape_ecommerce():
    url = input("Enter the URL of the e-commerce website: ").strip()

    if not (url.startswith("http://") or url.startswith("https://")):
        print("❌ Invalid URL. Please include 'http://' or 'https://' ")
        return

    r = requests.get(url, headers={"User-Agent": "Mozilla/5.0"})
    if r.status_code != 200:
        print(f"❌ Cannot scrape, status code: {r.status_code}")
        return

    print("✅ First page is available for scraping")

    soup = BeautifulSoup(r.text, "lxml")
    base_url = "{uri.scheme}://{uri.netloc}".format(uri=requests.utils.urlparse(url))

    page_links = [url]
    pagination_links = soup.find_all("a", href=True)
    for link in pagination_links:
        href = link["href"]
        if "page" in href.lower() or re.search(r"[?&]p(=|age=)\d+", href) or re.search(r"/\d+$", href):
            full_url = urljoin(base_url, href)
            if full_url not in page_links:
                page_links.append(full_url)

    page_links = sorted(set(page_links))
    print(f"🔗 Found {len(page_links)} pages to scrape")

    all_products = []
    scrape_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    for page_url in page_links:
        print(f"📄 Scraping: {page_url}")
        r = requests.get(page_url, headers={"User-Agent": "Mozilla/5.0"})
        if r.status_code != 200:
            print(f"⚠️ Skipping {page_url}, status {r.status_code}")
            continue

        soup = BeautifulSoup(r.text, "html.parser")

        containers = soup.find_all(
            lambda tag: tag.has_attr("class") and any(
                "product" in c.lower() or "card" in c.lower() for c in tag.get("class", []))
        )

        for container in containers:
            product_info = {
                "Product Name": "NA",
                # "Product Price": "NA",   # ❌ Commented out to remove from CSV
                "Regular Price": "NA",
                "Discounted Price": "NA",
                "Product URL": "NA",
                "Product Image": "NA",
                "Star Rating": "NA",
                "Availability": "NA",
                "Scraped At": scrape_time
            }

            name_tag = container.find(
                ["h2", "h3", "span", "p", "a"],
                class_=lambda c: c and "title" in c.lower()
            )

            if name_tag:
                product_name = name_tag.get_text(strip=True)
                if not product_name:
                    for attr in ["title", "aria-label", "data-product-title", "alt", "swan-standard-tile-name", "wjcEIp"]:
                        if name_tag.has_attr(attr):
                            product_name = name_tag[attr].strip()
                            break
                if product_name:
                    product_info["Product Name"] = product_name

            # ❌ Commented out Product Price section
            # price_tag = container.find(
            #     ["span", "div"],
            #     class_=lambda c: c and any(x in c.lower() for x in [
            #         "price", "money", "amount", "cost",
            #         "il-mb-[0.125rem] il-text-xl il-font-bold il-flex il-items-start",
            #         "sale-price", "swan-list-price", "Nx9bqj"
            #     ])
            # )
            # if price_tag:
            #     product_info["Product Price"] = price_tag.get_text(strip=True)

            regular_price, discounted_price = extract_prices(container)
            product_info["Regular Price"] = regular_price
            product_info["Discounted Price"] = discounted_price

            link_tag = container.find("a", href=True)
            if link_tag:
                product_info["Product URL"] = urljoin(page_url, link_tag["href"])

            img_tag = container.find("img")
            if img_tag:
                product_info["Product Image"] = img_tag.get("src") or img_tag.get("data-src", "")

            rating_tag = container.find(
                ["span", "div"],
                class_=lambda c: c and ("star" in c.lower() or "review" in c.lower())
            )
            if rating_tag:
                rating_value = rating_tag.get_text(strip=True)
                if rating_value:
                    product_info["Star Rating"] = rating_value

            avail_tag = container.find(
                ["span", "div"],
                class_=lambda c: c and ("stock" in c.lower() or "availability" in c.lower())
            )
            if avail_tag:
                product_info["Availability"] = avail_tag.get_text(strip=True)

            if product_info["Product Name"] != "NA":
                all_products.append(product_info)

    df = pd.DataFrame(all_products)
    df.drop_duplicates(subset=["Product URL", "Product Name"], inplace=True)

    if not df.empty:
        parsed_url = requests.utils.urlparse(url)
        domain = parsed_url.netloc.replace("www.", "").replace(".", "_")

        file_timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"clean_products_{domain}_{file_timestamp}.csv"

        df.to_csv(filename, index=False, encoding="utf-8-sig")
        print(f"✅ Clean product catalog saved to {filename}")
    else:
        print("⚠️ No products detected in the pages.")


# Run
scrape_ecommerce()
