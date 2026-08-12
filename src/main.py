import os
import json
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from datetime import datetime

from crawler import get_new_documents


STATE_FILE = "state.json"


def load_state():
    if not os.path.exists(STATE_FILE):
        return []

    try:
        with open(STATE_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return []


def save_state(state):
    with open(STATE_FILE, "w", encoding="utf-8") as f:
        json.dump(state, f, ensure_ascii=False, indent=2)


def build_report(documents):
    today = datetime.now().strftime("%d/%m/%Y")

    if not documents:
        return (
            f"BẢN TIN VĂN BẢN PHÁP LUẬT - {today}\n\n"
            "Không phát hiện văn bản mới trong khoảng thời gian kiểm tra."
        )

    lines = [
        f"BẢN TIN VĂN BẢN PHÁP LUẬT - {today}",
        "",
        f"Phát hiện {len(documents)} văn bản mới trên Thư Viện Pháp Luật.",
        "",
    ]

    for i, doc in enumerate(documents, 1):
        lines.extend([
            f"{i}. {doc.get('title', 'Không có tiêu đề')}",
            f"   Số hiệu: {doc.get('so_hieu') or 'Chưa xác định'}",
            f"   Loại văn bản: {doc.get('loai') or 'Chưa xác định'}",
            f"   Cơ quan ban hành: {doc.get('co_quan') or 'Chưa xác định'}",
            f"   Ngày ban hành: {doc.get('ngay_ban_hanh') or 'Chưa xác định'}",
            f"   Ngày hiệu lực: {doc.get('ngay_hieu_luc') or 'Chưa xác định'}",
            f"   Link: {doc.get('url', '')}",
            "",
        ])

    lines.append(
        "Lưu ý: Đây là bản tin tự động. "
        "Cần mở văn bản gốc để kiểm tra nội dung và hiệu lực trước khi áp dụng."
    )

    return "\n".join(lines)


def send_email(subject, body):
    host = os.environ.get("SMTP_HOST")
    port = int(os.environ.get("SMTP_PORT", "587"))
    user = os.environ.get("SMTP_USER")
    password = os.environ.get("SMTP_PASSWORD")
    mail_to = os.environ.get("MAIL_TO")

    if not all([host, user, password, mail_to]):
        raise RuntimeError("Thiếu cấu hình email SMTP")

    message = MIMEMultipart()
    message["From"] = user
    message["To"] = mail_to
    message["Subject"] = subject

    message.attach(
        MIMEText(body, "plain", "utf-8")
    )

    with smtplib.SMTP(host, port, timeout=30) as server:
        server.starttls()
        server.login(user, password)
        server.sendmail(
            user,
            mail_to,
            message.as_string()
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
        print("Không có văn bản mới, không gửi email.")
        return

    report = build_report(new_documents)

    today = datetime.now().strftime("%d/%m/%Y")
    subject = f"[Pháp luật Daily] Văn bản mới ngày {today}"

    send_email(subject, report)

    for document in new_documents:
        url = document.get("url")

        if url and url not in state:
            state.append(url)

    save_state(state)

    print("Đã gửi bản tin thành công.")


if __name__ == "__main__":
    main()
