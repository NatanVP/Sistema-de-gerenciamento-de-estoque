from flask import Flask, render_template, request, redirect, url_for, flash, session
import mysql.connector
from config import Config

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


if __name__ == "__main__":
    app.run(debug=True)