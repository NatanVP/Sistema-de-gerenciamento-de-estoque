from flask import Flask, render_template, request, redirect, url_for, flash, session
import mysql.connector
from config import Config
from apscheduler.schedulers.background import BackgroundScheduler
import relatorios as relatorio
import relatorios
from email_utils import enviar_relatorio

import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

def enviar_email(destinatario, assunto, mensagem):
    try:
        print("\n" + "="*60)
        print("=== INICIANDO ENVIO DE E-MAIL ===")
        print("="*60)
        print(f"Destinatario: {destinatario}")
        print(f"Assunto: {assunto}")
        print(f"Host: {app.config.get('MAIL_HOST')}")
        print(f"Porta: {app.config.get('MAIL_PORT')}")
        print(f"Usuario: {app.config.get('MAIL_USER')}")
        print(f"Senha configurada: {'Sim' if app.config.get('MAIL_PASSWORD') else 'NAO!'}")
        print(f"TLS: {app.config.get('MAIL_USE_TLS')}")
        print("="*60)
        
        msg = MIMEMultipart()
        msg["From"] = app.config["MAIL_USER"]
        msg["To"] = destinatario
        msg["Subject"] = assunto

        msg.attach(MIMEText(mensagem, "html"))

        print("Conectando ao servidor SMTP...")
        server = smtplib.SMTP(app.config["MAIL_HOST"], app.config["MAIL_PORT"])
        server.set_debuglevel(1)  # Ativa debug detalhado
        
        if app.config.get("MAIL_USE_TLS", True):
            print("Iniciando TLS...")
            server.starttls()

        print("Fazendo login...")
        server.login(app.config["MAIL_USER"], app.config["MAIL_PASSWORD"])
        
        print("Enviando mensagem...")
        server.send_message(msg)
        server.quit()
        
        print("="*60)
        print(">>> E-MAIL ENVIADO COM SUCESSO! <<<")
        print("="*60 + "\n")
        return True

    except smtplib.SMTPAuthenticationError as e:
        print("\n" + "="*60)
        print("ERRO DE AUTENTICACAO!")
        print("="*60)
        print("Possiveis causas:")
        print("1. Senha de app incorreta")
        print("2. Verificacao em 2 etapas nao ativada")
        print("3. E-mail incorreto")
        print(f"\nDetalhes: {e}")
        print("="*60 + "\n")
        return False
        
    except smtplib.SMTPException as e:
        print("\n" + "="*60)
        print("ERRO SMTP!")
        print("="*60)
        print(f"Detalhes: {e}")
        print("="*60 + "\n")
        return False
        
    except Exception as e:
        print("\n" + "="*60)
        print("ERRO DESCONHECIDO!")
        print("="*60)
        print(f"Tipo: {type(e).__name__}")
        print(f"Detalhes: {str(e)}")
        import traceback
        traceback.print_exc()
        print("="*60 + "\n")
        return False
    
def tarefa_relatorios():
    cursor = db.cursor(dictionary=True)
    cursor.execute("SELECT * FROM configuracoes_relatorios")
    configs = cursor.fetchall()
    cursor.close()

    for cfg in configs:
        arquivo = gerar_relatorio_resumo()
        enviar_relatorio(cfg["email"], arquivo)

scheduler = BackgroundScheduler()
scheduler.add_job(tarefa_relatorios, 'interval', hours=24)
scheduler.start()

# relatorios.py
import mysql.connector
from config import Config

