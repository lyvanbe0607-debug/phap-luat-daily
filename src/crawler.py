import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin
from datetime import datetime, timedelta
import re
import time


BASE_URL = "https://thuvienphapluat.vn"

# Thử phiên bản mobile trước vì GitHub Actions thường bị 403
URLS = [
    "https://m.thuvienphapluat.vn/van-ban-moi",
    "https://thuvienphapluat.vn/van-ban-moi",
]

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Linux; Android 13; Pixel 7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/131.0.0.0 Mobile Safari/537.36"
    ),
    "Accept": (
        "text/html,application/xhtml+xml,application/xml;"
        "q=0.9,image/avif,image/webp,*/*;q=0.8"
    ),
    "Accept-Language": "vi-VN,vi;q=0.9,en-US;q=0.8,en;q=0.7",
    "Referer": "https://www.google.com/",
    "Connection": "keep-alive",
}


def get_page():
    """
    Thử lấy trang Văn bản mới.
    Ưu tiên phiên bản mobile, nếu thất bại thì thử desktop.
    """

    session = requests.Session()
    session.headers.update(HEADERS)

    last_error = None

    for url in URLS:
        try:
            print(f"Đang truy cập: {url}")

            response = session.get(
                url,
                timeout=30,
                allow_redirects=True,
            )

            print(
                f"HTTP {response.status_code}: "
                f"{response.url}"
            )

            if response.status_code == 200:
                return response.text

            last_error = (
                f"HTTP {response.status_code} "
                f"tại {url}"
            )

        except requests.RequestException as exc:
            last_error = str(exc)

        time.sleep(2)

    raise RuntimeError(
        "Không thể truy cập Thư Viện Pháp Luật. "
        f"Lỗi cuối cùng: {last_error}"
    )


def get_new_documents(days=2, max_items=30):
    """
    Lấy các văn bản pháp luật mới trong khoảng days ngày gần nhất.
    """

    html = get_page()

    soup = BeautifulSoup(html, "html.parser")

    documents = []
    seen = set()

    today = datetime.now().date()
    from_date = today - timedelta(days=days)

    # Thử nhiều loại thẻ HTML vì giao diện mobile
    # và desktop có thể khác nhau.
    headings = soup.find_all(
        ["h1", "h2", "h3", "h4"]
    )

    for heading in headings:

        link = heading.find("a", href=True)

        if not link:
            continue

        title = link.get_text(
            " ",
            strip=True
        )

        if not title:
            continue

        href = link.get("href", "").strip()

        if not href:
            continue

        # Chỉ lấy liên kết văn bản pháp luật
        if "/van-ban/" not in href:
            continue

        url = urljoin(BASE_URL, href)

        if url in seen:
            continue

        seen.add(url)

        # Lấy nội dung khu vực xung quanh tiêu đề
        text = ""

        container = heading.parent

        if container:
            text = container.get_text(
                " ",
                strip=True
            )

        if len(text) < 50 and container:
            if container.parent:
                text = container.parent.get_text(
                    " ",
                    strip=True
                )

        # Tìm ngày ban hành
        match = re.search(
            r"Ban hành[:\s]*(\d{1,2}/\d{1,2}/\d{4})",
            text,
            re.IGNORECASE
        )

        ngay_ban_hanh = ""

        if match:
            ngay_ban_hanh = match.group(1)

        # Lọc theo ngày
        if ngay_ban_hanh:
            try:
                document_date = datetime.strptime(
                    ngay_ban_hanh,
                    "%d/%m/%Y"
                ).date()

                if document_date < from_date:
                    continue

            except ValueError:
                pass

        # Xác định loại văn bản
        loai = ""

        document_types = [
            "Luật",
            "Nghị định",
            "Nghị quyết",
            "Quyết định",
            "Thông tư",
            "Thông báo",
            "Công điện",
            "Chỉ thị",
            "Kế hoạch",
            "Pháp lệnh",
            "Công văn",
            "Văn bản hợp nhất",
            "Hướng dẫn",
        ]

        for document_type in document_types:
            if title.startswith(document_type):
                loai = document_type
                break

        documents.append(
            {
                "title": title,
                "url": url,
                "so_hieu": "",
                "loai": loai,
                "ngay_ban_hanh": ngay_ban_hanh,
                "ngay_hieu_luc": "",
                "co_quan": "",
            }
        )

        if len(documents) >= max_items:
            break

    return documents


if __name__ == "__main__":

    print(
        "=============================================="
    )

    print(
        "ĐANG LẤY VĂN BẢN MỚI TỪ "
        "THƯ VIỆN PHÁP LUẬT"
    )

    print(
        "=============================================="
    )

    try:

        documents = get_new_documents(
            days=2,
            max_items=30,
        )

        print(
            f"Tìm thấy {len(documents)} văn bản."
        )

        for i, doc in enumerate(documents, 1):

            print(
                "=" * 70
            )

            print(
                f"{i}. {doc['title']}"
            )

            print(
                f"Loại: "
                f"{doc['loai'] or 'Chưa xác định'}"
            )

            print(
                "Ngày ban hành: "
                f"{doc['ngay_ban_hanh'] or 'Chưa xác định'}"
            )

            print(
                f"Link: {doc['url']}"
            )

    except Exception as exc:

        print(
            "LỖI CRAWLER:"
        )

        print(
            str(exc)
        )

        raise
