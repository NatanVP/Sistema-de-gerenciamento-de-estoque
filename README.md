Sistema de Gerenciamento de Estoque

O projeto consiste em um sistema web desenvolvido em Python (Flask) com integração ao MySQL, voltado para o controle de estoque. A aplicação permite o cadastro, edição, exclusão e visualização de produtos, oferecendo uma interface simples e objetiva para gestão de inventário.

Tecnologias utilizadas:

-Backend: Python 3.x, Flask

-Frontend: HTML5, CSS3, JavaScript

-Banco de Dados: MySQL

-Template Engine: Jinja2

-Conexão com o banco: mysql-connector-python

Funcionalidades:

-Login e cadastro de usuários

-Permissões para editar e excluir produtos

-Cadastro de novos produtos

-Edição de produtos existentes

-Exclusão de produtos com confirmação

-Validação de formulários

-Exibição de mensagens de feedback

-Interface responsiva

-Estrutura do Banco de Dados

Para utilizar o sistema, é necessário criar o banco de dados no MySQL:
```
-- Criar banco de dados
CREATE DATABASE estoque;

-- Selecionar banco de dados
USE estoque;

-- Criar tabela de produtos
CREATE TABLE produtos (
    id INT AUTO_INCREMENT PRIMARY KEY,
    nome VARCHAR(100) NOT NULL,
    categoria VARCHAR(50),
    quantidade INT NOT NULL
);

-- Criar tabela de usuários
CREATE TABLE usuarios (
    id INT AUTO_INCREMENT PRIMARY KEY,
    usuario VARCHAR(100) NOT NULL UNIQUE,
    email VARCHAR(100) NOT NULL UNIQUE,
    senha VARCHAR(255) NOT NULL,
    perfil ENUM('admin', 'funcionario') NOT NULL DEFAULT 'funcionario'
);

```

Configuração de Conexão (config.py)

Crie o arquivo config.py na raiz do projeto e insira as credenciais do seu banco MySQL:
```python
db_config = {
    'host': 'localhost',      # Endereço do servidor MySQL
    'user': 'seu_usuario',    # Usuário do MySQL
    'password': 'sua_senha',  # Senha do MySQL
    'database': 'estoque'     # Nome do banco de dados criado
}
```

