import smtplib
from email.message import EmailMessage

# 建立 Email 物件
msg = EmailMessage()
msg["Subject"] = "測試信件"
msg["From"] = "你的Gmail帳號@gmail.com"
msg["To"] = "11231544@gafe.cksh.tp.edu.tw"
"11231073@gafe.cksh.tp.edu.tw"
msg.set_content("嗨！這是一封從 Python 寄出的測試信件～")

# 寄送 email（使用 Gmail SMTP 伺服器）
with smtplib.SMTP_SSL("smtp.gmail.com", 465) as smtp:
    smtp.login("你的Gmail帳號@gmail.com", "應用程式密碼")
    smtp.send_message(msg)