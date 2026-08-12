import os
import json
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from datetime import datetime

from openai import OpenAI

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


def summarize_documents(documents):
    if not documents:
        return "Hôm nay không phát hiện văn bản pháp luật mới."

    api_key = os.environ.get("OPENAI_API_KEY")

    if not api_key:
        raise RuntimeError("Thiếu OPENAI_API_KEY")

    model = os.environ.get(
        "OPENAI_MODEL",
        "gpt-4o-mini",
    )

    client = OpenAI(api_key=api_key)

    items = []

    for i, doc in enumerate(documents, 1):
        items.append(
            f"""
{i}. {doc.get('title', '')}
Số hiệu: {doc.get('so_hieu', '')}
Loại văn bản: {doc.get('loai', '')}
Ngày ban hành: {doc.get('ngay_ban_hanh', '')}
Ngày hiệu lực: {doc.get('ngay_hieu_luc', '')}
Cơ quan: {doc.get('co_quan', '')}
Link: {doc.get('url', '')}
"""
        )

    prompt = f"""
Bạn là trợ lý pháp lý chuyên tổng hợp văn bản pháp luật Việt Nam.

Hãy tổng hợp các văn bản dưới đây thành bản tin pháp luật
ngắn gọn, dễ đọc cho người làm doanh nghiệp/kế toán/thuế.

Yêu cầu:

1. Chỉ sử dụng thông tin được cung cấp.
2. Không tự suy đoán nội dung pháp luật.
3. Với mỗi văn bản, trình bày:
   - Tên văn bản
   - Số hiệu
   - Ngày ban hành
   - Ngày hiệu lực
   - Cơ quan ban hành
   - Nội dung chính
   - Đối tượng cần lưu ý
   - Việc doanh nghiệp nên làm
   - Link văn bản
4. Nếu chưa đủ thông tin để kết luận thì ghi rõ "Chưa đủ dữ liệu".
5. Ưu tiên những điểm có ảnh hưởng đến doanh nghiệp, thuế,
   kế toán, lao động, bảo hiểm và đầu tư.
6. Viết bằng tiếng Việt.
7. Không đưa ra tư vấn pháp lý chắc chắn nếu dữ liệu chưa đủ.

Danh sách văn bản:

{''.join(items)}
"""

    response = client.responses.create(
        model=model,
        input=prompt,
    )

    return response.output_text


def send_email(subject, body):
    host = os.environ.get("SMTP_HOST")
    port = int(
        os.environ.get(
            "SMTP_PORT",
            "587",
        )
    )
    user = os.environ.get("SMTP_USER")
    password = os.environ.get("SMTP_PASSWORD")
    mail_to = os.environ.get("MAIL_TO")

    if not all(
        [
            host,
            user,
            password,
            mail_to,
        ]
    ):
        raise RuntimeError(
            "Thiếu cấu hình email SMTP"
        )

    message = MIMEMultipart()

    message["From"] = user
    message["To"] = mail_to
    message["Subject"] = subject

    message.attach(
        MIMEText(
            body,
            "plain",
            "utf-8",
        )
    )

    with smtplib.SMTP(
        host,
        port,
        timeout=30,
    ) as server:

        server.starttls()

        server.login(
            user,
            password,
        )

        server.sendmail(
            user,
            mail_to,
            message.as_string(),
        )


def main():
    print(
        "Bắt đầu tổng hợp văn bản pháp luật..."
    )

    state = load_state()

    documents = get_new_documents(
        days=2,
        max_items=30,
    )

    print(
        f"Tìm thấy {len(documents)} văn bản."
    )

    new_documents = []

    for document in documents:
        url = document.get("url")

        if not url:
            continue

        if url not in state:
            new_documents.append(document)

    print(
        f"Có {len(new_documents)} văn bản mới."
    )

    if not new_documents:
        print(
            "Không có văn bản mới, không gửi email."
        )
        return

    report = summarize_documents(
        new_documents
    )

    today = datetime.now().strftime(
        "%d/%m/%Y"
    )

    subject = (
        f"[Pháp luật Daily] "
        f"Văn bản mới ngày {today}"
    )

    send_email(
        subject,
        report,
    )

    for document in new_documents:
        url = document.get("url")

        if url and url not in state:
            state.append(url)

    save_state(state)

    print(
        "Đã gửi bản tin thành công."
    )


if __name__ == "__main__":
    main()