def gerar_relatorio_resumo():
    """Gera um resumo do estoque em HTML"""
    try:
        db = mysql.connector.connect(
            host=Config.DB_HOST,
            port=Config.DB_PORT,
            user=Config.DB_USER,
            password=Config.DB_PASSWORD,
            database=Config.DB_NAME
        )
        
        cursor = db.cursor(dictionary=True)
        
        # Total de produtos
        cursor.execute("SELECT COUNT(*) as total FROM produtos")
        total_produtos = cursor.fetchone()['total']
        
        # Produtos com estoque baixo (exemplo: menos de 10 unidades)
        cursor.execute("SELECT nome, quantidade FROM produtos WHERE quantidade < 10 ORDER BY quantidade")
        produtos_criticos = cursor.fetchall()
        
        # Últimas movimentações
        cursor.execute("""
            SELECT m.tipo, p.nome, m.quantidade, m.data, m.usuario
            FROM movimentacoes m
            JOIN produtos p ON p.id = m.produto_id
            ORDER BY m.data DESC
            LIMIT 10
        """)
        ultimas_movimentacoes = cursor.fetchall()
        
        cursor.close()
        db.close()
        
        # Monta o HTML do relatório
        html = f"""
        <h3>Resumo do Estoque</h3>
        <p><strong>Total de Produtos:</strong> {total_produtos}</p>
        
        <h4>Produtos com Estoque Baixo:</h4>
        <table border="1" cellpadding="5" cellspacing="0">
            <tr>
                <th>Produto</th>
                <th>Quantidade</th>
            </tr>
        """
        
        for produto in produtos_criticos:
            html += f"""
            <tr>
                <td>{produto['nome']}</td>
                <td>{produto['quantidade']}</td>
            </tr>
            """
        
        html += """
        </table>
        
        <h4>Últimas Movimentações:</h4>
        <table border="1" cellpadding="5" cellspacing="0">
            <tr>
                <th>Tipo</th>
                <th>Produto</th>
                <th>Quantidade</th>
                <th>Data</th>
                <th>Usuário</th>
            </tr>
        """
        
        for mov in ultimas_movimentacoes:
            html += f"""
            <tr>
                <td>{mov['tipo']}</td>
                <td>{mov['nome']}</td>
                <td>{mov['quantidade']}</td>
                <td>{mov['data']}</td>
                <td>{mov['usuario']}</td>
            </tr>
            """
        
        html += "</table>"
        
        return html
        
    except Exception as e:
        print(f"Erro ao gerar relatório: {e}")
        return "<p>Erro ao gerar relatório.</p>"

app = Flask(__name__)
app.config.from_object(Config)

# tenta conectar ao MySQL
try:
    db = mysql.connector.connect(
        host=app.config["DB_HOST"],
        port=app.config.get("DB_PORT", 1902),
        user=app.config["DB_USER"],
        password=app.config["DB_PASSWORD"],
        database=app.config["DB_NAME"]
    )
    cursor = db.cursor()
    cursor.execute("SELECT NOW();")
    resultado = cursor.fetchone()
    print("Conectado ao MySQL com sucesso! Hora do servidor:", resultado[0])
except mysql.connector.Error as err:
    print("Erro ao conectar no MySQL:", err)

cursor = db.cursor(dictionary=True)

# Página inicial
@app.route("/")
def home():
    return render_template("login.html")

#login
@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        usuario = request.form["usuario"]
        senha = request.form["senha"]

        cursor = db.cursor(dictionary=True)
        cursor.execute("SELECT * FROM usuarios WHERE usuario = %s", (usuario,))  # <- Busca só pelo usuário
        user = cursor.fetchone()
        cursor.close()

        # Importa a função de verificação
        from werkzeug.security import check_password_hash

        # Verifica se o usuário existe E se a senha confere com o hash
        if user and check_password_hash(user["senha"], senha):
            session["usuario"] = user["usuario"]
            session["perfil"] = user["perfil"]
            flash("Login realizado com sucesso!", "success")
            return redirect(url_for("produtos"))
        else:
            return render_template("login.html", mensagem="Usuário ou senha incorretos.")

    return render_template("login.html")
#cadastro
@app.route("/cadastro", methods=["GET", "POST"])
def cadastro():
    if request.method == "POST":
        usuario = request.form["usuario"]
        email = request.form["email"]
        senha = request.form["senha"]
        perfil = request.form["perfil"]

        cursor = db.cursor(dictionary=True)

        # Verifica se o usuário já existe
        cursor.execute("SELECT * FROM usuarios WHERE usuario = %s", (usuario,))
        existente_usuario = cursor.fetchone()

        # Verifica se o e-mail já existe
        cursor.execute("SELECT * FROM usuarios WHERE email = %s", (email,))
        existente_email = cursor.fetchone()

        if existente_usuario:
            cursor.close()
            return render_template("cadastro.html", mensagem_usuario="Este nome de usuário já está em uso.")
        elif existente_email:
            cursor.close()
            return render_template("cadastro.html", mensagem_email="Este e-mail já está cadastrado.")
        else:
            from werkzeug.security import generate_password_hash
            senha_hash = generate_password_hash(senha)

            cursor.execute(
                "INSERT INTO usuarios (usuario, email, senha, perfil) VALUES (%s, %s, %s, %s)",
                (usuario, email, senha_hash, perfil)
            )
            db.commit()
            cursor.close()

            flash("Usuário cadastrado com sucesso!", "success")
            return redirect(url_for("login"))

    return render_template("cadastro.html")

