# relatorios.py
import mysql.connector
from config import Config

def gerar_relatorio_resumo(incluir_estoque=False, incluir_movimentacoes=False, incluir_criticos=False):
    """
    Gera relatório customizado baseado nas opções escolhidas
    """
    try:
        db = mysql.connector.connect(
            host=Config.DB_HOST,
            port=Config.DB_PORT,
            user=Config.DB_USER,
            password=Config.DB_PASSWORD,
            database=Config.DB_NAME
        )
        
        cursor = db.cursor(dictionary=True)
        html = "<h3>Relatório do Sistema de Estoque</h3>"
        
        # ========== ESTOQUE ==========
        if incluir_estoque:
            cursor.execute("SELECT nome, categoria, quantidade FROM produtos ORDER BY nome")
            produtos = cursor.fetchall()
            
            html += """
            <h4>📦 Estoque Atual</h4>
            <table border="1" cellpadding="8" cellspacing="0" style="border-collapse: collapse; width: 100%; margin-bottom: 20px;">
                <thead>
                    <tr style="background-color: #4CAF50; color: white;">
                        <th>Produto</th>
                        <th>Categoria</th>
                        <th>Quantidade</th>
                    </tr>
                </thead>
                <tbody>
            """
            
            for p in produtos:
                html += f"""
                <tr>
                    <td>{p['nome']}</td>
                    <td>{p['categoria']}</td>
                    <td>{p['quantidade']}</td>
                </tr>
                """
            
            html += "</tbody></table>"
        
        # ========== MOVIMENTAÇÕES (SAÍDAS) ==========
        if incluir_movimentacoes:
            cursor.execute("""
                SELECT 
                    p.nome as produto,
                    m.quantidade,
                    m.data,
                    m.usuario
                FROM movimentacoes m
                JOIN produtos p ON p.id = m.produto_id
                WHERE m.tipo = 'saida'
                ORDER BY m.data DESC
                LIMIT 50
            """)
            saidas = cursor.fetchall()
            
            html += """
            <h4>📤 Saídas de Produtos</h4>
            <table border="1" cellpadding="8" cellspacing="0" style="border-collapse: collapse; width: 100%; margin-bottom: 20px;">
                <thead>
                    <tr style="background-color: #f44336; color: white;">
                        <th>Produto</th>
                        <th>Quantidade</th>
                        <th>Data</th>
                        <th>Usuário</th>
                    </tr>
                </thead>
                <tbody>
            """
            
            if saidas:
                for s in saidas:
                    html += f"""
                    <tr>
                        <td>{s['produto']}</td>
                        <td>{s['quantidade']}</td>
                        <td>{s['data']}</td>
                        <td>{s['usuario']}</td>
                    </tr>
                    """
            else:
                html += '<tr><td colspan="4" style="text-align: center;">Nenhuma saída registrada</td></tr>'
            
            html += "</tbody></table>"
        
        # ========== PRODUTOS CRÍTICOS ==========
        if incluir_criticos:
            cursor.execute("""
                SELECT nome, categoria, quantidade 
                FROM produtos 
                WHERE quantidade < 10 
                ORDER BY quantidade ASC
            """)
            criticos = cursor.fetchall()
            
            html += """
            <h4>⚠️ Produtos com Estoque Crítico (menos de 10 unidades)</h4>
            <table border="1" cellpadding="8" cellspacing="0" style="border-collapse: collapse; width: 100%; margin-bottom: 20px;">
                <thead>
                    <tr style="background-color: #ff9800; color: white;">
                        <th>Produto</th>
                        <th>Categoria</th>
                        <th>Quantidade</th>
                    </tr>
                </thead>
                <tbody>
            """
            
            if criticos:
                for c in criticos:
                    html += f"""
                    <tr>
                        <td>{c['nome']}</td>
                        <td>{c['categoria']}</td>
                        <td style="color: red; font-weight: bold;">{c['quantidade']}</td>
                    </tr>
                    """
            else:
                html += '<tr><td colspan="3" style="text-align: center;">Nenhum produto em nível crítico</td></tr>'
            
            html += "</tbody></table>"
        
        cursor.close()
        db.close()
        
        if not (incluir_estoque or incluir_movimentacoes or incluir_criticos):
            return "<p>Nenhuma opção selecionada para o relatório.</p>"
        
        return html
        
    except Exception as e:
        print(f"Erro ao gerar relatório: {e}")
        import traceback
        traceback.print_exc()
        return "<p>Erro ao gerar relatório.</p>"