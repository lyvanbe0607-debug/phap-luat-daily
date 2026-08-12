import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin
from datetime import datetime, timedelta
import re


BASE_URL = "https://vanban.chinhphu.vn"
LIST_URL = "https://vanban.chinhphu.vn/he-thong-van-ban?classid=1"

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 Chrome/131.0 Safari/537.36"
    ),
    "Accept-Language": "vi-VN,vi;q=0.9,en;q=0.8",
}


def get_new_documents(days=2, max_items=30):
    print(f"Đang truy cập: {LIST_URL}")

    response = requests.get(
        LIST_URL,
        headers=HEADERS,
        timeout=30,
    )

    print(f"HTTP {response.status_code}")

    response.raise_for_status()

    soup = BeautifulSoup(response.text, "html.parser")

    today = datetime.now().date()
    from_date = today - timedelta(days=days)

    documents = []
    seen = set()

    # Tìm các liên kết có số hiệu văn bản và ngày ban hành
    for link in soup.find_all("a", href=True):
        text = link.get_text(" ", strip=True)

        match = re.search(
            r"(.+?)\s+(\d{2}/\d{2}/\d{4})$",
            text
        )

        if not match:
            continue

        so_hieu = match.group(1).strip()
        ngay_ban_hanh = match.group(2)

        # Loại bỏ những link không giống số hiệu văn bản
        if "/" not in so_hieu:
            continue

        try:
            document_date = datetime.strptime(
                ngay_ban_hanh,
                "%d/%m/%Y"
            ).date()
        except ValueError:
            continue

        if document_date < from_date:
            continue

        url = urljoin(
            BASE_URL,
            link.get("href")
        )

        if url in seen:
            continue

        seen.add(url)

        # Tìm trích yếu gần liên kết hiện tại
        container = link.parent
        title = ""

        if container:
            container_text = container.get_text(
                " ",
                strip=True
            )

            # Bỏ số hiệu/ngày ở đầu để lấy phần trích yếu
            title = container_text.replace(
                text,
                "",
                1
            ).strip()

        if not title and container and container.parent:
            parent_text = container.parent.get_text(
                " ",
                strip=True
            )

            title = parent_text.replace(
                text,
                "",
                1
            ).strip()

        # Làm sạch ngày bị lặp
        title = re.sub(
            r"^\d{2}/\d{2}/\d{4}\s*",
            "",
            title
        )

        title = re.sub(
            r"\s*Tài liệu đính kèm.*$",
            "",
            title
        ).strip()

        loai = detect_document_type(so_hieu)

        documents.append({
            "title": title or so_hieu,
            "url": url,
            "so_hieu": so_hieu,
            "loai": loai,
            "ngay_ban_hanh": ngay_ban_hanh,
            "ngay_hieu_luc": "",
            "co_quan": "",
        })

        if len(documents) >= max_items:
            break

    print(
        f"Tìm thấy {len(documents)} văn bản "
        f"trong {days} ngày gần nhất."
    )

    return documents


def detect_document_type(so_hieu):
    value = so_hieu.upper()

    types = {
        "/NĐ-CP": "Nghị định",
        "/NQ-CP": "Nghị quyết",
        "/QĐ-TTG": "Quyết định",
        "/TT-": "Thông tư",
        "/QH": "Luật/Nghị quyết Quốc hội",
        "VBHN": "Văn bản hợp nhất",
        "/CT-": "Chỉ thị",
        "/CĐ-": "Công điện",
    }

    for marker, name in types.items():
        if marker in value:
            return name

    return "Văn bản pháp luật"


if __name__ == "__main__":
    docs = get_new_documents(
        days=2,
        max_items=30
    )

    for i, doc in enumerate(docs, 1):
        print("=" * 70)
        print(f"{i}. {doc['so_hieu']}")
        print(doc["title"])
        print(doc["ngay_ban_hanh"])
        print(doc["url"])
