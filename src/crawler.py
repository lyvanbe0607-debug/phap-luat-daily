import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin
from datetime import datetime, timedelta
import re


BASE_URL = "https://thuvienphapluat.vn"
SEARCH_URL = f"{BASE_URL}/page/tim-van-ban.aspx"


def get_new_documents(days=1, max_items=30):
    """
    Lấy các văn bản pháp luật mới từ Thư Viện Pháp Luật.
    Mặc định lấy dữ liệu trong 1 ngày gần nhất.
    """

    today = datetime.now()
    from_date = today - timedelta(days=days)

    params = {
        "keyword": "",
    }

    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/130.0 Safari/537.36"
        )
    }

    response = requests.get(
        SEARCH_URL,
        params=params,
        headers=headers,
        timeout=30,
    )

    response.raise_for_status()

    soup = BeautifulSoup(response.text, "html.parser")

    documents = []

    # Tìm các liên kết đến trang văn bản
    links = soup.find_all("a", href=True)

    seen = set()

    for link in links:
        href = link.get("href", "").strip()

        if "/van-ban/" not in href:
            continue

        title = link.get_text(" ", strip=True)

        if not title or len(title) < 10:
            continue

        url = urljoin(BASE_URL, href)

        if url in seen:
            continue

        seen.add(url)

        # Lấy trang chi tiết
        try:
            detail = requests.get(
                url,
                headers=headers,
                timeout=30,
            )

            if detail.status_code != 200:
                continue

            detail_soup = BeautifulSoup(
                detail.text,
                "html.parser",
            )

            text = detail_soup.get_text(
                "\n",
                strip=True,
            )

            so_hieu = extract_field(
                text,
                ["Số hiệu:"],
            )

            loai = extract_field(
                text,
                ["Loại văn bản:"],
            )

            ngay_ban_hanh = extract_field(
                text,
                ["Ngày ban hành:"],
            )

            ngay_hieu_luc = extract_field(
                text,
                ["Ngày hiệu lực:"],
            )

            co_quan = extract_field(
                text,
                ["Nơi ban hành:"],
            )

            documents.append(
                {
                    "title": title,
                    "url": url,
                    "so_hieu": so_hieu,
                    "loai": loai,
                    "ngay_ban_hanh": ngay_ban_hanh,
                    "ngay_hieu_luc": ngay_hieu_luc,
                    "co_quan": co_quan,
                }
            )

            if len(documents) >= max_items:
                break

        except requests.RequestException:
            continue

    return documents


def extract_field(text, labels):
    """
    Tìm giá trị của một trường trong nội dung trang.
    """

    for label in labels:
        pattern = rf"{re.escape(label)}\s*([^\n]+)"

        match = re.search(
            pattern,
            text,
            flags=re.IGNORECASE,
        )

        if match:
            return match.group(1).strip()

    return ""


if __name__ == "__main__":
    documents = get_new_documents()

    print(
        f"Tìm thấy {len(documents)} văn bản."
    )

    for doc in documents:
        print("=" * 70)
        print("Tên:", doc["title"])
        print("Số hiệu:", doc["so_hieu"])
        print("Loại:", doc["loai"])
        print("Ngày ban hành:", doc["ngay_ban_hanh"])
        print("Ngày hiệu lực:", doc["ngay_hieu_luc"])
        print("Cơ quan:", doc["co_quan"])
        print("Link:", doc["url"])
