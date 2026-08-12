import os
import json
import requests
from datetime import datetime

from crawler import get_new_documents


STATE_FILE = "state.json"
TELEGRAM_API = "https://api.telegram.org"


def load_state():
    if not os.path.exists(STATE_FILE):
        return []

    try:
        with open(STATE_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)

        # Định dạng mới: danh sách URL đã gửi
        if isinstance(data, list):
            return data

        # Tương thích với state.json cũ
        if isinstance(data, dict):
            urls = []

            for value in data.values():
                if isinstance(value, list):
                    for item in value:
                        if isinstance(item, str):
                            urls.append(item)
                        elif isinstance(item, dict):
                            url = item.get("url")
                            if url:
                                urls.append(url)

            return urls

        return []

    except Exception as exc:
        print(f"Không đọc được state.json: {exc}")
        return []


def save_state(state):
    with open(STATE_FILE, "w", encoding="utf-8") as f:
        json.dump(state, f, ensure_ascii=False, indent=2)


def build_report(documents):
    today = datetime.now().strftime("%d/%m/%Y")

    lines = [
        f"📚 BẢN TIN VĂN BẢN PHÁP LUẬT - {today}",
        "",
        f"Phát hiện {len(documents)} văn bản mới trên Thư Viện Pháp Luật.",
        "",
    ]

    for i, doc in enumerate(documents, 1):
        lines.extend([
            f"{i}. {doc.get('title', 'Không có tiêu đề')}",
            f"Số hiệu: {doc.get('so_hieu') or 'Chưa xác định'}",
            f"Loại văn bản: {doc.get('loai') or 'Chưa xác định'}",
            f"Cơ quan ban hành: {doc.get('co_quan') or 'Chưa xác định'}",
            f"Ngày ban hành: {doc.get('ngay_ban_hanh') or 'Chưa xác định'}",
            f"Ngày hiệu lực: {doc.get('ngay_hieu_luc') or 'Chưa xác định'}",
            f"🔗 {doc.get('url', '')}",
            "",
        ])

    lines.append(
        "ℹ️ Bản tin được tạo tự động. Vui lòng mở văn bản gốc để kiểm tra "
        "nội dung và hiệu lực trước khi áp dụng."
    )

    return "\n".join(lines)


def send_telegram(text):
    token = os.environ.get("TELEGRAM_BOT_TOKEN")
    chat_id = os.environ.get("TELEGRAM_CHAT_ID")

    if not token or not chat_id:
        raise RuntimeError(
            "Thiếu TELEGRAM_BOT_TOKEN hoặc TELEGRAM_CHAT_ID"
        )

    url = f"{TELEGRAM_API}/bot{token}/sendMessage"

    # Telegram giới hạn mỗi tin nhắn khoảng 4096 ký tự.
    chunks = []

    while len(text) > 4000:
        cut = text.rfind("\n\n", 0, 4000)

        if cut < 1000:
            cut = text.rfind("\n", 0, 4000)

        if cut < 1000:
            cut = 4000

        chunks.append(text[:cut])
        text = text[cut:].lstrip()

    chunks.append(text)

    for chunk in chunks:
        response = requests.post(
            url,
            json={
                "chat_id": chat_id,
                "text": chunk,
                "disable_web_page_preview": True,
            },
            timeout=30,
        )

        response.raise_for_status()

        data = response.json()

        if not data.get("ok"):
            raise RuntimeError(
                f"Telegram API lỗi: {data}"
            )


def main():
    print("Bắt đầu tổng hợp văn bản pháp luật...")

    state = load_state()

    documents = get_new_documents(
        days=2,
        max_items=30,
    )

    print(f"Tìm thấy {len(documents)} văn bản.")

    new_documents = []

    for document in documents:
        url = document.get("url")

        if url and url not in state:
            new_documents.append(document)

    print(f"Có {len(new_documents)} văn bản mới.")

    if not new_documents:
        print(
            "Không có văn bản mới, không gửi Telegram."
        )
        return

    report = build_report(new_documents)

    send_telegram(report)

    for document in new_documents:
        url = document.get("url")

        if url and url not in state:
            state.append(url)

    save_state(state)

    print(
        "Đã gửi bản tin Telegram thành công."
    )


if __name__ == "__main__":
    main()