# Listar produtos
@app.route("/produtos")
def produtos():
    cursor.execute("SELECT * FROM produtos")
    produtos = cursor.fetchall()
    return render_template("produtos.html", produtos=produtos)

# Cadastrar produto
@app.route("/add_produto", methods=["POST"])
def add_produto():
    nome = request.form["nome"]
    categoria = request.form["categoria"]
    quantidade = request.form["quantidade"]
    
    sql = "INSERT INTO produtos (nome, categoria, quantidade) VALUES (%s,%s,%s)"
    cursor.execute(sql, (nome, categoria, quantidade))
    db.commit()
    flash("Produto adicionado com sucesso!", "success")
    return redirect(url_for("produtos"))

# Excluir produto
@app.route("/excluir_produto/<int:id>", methods=["POST"])
def excluir_produto(id):
    if "perfil" not in session or session["perfil"] != "admin":
        flash("Você não tem permissão para excluir produtos.", "danger")
        return redirect(url_for("produtos"))
    
    cursor = db.cursor()
    cursor.execute("DELETE FROM produtos WHERE id = %s", (id,))
    db.commit()
    cursor.close()
    flash("Produto excluído com sucesso!", "success")
    return redirect("/produtos")


# Editar produto
@app.route("/editar_produto/<int:id>", methods=["GET", "POST"])
def editar_produto(id):
    if "perfil" not in session or session["perfil"] != "admin":
        flash("Você não tem permissão para editar produtos.", "danger")
        return redirect(url_for("produtos"))
    
    if request.method == "GET":
        cursor = db.cursor(dictionary=True)
        cursor.execute("SELECT * FROM produtos WHERE id = %s", (id,))
        produto = cursor.fetchone()
        cursor.close()
        return render_template("editar.html", produto=produto)

    nome = request.form["nome"]
    categoria = request.form["categoria"]
    quantidade = request.form["quantidade"]

    cursor = db.cursor()
    cursor.execute("""
        UPDATE produtos
        SET nome=%s, categoria=%s, quantidade=%s
        WHERE id=%s
    """, (nome, categoria, quantidade, id))
    db.commit()
    cursor.close()
    flash("Produto editado com sucesso!", "success")
    return redirect("/produtos")

@app.route("/logout")
def logout():
    session.pop("usuario", None)
    session.pop("perfil", None)
    flash("Logout realizado com sucesso!", "info")
    return redirect(url_for("login"))



# ====== GERENCIAR ESTOQUE ======
@app.route("/estoque")
def estoque():
    # mostra a lista de produtos e opção de ajuste manual (só admin)
    cursor = db.cursor(dictionary=True)
    cursor.execute("SELECT * FROM produtos")
    produtos = cursor.fetchall()
    cursor.close()
    return render_template("estoque.html", produtos=produtos)

# Ajuste manual (somente admin)
@app.route("/estoque/ajustar", methods=["POST"])
def ajustar_estoque():
    if "perfil" not in session or session["perfil"] != "admin":
        flash("Você não tem permissão para ajustar o estoque manualmente.", "danger")
        return redirect(url_for("estoque"))

    produto_id = request.form.get("produto_id")
    nova_qtd = request.form.get("nova_quantidade")

    try:
        nova_qtd = int(nova_qtd)
    except (ValueError, TypeError):
        flash("Quantidade inválida.", "danger")
        return redirect(url_for("estoque"))

    cursor = db.cursor()
    cursor.execute("UPDATE produtos SET quantidade = %s WHERE id = %s", (nova_qtd, produto_id))
    db.commit()
    cursor.close()
    flash("Estoque ajustado com sucesso.", "success")
    return redirect(url_for("estoque"))


