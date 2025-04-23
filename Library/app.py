import json
import os
from datetime import datetime
from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
from dataclasses import dataclass, field, asdict

@dataclass
class Livro:
    titulo: str
    autor: str
    ano: int
    isbn: str = ""
    genero: str = ""
    disponivel: bool = True
    data_emprestimo: str = None
    emprestado_para: str = None
    id: int = None

    def __post_init__(self):
        if not self.id:
            #usar timestamp como ID temporario
            self.id = int(datetime.now().timestamp())

    def emprestar(self, usuario):
        if self.disponivel:
            self.disponivel = False
            self.data_emprestimo = datetime.now().strftime("%d/%m/%Y")
            self.emprestado_para = usuario
            return True
        return False
    
    def devolver(self):
        if not self.disponivel:
            self.disponivel = True
            self.data_emprestimo = None
            self.emprestado_para = None
            return True
        return False
    
    def to_dict(self):
        return asdict(self)

class Biblioteca:
    def __init__(self, nome = "Minha Biblioteca"):
        self.nome = nome
        self.livros = []
        self.arquivo_dados = "biblioteca_dados.json"
        self.carregar_dados()

    def adicionar_livro(self, livro):
        #Verificar se ISBN já existe
        if livro.isbn:
            for l in self.livros:
                if l.isbn == livro.isbn:
                    raise ValueError("ISBN já cadastrado.")
        self.livros.append(livro)
        self.salvar_dados()
        return True, f"Livro '{livro.titulo}' adicionado com sucesso!"
    
    def remover_livro(self, livro_id):
        for i, livro in enumerate(self.livros):
            if livro.id == livro_id:
                livro_removido = self.livros.pop(i)
                self.salvar_dados()
                return True, f"Livro '{livro_removido.titulo}' removido com sucesso!"
        return False, "Livro não encontrado."
    
    def buscar_por_id(self, livro_id):
        for livro in self.livros:
            if livro.id == livro_id:
                return livro
        return None
    
    def buscar_por_titulo(self, titulo):
        resultado = [livro for livro in self.livros if titulo.lower() in livro.titulo.lower()]
        return resultado
    
    def buscar_por_autor(self, autor):
        resultado = [livro for livro in self.livros if autor.lower() in livro.autor.lower()]
        return resultado
    
    def buscar_por_genero(self, genero):
        resultado = [livro for livro in self.livros if genero.lower() in livro.genero.lower()]
        return resultado
    
    def buscar_disponiveis(self):
        resultado = [livro for livro in self.livros if livro.disponivel]
        return resultado
    
    def buscar_emprestados(self):
        resultado = [livro for livro in self.livros if not livro.disponivel]
        return resultado
    
    def emprestar_livro(self, livro_id, usuario):
        livro = self.buscar_por_id(livro_id)
        if livro:
            if livro.emprestar(usuario):
                self.salvar_dados()
                return True, f"Livro '{livro.titulo}' emprestado para '{usuario}'."
            else:
                return False, "Livro já emprestado."
        return False, "Livro não encontrado."
    
    def devolver_livro(self, livro_id):
        livro = self.buscar_por_id(livro_id)
        if livro:
            if livro.devolver():
                self.salvar_dados()
                return True, f"Livro '{livro.titulo}' devolvido com sucesso!"
            else:
                return False, "Livro não está emprestado."
        return False, "Livro não encontrado."
    
    def editar_livro(self, livro_id, dados):
        livro = self.buscar_por_id(livro_id)
        if livro:
            for key, value in dados.items():
                if hasattr(livro, key):
                    setattr(livro, key, value)
            self.salvar_dados()
            return True, f"Livro '{livro.titulo}' editado com sucesso!"
        return False, "Livro não encontrado."
    
    def salvar_dados(self):
        with open(self.arquivo_dados, 'w', encoding='utf-8') as arquivo:
            dados = [livro.to_dict() for livro in self.livros]
            json.dump(dados, arquivo, ensure_ascii=False, indent=2)

    def carregar_dados(self):
        if os.path.exists(self.arquivo_dados):
            try:
                with open (self.arquivo_dados, 'r', encoding='utf-8') as arquivo:
                    dados = json.load(arquivo)
                    self.livros = [Livro(**livro) for livro in dados]
            except Exception as e:
                print(f"Erro ao carregar dados: {e}")
                self.livros = []
        else:
            self.livros = []

app = Flask(__name__)
app.secret_key = 'biblioteca_secreta'

biblioteca = Biblioteca()

