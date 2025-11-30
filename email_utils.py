import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from config import Config

def enviar_relatorio(destinatario, arquivo_html):
    msg = MIMEMultipart()
    msg["From"] = Config.EMAIL_REMETENTE
    msg["To"] = destinatario
    msg["Subject"] = "Relatório de Estoque"

    with open(arquivo_html, "r", encoding="utf-8") as f:
        corpo_html = f.read()

    msg.attach(MIMEText(corpo_html, "html"))

    with smtplib.SMTP(Config.EMAIL_SERVIDOR, Config.EMAIL_PORTA) as servidor:
        servidor.starttls()
        servidor.login(Config.EMAIL_REMETENTE, Config.EMAIL_SENHA)
        servidor.sendmail(Config.EMAIL_REMETENTE, destinatario, msg.as_string())

    print(f"[OK] Relatório enviado para {destinatario}")
