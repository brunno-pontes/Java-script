from flask import Flask, render_template, request, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
import os

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///padaria.db'
app.config['SECRET_KEY'] = 'chave_secreta'

db = SQLAlchemy()
db.init_app(app)

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

# Modelo de Produto
class Produto(db.Model):
    __tablename__ = 'produto'
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(100), nullable=False)
    descricao = db.Column(db.String(500))
    ingredientes = db.Column(db.String(500))
    origem = db.Column(db.String(100))
    imagem = db.Column(db.String(100))

    def __init__(self, nome: str, descricao: str, ingredientes:str, origem: str, imagem: str)->None:
        self.nome = nome
        self.descricao = descricao
        self.ingredientes = ingredientes
        self.origem = origem
        self.imagem = imagem

# Modelo de Usuário com Flask-Login
class Usuario(UserMixin, db.Model):
    __tablename__ = 'usuario'
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False)
    senha = db.Column(db.String(100), nullable=False)

@login_manager.user_loader
def load_user(user_id):
    return Usuario.query.get(int(user_id))



@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        senha = request.form['senha']
        user = Usuario.query.filter_by(email=email, senha=senha).first()
        if user:
            login_user(user)
            # flash('Login realizado com sucesso!', 'success')
            return redirect(url_for('home'))
        else:
            flash('Usuário ou senha incorretos', 'danger')
    return render_template('login.html')

@app.route('/cadastro', methods=['GET', 'POST'])
def cadastro():
    if request.method == 'POST':
        nome = request.form['nome']
        email = request.form['email']
        senha = request.form['senha']
        if Usuario.query.filter_by(email=email).first():
            flash('Email já cadastrado!', 'danger')
        else:
            novo_usuario = Usuario(nome=nome, email=email, senha=senha)
            db.session.add(novo_usuario)
            db.session.commit()
            flash('Cadastro realizado com sucesso! Faça login.', 'success')
            return redirect(url_for('login'))
    return render_template('cadastro.html')


@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('Logout realizado com sucesso!', 'info')
    
    return redirect(url_for('login'))

@app.route('/')
@login_required
def home():
    return render_template(('index.html'))
@app.route("/produtos", methods=["GET", "POST"])
@login_required
def produtos():
    if request.method == 'POST':
        termo = request.form['pesquisa']
        resultado = db.session.execute(db.select(Produto).filter(Produto.nome.like(f'%{termo}%'))).scalars()
        return render_template('produto.html', produtos=resultado)

    else: 
        produtos = db.session.execute(db.select(Produto)).scalars()
        return render_template('produto.html', produtos=produtos)

@app.route('/cadastrar_produto', methods=['GET', 'POST'])
@login_required
def cadastrar_produto():
        if request.method == 'POST':
            status = {"type": "success", "message": "Produto cadastrado com sucesso!"}
            dados = request.form
            imagem = request.files['imagem']
            try:
                produto = Produto(dados['nome'], dados['descricao'], dados['ingredientes'], dados['origem'], imagem.filename)
                imagem.save(os.path.join('static/imagens', imagem.filename))
                db.session.add(produto)
                db.session.commit()
            except:
                status = {"type": "error", "message": "Erro ao cadastrar produto!"}    


            return render_template('cadastrar_produto.html', status=status)    
        else:
             return render_template('cadastrar_produto.html')
        
@app.route('/editar_produto/<int:id>', methods=['GET', 'POST'])
@login_required
def editar_produto(id):
    if request.method == 'POST':
            dados = request.form
            imagem = request.files['imagem']
            produto = db.session.execute(db.select(Produto).filter(Produto.id == id)).scalar()
            produto.nome = dados['nome']
            produto.descricao = dados['descricao']
            produto.ingredientes = dados['ingredientes']
            produto.origem = dados['origem']
            if imagem.filename:
               produto.imagem = imagem.filename
            db.session.commit()
            return redirect('/produtos')
       
    else:
        produto = db.session.execute(db.select(Produto).filter(Produto.id == id)).scalar()
        return render_template('editar_produto.html',produto=produto)               
@app.route('/deletar_produto/<int:id>', methods=['GET', 'POST'])
@login_required
def deletar_produto(id):
    produto = db.session.execute(db.select(Produto).filter(Produto.id == id)).scalar()
    db.session.delete(produto)
    db.session.commit()
    return redirect('/produtos')    

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
        app.run(debug=True)