@app.route('/')
def index():
    return render_template('index.html', livros=biblioteca.livros)

@app.route('/livros')
def listar_livros():
    return render_template('livros.html', livros=biblioteca.livros)

@app.route('/livro/novo', methods=['GET', 'POST'])
def novo_livro():
    if request.method == 'POST':
        livro = Livro(
            titulo = request.form('titulo'),
            autor = request.form('autor'),
            ano = int(request.form('ano')),
            isbn = request.form('isbn', ''),
            genero = request.form('genero', '')
        )
        sucesso ,mensagem = biblioteca.adicionar_livro(livro)
        if sucesso:
            flash(mensagem, 'success')
            return redirect(url_for('listar_livros'))
        else:
            flash(mensagem, 'danger')
    return render_template('form_livro.html')

@app.route('/livro/<int:id>', methods=['GET', 'POST'])
def editar_livro(id):
    livro = biblioteca.buscar_por_id(id)
    if not livro:
        flash("Livro não encontrado.", 'danger')
        return redirect(url_for('listar_livros'))
    
    if request.method == 'POST':
        dados = {
            'titulo': request.form.get('titulo'),
            'autor': request.form.get('autor'),
            'ano': int(request.form.get('ano')),
            'isbn': request.form.get('isbn',''),
            'genero': request.form.get('genero', '')
        }
        sucesso, mensagem = biblioteca.editar_livro(id, dados)
        if sucesso:
            flash(mensagem, 'success')
            return redirect(url_for('listar_livros'))
        else:
            flash(mensagem, 'danger')
    return render_template('form_livro.html', livro=livro)

@app.route
def remover_livro(id):
    sucesso, mensagem = biblioteca.remover_livro(id)
    if sucesso:
        flash(mensagem, 'success')
    else:
        flash(mensagem, 'danger')
    return redirect(url_for('listar_livros'))

@app.route('/livro/emprestar/<int:id>', methods=['GET', 'POST'])
def emprestar_livro(id):
    livro = biblioteca.buscar_por_id(id)
    if not livro:
        flash("Livro não encontrado.", 'danger')
        return redirect (url_for('listar_livros'))
    if request.method == 'POST':
        usuario = request.form.get('usuario')
        sucesso, mensagem = biblioteca.emprestar_livro(id, usuario)
        if sucesso:
            flash(mensagem, 'success')
            return redirect(url_for('listar_livros'))
        else:
            flash(mensagem, 'danger')
    return render_template('emprestar_livro.html', livro=livro)

@app.route('/livro/devolver/<int:id>')
def devolver_livro(id):
    sucesso, mensagem = biblioteca.devolver_livro(id)
    if sucesso:
        flash(mensagem, 'success')
    else:
        flash(mensagem, 'danger')
    return redirect(url_for('listar_livros'))

@app.route('/buscar')
def buscar():
    termo = request.args.get('termo')
    tipo = request.args.get('tipo')
    if tipo == 'titulo':
        resultado = biblioteca.buscar_por_titulo(termo)
    elif tipo == 'autor':
        resultado = biblioteca.buscar_por_autor(termo)
    elif tipo == 'genero':
        resultado = biblioteca.buscar_por_genero(termo)
    elif tipo == 'disponivel':
        resultado = biblioteca.buscar_disponiveis()
    elif tipo == 'emprestados':
        resultado = biblioteca.buscar_emprestados()
    else:
        resultado = []
    return render_template('buscar.html', livros=resultado, termo=termo, tipo=tipo)

@app.route('/api/livros', methods=['GET'])
def api_listar_livros():
    return jsonify([livro.to_dict() for livro in biblioteca.livros])

@app.route('/api/livros', methods=['GET'])
def api_obter_livro(id):
    livro = biblioteca.buscar_por_id(id)
    if livro:
        return jsonify(livro.to_dict())
    else:
        return jsonify({"error": "Livro não encontrado."}), 404
    
def inicializar_dados():
    if not biblioteca.livros:
        livros_exemplo = [
            Livro(titulo="1984", autor="George Orwell", ano=1949, isbn="1234567890", genero="Ficção Científica"),
            Livro(titulo="Dom Casmurro", autor="Machado de Assis", ano=1899, isbn="0987654321", genero="Romance"),
            Livro(titulo="O Senhor dos Anéis", autor="J.R.R. Tolkien", ano=1954, isbn="1122334455", genero="Fantasia"),
        ]
        for livro in livros_exemplo:
            biblioteca.adicionar_livro(livro)

if __name__ == '__main__':
    inicializar_dados()
    app.run(debug=True)