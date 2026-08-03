import json
import re
import urllib.request
from pathlib import Path

DATA_DIR = Path("data/k4_ecommerce")
DATA_DIR.mkdir(parents=True, exist_ok=True)

URLS = [
    {
        "doc_id": "k4-returns-policy",
        "title": "Chính sách trả hàng và hoàn tiền Shopee",
        "url": "https://help.shopee.vn/portal/article/77251",
        "customer_role": "buyer",
        "category": "returns",
        "filename": "returns-policy.md",
    },
    {
        "doc_id": "k4-seller-listing",
        "title": "Quy định về đăng bán sản phẩm và hàng cấm",
        "url": "https://help.shopee.vn/portal/article/77246",
        "customer_role": "seller",
        "category": "listing",
        "filename": "seller-listing.md",
    },
    {
        "doc_id": "k4-shipping-policy",
        "title": "Chính sách vận chuyển và giao nhận Shopee",
        "url": "https://help.shopee.vn/portal/article/77250",
        "customer_role": "buyer",
        "category": "shipping",
        "filename": "shipping-policy.md",
    },
    {
        "doc_id": "k4-privacy-policy",
        "title": "Chính sách bảo mật thông tin cá nhân",
        "url": "https://help.shopee.vn/portal/article/77244",
        "customer_role": "both",
        "category": "privacy",
        "filename": "privacy-policy.md",
    },
    {
        "doc_id": "k4-payment-policy",
        "title": "Điều khoản thanh toán và ví ShopeePay / SPayLater",
        "url": "https://help.shopee.vn/portal/article/118121",
        "customer_role": "both",
        "category": "payment",
        "filename": "payment-policy.md",
    },
]

def clean_html(html_content: str) -> str:
    text = re.sub(r'<style.*?>.*?</style>', '', html_content, flags=re.DOTALL | re.IGNORECASE)
    text = re.sub(r'<script.*?>.*?</script>', '', html_content, flags=re.DOTALL | re.IGNORECASE)
    text = re.sub(r'</p>|<br\s*/?>|</div>|</li>|</h1>|</h2>|</h3>|</h4>', '\n\n', text, flags=re.IGNORECASE)
    text = re.sub(r'<[^>]+>', ' ', text)
    text = re.sub(r'&nbsp;', ' ', text)
    text = re.sub(r'&amp;', '&', text)
    text = re.sub(r'&quot;', '"', text)
    text = re.sub(r'&lt;', '<', text)
    text = re.sub(r'&gt;', '>', text)
    text = re.sub(r'[ \t]+', ' ', text)
    text = re.sub(r'\n[ \t]+', '\n', text)
    text = re.sub(r'\n{3,}', '\n\n', text)
    return text.strip()

def fetch_page(item: dict) -> tuple[str, str]:
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
    req = urllib.request.Request(item["url"], headers=headers)
    try:
        with urllib.request.urlopen(req, timeout=15) as response:
            html = response.read().decode("utf-8", errors="ignore")
            match = re.search(r'FORGE_SSR_DATA_MAP"\s*:\s*(\{.*?\})\s*\}', html)
            if match:
                try:
                    data_map = json.loads(match.group(1))
                    for k, v in data_map.items():
                        if isinstance(v, dict) and "content" in v:
                            title = v.get("title", item["title"])
                            content_raw = v.get("content", "")
                            cleaned = clean_html(content_raw)
                            if len(cleaned) > 100:
                                return title, cleaned
                except Exception as e:
                    print(f"Error parsing JSON map for {item['doc_id']}: {e}")
            
            cleaned = clean_html(html)
            return item["title"], cleaned
    except Exception as err:
        print(f"Fetch failed for {item['url']}: {err}")
        return item["title"], ""

def main():
    sources_rows = ["doc_id,file_path,title,source_url,retrieved_at,document_version,license_or_permission"]
    
    for item in URLS:
        print(f"Fetching {item['doc_id']} from {item['url']}...")
        title, body = fetch_page(item)
        if not body or len(body) < 100:
            print(f"Warning: Empty or small body for {item['doc_id']}")
        
        md_content = f"""---
doc_id: {item['doc_id']}
title: "{title}"
customer_role: {item['customer_role']}
category: {item['category']}
language: vi
source_url: {item['url']}
retrieved_at: 2026-08-03
document_version: "2026.1"
---

# {title}

{body}
"""
        file_path = DATA_DIR / item["filename"]
        file_path.write_text(md_content, encoding="utf-8")
        sources_rows.append(
            f"{item['doc_id']},data/k4_ecommerce/{item['filename']},{title},{item['url']},2026-08-03,2026.1,public-page"
        )
    
    (DATA_DIR / "sources.csv").write_text("\n".join(sources_rows) + "\n", encoding="utf-8")
    print(f"Successfully generated {len(URLS)} Markdown files and sources.csv in {DATA_DIR}")

if __name__ == "__main__":
    main()
