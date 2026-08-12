import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin
from datetime import datetime, timedelta
import re


BASE_URL = "https://thuvienphapluat.vn"
NEW_DOCS_URL = f"{BASE_URL}/van-ban-moi"

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/131.0 Safari/537.36"
    ),
    "Accept": (
        "text/html,application/xhtml+xml,application/xml;"
        "q=0.9,image/avif,image/webp,*/*;q=0.8"
    ),
    "Accept-Language": "vi-VN,vi;q=0.9,en;q=0.8",
}


def get_new_documents(days=2, max_items=30):
    """
    Lấy danh sách văn bản mới từ trang Văn bản mới
    của Thư Viện Pháp Luật.

    Không truy cập trang tìm kiếm cũ để tránh lỗi HTTP 403
    trên GitHub Actions.
    """

    response = requests.get(
        NEW_DOCS_URL,
        headers=HEADERS,
        timeout=30,
    )

    response.raise_for_status()

    soup = BeautifulSoup(response.text, "html.parser")

    documents = []
    seen = set()

    today = datetime.now().date()
    from_date = today - timedelta(days=days)

    # Các tiêu đề văn bản trên trang được đặt trong thẻ h2
    for heading in soup.find_all("h2"):

        link = heading.find("a", href=True)

        if not link:
            continue

        title = link.get_text(" ", strip=True)

        if not title:
            continue

        href = link.get("href", "").strip()

        if not href:
            continue

        # Chỉ lấy liên kết đến văn bản pháp luật
        if "/van-ban/" not in href:
            continue

        url = urljoin(BASE_URL, href)

        if url in seen:
            continue

        seen.add(url)

        # Tìm phần tử chứa thông tin ngày ban hành
        container = heading.parent

        text = ""

        if container:
            text = container.get_text(
                " ",
                strip=True
            )

        # Nếu parent chưa đủ thông tin thì thử parent cấp cao hơn
        if "Ban hành" not in text and container:
            grand_parent = container.parent

            if grand_parent:
                text = grand_parent.get_text(
                    " ",
                    strip=True
                )

        # Tìm ngày ban hành
        match = re.search(
            r"Ban hành:\s*(\d{2}/\d{2}/\d{4})",
            text
        )

        ngay_ban_hanh = ""

        if match:
            ngay_ban_hanh = match.group(1)

        # Nếu xác định được ngày ban hành thì lọc theo khoảng ngày
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

        # Cố gắng xác định loại văn bản từ tiêu đề
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
        "Đang lấy văn bản mới từ Thư Viện Pháp Luật..."
    )

    documents = get_new_documents(
        days=2,
        max_items=30,
    )

    print(
        f"Tìm thấy {len(documents)} văn bản."
    )

    for i, doc in enumerate(documents, 1):

        print("=" * 70)

        print(
            f"{i}. {doc['title']}"
        )

        print(
            f"Loại: {doc['loai'] or 'Chưa xác định'}"
        )

        print(
            f"Ngày ban hành: "
            f"{doc['ngay_ban_hanh'] or 'Chưa xác định'}"
        )

        print(
            f"Link: {doc['url']}"
        )