# ====== MOVIMENTAÇÕES (ENTRADA / SAÍDA) ======
@app.route("/movimentacoes", methods=["GET"])
def movimentacoes():
    # lista produtos para formulário e exibe histórico (paginável no futuro)
    cursor = db.cursor(dictionary=True)
    cursor.execute("SELECT * FROM produtos")
    produtos = cursor.fetchall()

    cursor.execute("""
        SELECT m.id, m.produto_id, m.tipo, m.quantidade, m.data, m.usuario, p.nome
        FROM movimentacoes m
        LEFT JOIN produtos p ON p.id = m.produto_id
        ORDER BY m.data DESC
        LIMIT 200
    """)
    historico = cursor.fetchall()
    cursor.close()
    return render_template("movimentacoes.html", produtos=produtos, historico=historico)


# Registrar entrada
@app.route("/movimentacoes/entrada", methods=["POST"])
def movimentacao_entrada():
    produto_id = request.form.get("produto_id")
    quantidade = request.form.get("quantidade")

    try:
        quantidade = int(quantidade)
    except (ValueError, TypeError):
        flash("Quantidade inválida.", "danger")
        return redirect(url_for("movimentacoes"))

    if quantidade <= 0:
        flash("Quantidade deve ser maior que zero.", "danger")
        return redirect(url_for("movimentacoes"))

    usuario = session.get("usuario", "desconhecido")

    cursor = db.cursor()
    # atualiza produtos
    cursor.execute("UPDATE produtos SET quantidade = quantidade + %s WHERE id = %s", (quantidade, produto_id))
    # insere movimentação
    cursor.execute("INSERT INTO movimentacoes (produto_id, tipo, quantidade, usuario) VALUES (%s, %s, %s, %s)",
                   (produto_id, 'entrada', quantidade, usuario))
    db.commit()
    cursor.close()

    flash("Entrada registrada com sucesso.", "success")
    return redirect(url_for("movimentacoes"))


# Registrar saída
@app.route("/movimentacoes/saida", methods=["POST"])
def movimentacao_saida():
    produto_id = request.form.get("produto_id")
    quantidade = request.form.get("quantidade")

    try:
        quantidade = int(quantidade)
    except (ValueError, TypeError):
        flash("Quantidade inválida.", "danger")
        return redirect(url_for("movimentacoes"))

    if quantidade <= 0:
        flash("Quantidade deve ser maior que zero.", "danger")
        return redirect(url_for("movimentacoes"))

    usuario = session.get("usuario", "desconhecido")

    cursor = db.cursor(dictionary=True)
    # verifica estoque atual
    cursor.execute("SELECT quantidade FROM produtos WHERE id = %s", (produto_id,))
    row = cursor.fetchone()
    if not row:
        cursor.close()
        flash("Produto não encontrado.", "danger")
        return redirect(url_for("movimentacoes"))

    estoque_atual = int(row["quantidade"])
    if quantidade > estoque_atual:
        cursor.close()
        flash("Estoque insuficiente para essa saída.", "danger")
        return redirect(url_for("movimentacoes"))

    cursor = db.cursor()
    cursor.execute("UPDATE produtos SET quantidade = quantidade - %s WHERE id = %s", (quantidade, produto_id))
    cursor.execute("INSERT INTO movimentacoes (produto_id, tipo, quantidade, usuario) VALUES (%s, %s, %s, %s)",
                   (produto_id, 'saida', quantidade, usuario))
    db.commit()
    cursor.close()

    flash("Saída registrada com sucesso.", "success")
    return redirect(url_for("movimentacoes"))


@app.route("/configuracoes", methods=["GET"])
def configuracoes():
    if "perfil" not in session or session["perfil"] != "admin":
        flash("Você não tem permissão para acessar esta área.", "danger")
        return redirect(url_for("produtos"))

    cursor = db.cursor(dictionary=True)
    cursor.execute("SELECT * FROM configuracoes_relatorios")
    configuracoes = cursor.fetchall()
    cursor.close()

    return render_template("configuracoes.html", configuracoes=configuracoes)


