from flask import Flask, render_template, request, redirect, url_for, session
import sqlite3
import os

app = Flask(__name__)

# Defina a chave secreta (pode ser uma string aleatória ou gerada de maneira segura)
app.secret_key = os.urandom(24)  # Gera uma chave secreta de 24 bytes aleatórios

# Função para conectar ao banco de dados
def conectar_banco():
    conexao = sqlite3.connect('banco.db')  # Alterado para o banco 'banco.db'
    conexao.row_factory = sqlite3.Row  # Permite acessar colunas por nome
    return conexao

@app.route('/')
def home():
    return render_template('login.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        usuario = request.form['usuario']
        senha = request.form['senha']

        conexao = conectar_banco()
        cursor = conexao.cursor()
        cursor.execute('SELECT id, nome, usuario, senha, tipo FROM usuarios WHERE usuario = ?', (usuario,))
        user = cursor.fetchone()

        if user and user[3] == senha:  # Verificando senha
            session['user_id'] = user[0]
            session['user_name'] = user[1]
            session['user_tipo'] = user[4]  # Guardando o tipo do usuário (admin ou comum)
            return redirect(url_for('dashboard'))

        return 'Usuário ou senha inválidos'

    return render_template('login.html')

@app.route('/dashboard')
def dashboard():
    user_name = session.get('user_name')  # Acessando o nome do usuário diretamente da sessão
    if not user_name:  # Caso o nome do usuário não esteja na sessão
        return redirect(url_for('login'))  # Redireciona para o login
    return render_template('dashboard.html', user_name=user_name)

# Rota para a página de relatórios
@app.route('/relatorios', methods=['GET', 'POST'])
def relatorios():
    user_name = session.get('user_name')  # Acessando o nome do usuário diretamente da sessão
    # Conectando ao banco de dados
    conn = sqlite3.connect('banco.db')
    cursor = conn.cursor()

    # Consulta para pegar os produtos únicos da tabela 'movimentacao'
    cursor.execute("SELECT DISTINCT produto FROM movimentacoes")
    produtos = cursor.fetchall()

    # Fecha a conexão
    conn.close()

    # Passa as categorias e produtos para o template
    return render_template('relatorios.html', user_name=user_name, produtos=produtos)

# Rota para listar movimentações
@app.route('/movimentacao', methods=['GET', 'POST'])
def movimentacao():
    # Recupera o nome do usuário da sessão
    user_name = session.get('user_name')  # Supondo que o nome do usuário esteja armazenado na sessão

    # Conectando ao banco de dados e configurando para usar Row
    conexao = sqlite3.connect('banco.db')
    conexao.row_factory = sqlite3.Row  # Aqui configuramos para retornar linhas como dicionários
    cursor = conexao.cursor()

    # Consulta para pegar todos os dados da tabela 'movimentacoes'
    cursor.execute('SELECT * FROM movimentacoes ORDER BY id DESC')

    movimentacoes = cursor.fetchall()

    conexao.close()  # Fechando a conexão com o banco de dados

    # Passando as variáveis para o template
    return render_template('movimentacao.html', movimentacoes=movimentacoes, user_name=user_name)

@app.route('/cadastro_movimentacao', methods=['GET', 'POST'])
def cadastro_movimentacao():
    # Recupera o nome do usuário da sessão
    user_name = session.get('user_name')  # Supondo que o nome do usuário esteja armazenado na sessão

    if request.method == 'POST':
        # Recuperando os dados do formulário
        produto = request.form['produto']
        marca = request.form['marca']
        tipo_medida = request.form['tipo_medida']
        medida = request.form['medida']
        quantidade = request.form['quantidade']
        valor_unidade = request.form['valor_unidade']
        tipo = request.form['tipo']  # Novo campo tipo
        data_compra = request.form['data_compra']  # Novo campo data_compra
        categoria = request.form['categoria']  # Novo campo data_compra

        # Calculando o valor total
        valor_total = float(quantidade) * float(valor_unidade)

        # Conectando ao banco de dados e inserindo os dados
        conexao = sqlite3.connect('banco.db')  # Conexão com o banco de dados
        cursor = conexao.cursor()
        cursor.execute('''
            INSERT INTO movimentacoes (produto, marca, tipo_medida, medida, quantidade, valor_unidade, valor_total, tipo, data_compra, categoria)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?,?)
        ''', (produto, marca, tipo_medida, medida, quantidade, valor_unidade, valor_total, tipo, data_compra, categoria))

        conexao.commit()  # Confirmando a inserção
        conexao.close()  # Fechando a conexão com o banco de dados

        return redirect(url_for('movimentacao'))  # Redirecionando após o cadastro

    # Passando a variável user_name para o template
    return render_template('cadastro_movimentacao.html', user_name=user_name)

# Rota para editar movimentação
@app.route('/editar_movimentacao/<int:id>', methods=['GET', 'POST'])
def editar_movimentacao(id):
    # Recupera o nome do usuário da sessão
    user_name = session.get('user_name')  # Supondo que o nome do usuário esteja armazenado na sessão

    conexao = conectar_banco()
    cursor = conexao.cursor()

    if request.method == 'POST':
        produto = request.form['produto']
        marca = request.form['marca']
        tipo_medida = request.form['tipo_medida']
        medida = request.form['medida']
        quantidade = request.form['quantidade']
        valor_unidade = request.form['valor_unidade']
        valor_total = float(quantidade) * float(valor_unidade)  # Calculando o valor total
        data_compra = request.form['data_compra']  # Captura a data
        tipo = request.form['tipo']  # Captura o tipo de movimentação
        categoria = request.form['categoria']  # Captura o tipo de movimentação

        cursor.execute('''
            UPDATE movimentacoes
            SET produto = ?, marca = ?, tipo_medida = ?, medida = ?, quantidade = ?, valor_unidade = ?, valor_total = ?, data_compra = ?, tipo = ?,  categoria = ?
            WHERE id = ?
        ''', (produto, marca, tipo_medida, medida, quantidade, valor_unidade, valor_total, data_compra, tipo, categoria, id))
        conexao.commit()
        conexao.close()

        return redirect(url_for('movimentacao'))

    # Obtendo os dados da movimentação com o ID fornecido
    cursor.execute('SELECT * FROM movimentacoes WHERE id = ?', (id,))
    movimentacao = cursor.fetchone()
    conexao.close()

    # Passando a variável user_name e os dados da movimentação para o template
    return render_template('editar_movimentacao.html', movimentacao=movimentacao, user_name=user_name)

# Rota para excluir movimentação
@app.route('/excluir_movimentacao/<int:id>', methods=['POST'])
def excluir_movimentacao(id):
    conexao = conectar_banco()
    cursor = conexao.cursor()
    cursor.execute('DELETE FROM movimentacoes WHERE id = ?', (id,))
    conexao.commit()
    conexao.close()

    return redirect(url_for('movimentacao'))

from flask import redirect, url_for, session

@app.route('/usuarios')
def usuarios():
    if session.get('user_tipo') != 'admin':
        return redirect(url_for('dashboard'))  # Redireciona para o dashboard caso o usuário não seja admin

    conexao = conectar_banco()
    cursor = conexao.cursor()
    cursor.execute('SELECT * FROM usuarios')
    users = cursor.fetchall()
    conexao.close()

    # Obter o nome do usuário diretamente da sessão
    user_name = session.get('user_name')

    return render_template('usuarios.html', users=users, user_name=user_name)

@app.route('/cadastro_usuario', methods=['GET', 'POST'])
def cadastro_usuario():
    # Acesso ao nome do usuário da sessão
    user_name = session.get('user_name')

    if request.method == 'POST':
        nome = request.form['nome']
        usuario = request.form['usuario']
        email = request.form['email']
        senha = request.form['senha']

        # Conectar ao banco de dados
        conexao = conectar_banco()
        cursor = conexao.cursor()
        try:
            # Inserir novo usuário no banco de dados
            cursor.execute('INSERT INTO usuarios (nome, usuario, email, senha) VALUES (?, ?, ?, ?)',
                           (nome, usuario, email, senha))
            conexao.commit()
        except sqlite3.IntegrityError:
            return "Erro: Usuário já existe."
        finally:
            conexao.close()

        # Redirecionar para a página de usuários com o nome do usuário logado
        return redirect(url_for('usuarios', user_name=user_name))

    # Renderizar a página de cadastro
    return render_template('cadastro_usuario.html', user_name=user_name)

@app.route('/editar_usuario/<int:user_id>', methods=['GET', 'POST'])
def editar_usuario(user_id):
    conexao = conectar_banco()
    cursor = conexao.cursor()

    # Recupera o nome do usuário logado
    user_name = session.get('user_name')

    if request.method == 'POST':
        nome = request.form['nome']
        usuario = request.form['usuario']
        email = request.form['email']
        senha = request.form['senha']

        # Atualiza os dados do usuário no banco de dados
        cursor.execute('''UPDATE usuarios SET nome = ?, usuario = ?, email = ?, senha = ? WHERE id = ?''',
                       (nome, usuario, email, senha, user_id))
        conexao.commit()
        conexao.close()

        # Redireciona para a página de usuários
        return redirect(url_for('usuarios', user_name=user_name))

    # Busca os dados do usuário para pré-preencher o formulário
    cursor.execute('SELECT * FROM usuarios WHERE id = ?', (user_id,))
    user = cursor.fetchone()
    conexao.close()

    # Renderiza o template de edição, passando o objeto 'user'
    return render_template('editar_usuario.html', user=user, user_name=user_name)

    # Buscar dados do usuário para pré-preencher o formulário
    cursor.execute('SELECT * FROM usuarios WHERE id = ?', (user_id,))
    user = cursor.fetchone()
    conexao.close()

    # Renderizar o template de edição de usuário
    return render_template('editar_usuario.html', user=user, user_name=user_name)

# Alteração para o método DELETE
@app.route('/excluir_usuario/<int:user_id>', methods=['POST', 'DELETE'])
def excluir_usuario(user_id):
    if request.method == 'POST' or request.form.get('_method') == 'DELETE':
        conexao = conectar_banco()
        cursor = conexao.cursor()
        cursor.execute('DELETE FROM usuarios WHERE id = ?', (user_id,))
        conexao.commit()
        conexao.close()
        return redirect(url_for('usuarios', user_name=request.args.get('user_name')))
    return redirect(url_for('usuarios', user_name=request.args.get('user_name')))

@app.route('/logout')
def logout():
    session.clear()  # Limpa todos os dados da sessão
    return redirect(url_for('login'))

if __name__ == '__main__':
    app.run(debug=True)