@app.route("/configuracoes/salvar", methods=["POST"])
def salvar_configuracao():
    if "perfil" not in session or session["perfil"] != "admin":
        flash("Sem permissão.", "danger")
        return redirect(url_for("configuracoes"))

    email = request.form.get("email_relatorios")
    frequencia = request.form.get("frequencia", "diario")
    formato = request.form.get("formato", "pdf")

    if not email:
        flash("E-mail é obrigatório!", "danger")
        return redirect(url_for("configuracoes"))

    incluir_estoque = 1 if "estoque" in request.form else 0
    incluir_mov = 1 if "movimentacoes" in request.form else 0
    incluir_criticos = 1 if "criticos" in request.form else 0

    # Salva a configuração no banco
    cursor = db.cursor()
    cursor.execute("""
        INSERT INTO configuracoes_relatorios 
        (email, frequencia, formato, incluir_estoque, incluir_movimentacoes, incluir_produtos_criticos)
        VALUES (%s, %s, %s, %s, %s, %s)
    """, (email, frequencia, formato, incluir_estoque, incluir_mov, incluir_criticos))
    db.commit()
    cursor.close()

    # Gera e envia o relatório de teste
    try:
        # Passa as opções selecionadas para gerar o relatório
        conteudo_relatorio = relatorio.gerar_relatorio_resumo(
            incluir_estoque=bool(incluir_estoque),
            incluir_movimentacoes=bool(incluir_mov),
            incluir_criticos=bool(incluir_criticos)
        )
        
        opcoes_selecionadas = []
        if incluir_estoque:
            opcoes_selecionadas.append("Estoque")
        if incluir_mov:
            opcoes_selecionadas.append("Movimentações")
        if incluir_criticos:
            opcoes_selecionadas.append("Produtos Críticos")
        
        assunto = "Teste de Relatório - Sistema de Estoque"
        mensagem = f"""
        <html>
        <body style="font-family: Arial, sans-serif;">
            <h2 style="color: #333;">📊 Relatório de Teste - Sistema de Estoque</h2>
            <p>Este e-mail confirma que as configurações foram salvas com sucesso.</p>
            <div style="background-color: #f4f4f4; padding: 15px; border-radius: 5px; margin: 20px 0;">
                <p><strong>⚙️ Configurações:</strong></p>
                <ul>
                    <li><strong>E-mail:</strong> {email}</li>
                    <li><strong>Frequência:</strong> {frequencia}</li>
                    <li><strong>Formato:</strong> {formato}</li>
                    <li><strong>Incluído no relatório:</strong> {', '.join(opcoes_selecionadas) if opcoes_selecionadas else 'Nenhuma opção'}</li>
                </ul>
            </div>
            <hr style="border: 1px solid #ddd;">
            {conteudo_relatorio}
            <hr style="border: 1px solid #ddd; margin-top: 30px;">
            <p style="color: #666; font-size: 12px;">Este é um e-mail automático do Sistema de Gerenciamento de Estoque.</p>
        </body>
        </html>
        """
        
        enviado = enviar_email(email, assunto, mensagem)
        
        if enviado:
            flash("✅ Configuração adicionada e e-mail de teste enviado com sucesso!", "success")
        else:
            flash("⚠️ Configuração adicionada, mas houve erro ao enviar o e-mail de teste.", "warning")
            
    except Exception as e:
        print(f"Erro ao gerar/enviar relatório de teste: {e}")
        import traceback
        traceback.print_exc()
        flash("⚠️ Configuração adicionada, mas houve erro ao gerar o relatório de teste.", "warning")

    return redirect(url_for("configuracoes"))

@app.route("/configuracoes/excluir/<int:id>", methods=["POST"])
def excluir_configuracao(id):
    if "perfil" not in session or session["perfil"] != "admin":
        flash("Sem permissão.", "danger")
        return redirect(url_for("configuracoes"))

    cursor = db.cursor()
    cursor.execute("DELETE FROM configuracoes_relatorios WHERE id = %s", (id,))
    db.commit()
    cursor.close()

    flash("Configuração apagada.", "info")
    return redirect(url_for("configuracoes"))



if __name__ == "__main__":
    app.run(debug=True)