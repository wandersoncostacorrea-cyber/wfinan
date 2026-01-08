from flask import Flask, render_template, request, redirect, url_for, flash, jsonify, send_file
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from datetime import datetime, timedelta
from sqlalchemy import func, extract, or_, and_
from calendar import monthrange
import os
import base64

app = Flask(__name__)
app.config['SECRET_KEY'] = 'sua-chave-secreta-aqui-mude-em-producao'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///finance.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['MAX_CONTENT_LENGTH'] = 5 * 1024 * 1024  # 5MB max

# Criar pasta de uploads se não existir
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

db = SQLAlchemy(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'

# Models
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(200), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    accounts = db.relationship('Account', backref='user', lazy=True, cascade='all, delete-orphan')
    transactions = db.relationship('Transaction', backref='user', lazy=True, cascade='all, delete-orphan')
    categories = db.relationship('Category', backref='user', lazy=True, cascade='all, delete-orphan')
    credit_cards = db.relationship('CreditCard', backref='user', lazy=True, cascade='all, delete-orphan')
    installments = db.relationship('Installment', backref='user', lazy=True, cascade='all, delete-orphan')
    transfers = db.relationship('Transfer', backref='user', lazy=True, cascade='all, delete-orphan')

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)


class Account(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    name = db.Column(db.String(100), nullable=False)
    type = db.Column(db.String(50), nullable=False)
    initial_balance = db.Column(db.Float, default=0.0)
    current_balance = db.Column(db.Float, default=0.0)
    color = db.Column(db.String(7), default='#3B82F6')
    icon = db.Column(db.String(50), default='bank')
    active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    transactions = db.relationship('Transaction', backref='account', lazy=True)
    transfers_from = db.relationship('Transfer', foreign_keys='Transfer.from_account_id', backref='from_account', lazy=True)
    transfers_to = db.relationship('Transfer', foreign_keys='Transfer.to_account_id', backref='to_account', lazy=True)


class Category(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    name = db.Column(db.String(100), nullable=False)
    type = db.Column(db.String(20), nullable=False)
    color = db.Column(db.String(7), default='#6B7280')
    icon = db.Column(db.String(50), default='tag')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    transactions = db.relationship('Transaction', backref='category', lazy=True)


class CreditCard(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    name = db.Column(db.String(100), nullable=False)
    limit = db.Column(db.Float, nullable=False)
    closing_day = db.Column(db.Integer, nullable=False)  # Dia do fechamento (1-31)
    due_day = db.Column(db.Integer, nullable=False)  # Dia do vencimento (1-31)
    color = db.Column(db.String(7), default='#8B5CF6')
    icon = db.Column(db.String(50), default='credit-card')
    active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    transactions = db.relationship('Transaction', backref='credit_card', lazy=True)
    
    def get_current_invoice_period(self):
        """Retorna período da fatura atual (início e fim)"""
        today = datetime.today()
        
        if today.day < self.closing_day:
            # Fatura atual: mês passado até este mês
            end_date = datetime(today.year, today.month, self.closing_day)
            if today.month == 1:
                start_date = datetime(today.year - 1, 12, self.closing_day)
            else:
                start_date = datetime(today.year, today.month - 1, self.closing_day)
        else:
            # Fatura atual: este mês até próximo mês
            start_date = datetime(today.year, today.month, self.closing_day)
            if today.month == 12:
                end_date = datetime(today.year + 1, 1, self.closing_day)
            else:
                end_date = datetime(today.year, today.month + 1, self.closing_day)
        
        return start_date.date(), end_date.date()
    
    def get_invoice_total(self, start_date, end_date):
        """Calcula o total da fatura em um período"""
        total = db.session.query(func.sum(Transaction.amount)).filter(
            Transaction.credit_card_id == self.id,
            Transaction.type == 'expense',
            Transaction.date >= start_date,
            Transaction.date < end_date
        ).scalar() or 0
        
        # Adicionar parcelas do período
        installment_total = db.session.query(func.sum(Installment.amount)).filter(
            Installment.credit_card_id == self.id,
            Installment.due_date >= start_date,
            Installment.due_date < end_date
        ).scalar() or 0
        
        return total + installment_total
    
    def get_available_limit(self):
        """Calcula o limite disponível"""
        start_date, end_date = self.get_current_invoice_period()
        used = self.get_invoice_total(start_date, end_date)
        return self.limit - used


class Transaction(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    account_id = db.Column(db.Integer, db.ForeignKey('account.id'), nullable=True)
    credit_card_id = db.Column(db.Integer, db.ForeignKey('credit_card.id'), nullable=True)
    category_id = db.Column(db.Integer, db.ForeignKey('category.id'), nullable=True)
    description = db.Column(db.String(200), nullable=False)
    amount = db.Column(db.Float, nullable=False)
    type = db.Column(db.String(20), nullable=False)
    date = db.Column(db.Date, nullable=False)
    notes = db.Column(db.Text)
    attachment = db.Column(db.String(200))  # Nome do arquivo
    attachment_type = db.Column(db.String(50))  # image ou pdf
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


class Installment(db.Model):
    """Parcelas de compras parceladas"""
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    account_id = db.Column(db.Integer, db.ForeignKey('account.id'), nullable=True)
    credit_card_id = db.Column(db.Integer, db.ForeignKey('credit_card.id'), nullable=True)
    category_id = db.Column(db.Integer, db.ForeignKey('category.id'), nullable=True)
    description = db.Column(db.String(200), nullable=False)
    total_amount = db.Column(db.Float, nullable=False)  # Valor total da compra
    amount = db.Column(db.Float, nullable=False)  # Valor da parcela
    current_installment = db.Column(db.Integer, nullable=False)  # Parcela atual (1, 2, 3...)
    total_installments = db.Column(db.Integer, nullable=False)  # Total de parcelas
    due_date = db.Column(db.Date, nullable=False)  # Data de vencimento desta parcela
    paid = db.Column(db.Boolean, default=False)
    paid_date = db.Column(db.Date)
    purchase_date = db.Column(db.Date, nullable=False)  # Data da compra
    notes = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    account = db.relationship('Account', backref='installments')
    credit_card = db.relationship('CreditCard', backref='installments')
    category = db.relationship('Category', backref='installments')


class Transfer(db.Model):
    """Transferências entre contas"""
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    from_account_id = db.Column(db.Integer, db.ForeignKey('account.id'), nullable=False)
    to_account_id = db.Column(db.Integer, db.ForeignKey('account.id'), nullable=False)
    amount = db.Column(db.Float, nullable=False)
    date = db.Column(db.Date, nullable=False)
    description = db.Column(db.String(200))
    notes = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


# ==================== ROTAS BÁSICAS ====================

@app.route('/')
def index():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    return redirect(url_for('login'))


@app.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    
    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')
        
        if User.query.filter_by(username=username).first():
            flash('Usuário já existe', 'error')
            return redirect(url_for('register'))
        
        if User.query.filter_by(email=email).first():
            flash('Email já cadastrado', 'error')
            return redirect(url_for('register'))
        
        user = User(username=username, email=email)
        user.set_password(password)
        db.session.add(user)
        db.session.commit()
        
        create_default_categories(user.id)
        
        flash('Cadastro realizado com sucesso!', 'success')
        return redirect(url_for('login'))
    
    return render_template('register.html')


@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        user = User.query.filter_by(username=username).first()
        
        if user and user.check_password(password):
            login_user(user)
            return redirect(url_for('dashboard'))
        
        flash('Usuário ou senha inválidos', 'error')
    
    return render_template('login.html')


@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))


@app.route('/dashboard')
@login_required
def dashboard():
    today = datetime.today()
    current_month = today.month
    current_year = today.year
    
    # Estatísticas do mês
    month_income = db.session.query(func.sum(Transaction.amount)).filter(
        Transaction.user_id == current_user.id,
        Transaction.type == 'income',
        extract('month', Transaction.date) == current_month,
        extract('year', Transaction.date) == current_year
    ).scalar() or 0
    
    month_expense = db.session.query(func.sum(Transaction.amount)).filter(
        Transaction.user_id == current_user.id,
        Transaction.type == 'expense',
        Transaction.account_id.isnot(None),  # Apenas débito
        extract('month', Transaction.date) == current_month,
        extract('year', Transaction.date) == current_year
    ).scalar() or 0
    
    # Adicionar parcelas pagas do mês
    month_installments = db.session.query(func.sum(Installment.amount)).filter(
        Installment.user_id == current_user.id,
        Installment.paid == True,
        extract('month', Installment.paid_date) == current_month,
        extract('year', Installment.paid_date) == current_year,
        Installment.account_id.isnot(None)  # Apenas débito
    ).scalar() or 0
    
    month_expense += month_installments
    
    balance = month_income - month_expense
    
    # Contas
    accounts = Account.query.filter_by(user_id=current_user.id, active=True).all()
    total_accounts = sum(acc.current_balance for acc in accounts)
    
    # Cartões de crédito
    credit_cards = CreditCard.query.filter_by(user_id=current_user.id, active=True).all()
    
    # Últimas transações (incluindo parcelas)
    recent_transactions = Transaction.query.filter_by(user_id=current_user.id)\
        .order_by(Transaction.date.desc(), Transaction.created_at.desc())\
        .limit(10).all()
    
    # Despesas por categoria
    expenses_by_category = db.session.query(
        Category.name, 
        Category.color,
        func.sum(Transaction.amount).label('total')
    ).join(Transaction).filter(
        Transaction.user_id == current_user.id,
        Transaction.type == 'expense',
        extract('month', Transaction.date) == current_month,
        extract('year', Transaction.date) == current_year
    ).group_by(Category.id).all()
    
    # Parcelas pendentes do mês
    pending_installments = Installment.query.filter(
        Installment.user_id == current_user.id,
        Installment.paid == False,
        extract('month', Installment.due_date) == current_month,
        extract('year', Installment.due_date) == current_year
    ).count()
    
    # Comprometimento futuro (próximos 3 meses)
    future_commitment = 0
    for i in range(1, 4):
        future_month = (today.month + i - 1) % 12 + 1
        future_year = today.year + (today.month + i - 1) // 12
        
        commitment = db.session.query(func.sum(Installment.amount)).filter(
            Installment.user_id == current_user.id,
            Installment.paid == False,
            extract('month', Installment.due_date) == future_month,
            extract('year', Installment.due_date) == future_year
        ).scalar() or 0
        
        future_commitment += commitment
    
    return render_template('dashboard.html',
                         month_income=month_income,
                         month_expense=month_expense,
                         balance=balance,
                         accounts=accounts,
                         total_accounts=total_accounts,
                         credit_cards=credit_cards,
                         recent_transactions=recent_transactions,
                         expenses_by_category=expenses_by_category,
                         pending_installments=pending_installments,
                         future_commitment=future_commitment,
                         current_month=current_month,
                         current_year=current_year)


# ==================== TRANSAÇÕES ====================

@app.route('/transactions')
@login_required
def transactions():
    account_filter = request.args.get('account', type=int)
    category_filter = request.args.get('category', type=int)
    type_filter = request.args.get('type')
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')
    
    query = Transaction.query.filter_by(user_id=current_user.id)
    
    if account_filter:
        query = query.filter_by(account_id=account_filter)
    if category_filter:
        query = query.filter_by(category_id=category_filter)
    if type_filter:
        query = query.filter_by(type=type_filter)
    if start_date:
        query = query.filter(Transaction.date >= datetime.strptime(start_date, '%Y-%m-%d').date())
    if end_date:
        query = query.filter(Transaction.date <= datetime.strptime(end_date, '%Y-%m-%d').date())
    
    transactions_list = query.order_by(Transaction.date.desc(), Transaction.created_at.desc()).all()
    
    accounts = Account.query.filter_by(user_id=current_user.id, active=True).all()
    categories = Category.query.filter_by(user_id=current_user.id).all()
    
    return render_template('transactions.html',
                         transactions=transactions_list,
                         accounts=accounts,
                         categories=categories)


@app.route('/transaction/add', methods=['GET', 'POST'])
@login_required
def add_transaction():
    if request.method == 'POST':
        # Verificar se é parcelado
        is_installment = request.form.get('is_installment') == 'on'
        installments_count = int(request.form.get('installments_count', 1))
        
        payment_method = request.form.get('payment_method')  # debit ou credit
        
        if is_installment and installments_count > 1:
            # Criar parcelas
            return create_installment_purchase(request.form, payment_method)
        else:
            # Transação simples
            return create_simple_transaction(request.form, payment_method)
    
    accounts = Account.query.filter_by(user_id=current_user.id, active=True).all()
    credit_cards = CreditCard.query.filter_by(user_id=current_user.id, active=True).all()
    categories = Category.query.filter_by(user_id=current_user.id).all()
    
    return render_template('add_transaction.html', 
                         accounts=accounts, 
                         credit_cards=credit_cards,
                         categories=categories)


def create_simple_transaction(form_data, payment_method):
    """Cria uma transação simples"""
    # Upload de anexo
    attachment_filename = None
    attachment_type = None
    
    if 'attachment' in request.files:
        file = request.files['attachment']
        if file and file.filename:
            filename = secure_filename(file.filename)
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            attachment_filename = f"{timestamp}_{filename}"
            file.save(os.path.join(app.config['UPLOAD_FOLDER'], attachment_filename))
            
            if filename.lower().endswith(('.png', '.jpg', '.jpeg', '.gif')):
                attachment_type = 'image'
            elif filename.lower().endswith('.pdf'):
                attachment_type = 'pdf'
    
    transaction = Transaction(
        user_id=current_user.id,
        account_id=int(form_data.get('account_id')) if payment_method == 'debit' else None,
        credit_card_id=int(form_data.get('credit_card_id')) if payment_method == 'credit' else None,
        category_id=form_data.get('category_id') or None,
        description=form_data.get('description'),
        amount=float(form_data.get('amount')),
        type=form_data.get('type'),
        date=datetime.strptime(form_data.get('date'), '%Y-%m-%d').date(),
        notes=form_data.get('notes'),
        attachment=attachment_filename,
        attachment_type=attachment_type
    )
    
    db.session.add(transaction)
    
    # Atualizar saldo da conta (apenas débito)
    if payment_method == 'debit':
        account = Account.query.get(transaction.account_id)
        if transaction.type == 'income':
            account.current_balance += transaction.amount
        else:
            account.current_balance -= transaction.amount
    
    db.session.commit()
    flash('Transação adicionada com sucesso!', 'success')
    return redirect(url_for('transactions'))


def create_installment_purchase(form_data, payment_method):
    """Cria parcelas de uma compra parcelada"""
    description = form_data.get('description')
    total_amount = float(form_data.get('amount'))
    installments_count = int(form_data.get('installments_count'))
    purchase_date = datetime.strptime(form_data.get('date'), '%Y-%m-%d').date()
    
    installment_amount = total_amount / installments_count
    
    # Criar cada parcela
    for i in range(installments_count):
        # Calcular data de vencimento
        due_date = purchase_date + timedelta(days=30 * i)
        
        installment = Installment(
            user_id=current_user.id,
            account_id=int(form_data.get('account_id')) if payment_method == 'debit' else None,
            credit_card_id=int(form_data.get('credit_card_id')) if payment_method == 'credit' else None,
            category_id=form_data.get('category_id') or None,
            description=f"{description} - Parcela {i+1}/{installments_count}",
            total_amount=total_amount,
            amount=installment_amount,
            current_installment=i + 1,
            total_installments=installments_count,
            due_date=due_date,
            purchase_date=purchase_date,
            notes=form_data.get('notes')
        )
        
        # Se primeira parcela e débito, pagar automaticamente
        if i == 0 and payment_method == 'debit':
            installment.paid = True
            installment.paid_date = purchase_date
            
            # Atualizar saldo da conta
            account = Account.query.get(installment.account_id)
            account.current_balance -= installment_amount
        
        db.session.add(installment)
    
    db.session.commit()
    flash(f'Compra parcelada em {installments_count}x criada com sucesso!', 'success')
    return redirect(url_for('installments_list'))


@app.route('/transaction/edit/<int:id>', methods=['GET', 'POST'])
@login_required
def edit_transaction(id):
    transaction = Transaction.query.filter_by(id=id, user_id=current_user.id).first_or_404()
    
    if request.method == 'POST':
        # Reverter saldo anterior
        if transaction.account_id:
            account = Account.query.get(transaction.account_id)
            if transaction.type == 'income':
                account.current_balance -= transaction.amount
            else:
                account.current_balance += transaction.amount
        
        # Atualizar transação
        old_account_id = transaction.account_id
        payment_method = request.form.get('payment_method')
        
        transaction.account_id = int(request.form.get('account_id')) if payment_method == 'debit' else None
        transaction.credit_card_id = int(request.form.get('credit_card_id')) if payment_method == 'credit' else None
        transaction.category_id = request.form.get('category_id') or None
        transaction.description = request.form.get('description')
        transaction.amount = float(request.form.get('amount'))
        transaction.type = request.form.get('type')
        transaction.date = datetime.strptime(request.form.get('date'), '%Y-%m-%d').date()
        transaction.notes = request.form.get('notes')
        
        # Upload de novo anexo
        if 'attachment' in request.files:
            file = request.files['attachment']
            if file and file.filename:
                filename = secure_filename(file.filename)
                timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                attachment_filename = f"{timestamp}_{filename}"
                file.save(os.path.join(app.config['UPLOAD_FOLDER'], attachment_filename))
                
                transaction.attachment = attachment_filename
                if filename.lower().endswith(('.png', '.jpg', '.jpeg', '.gif')):
                    transaction.attachment_type = 'image'
                elif filename.lower().endswith('.pdf'):
                    transaction.attachment_type = 'pdf'
        
        # Aplicar novo saldo (apenas débito)
        if payment_method == 'debit' and transaction.account_id:
            if old_account_id != transaction.account_id:
                account = Account.query.get(transaction.account_id)
            
            if transaction.type == 'income':
                account.current_balance += transaction.amount
            else:
                account.current_balance -= transaction.amount
        
        db.session.commit()
        flash('Transação atualizada com sucesso!', 'success')
        return redirect(url_for('transactions'))
    
    accounts = Account.query.filter_by(user_id=current_user.id, active=True).all()
    credit_cards = CreditCard.query.filter_by(user_id=current_user.id, active=True).all()
    categories = Category.query.filter_by(user_id=current_user.id).all()
    
    return render_template('edit_transaction.html', 
                         transaction=transaction,
                         accounts=accounts,
                         credit_cards=credit_cards,
                         categories=categories)


@app.route('/transaction/delete/<int:id>', methods=['POST'])
@login_required
def delete_transaction(id):
    transaction = Transaction.query.filter_by(id=id, user_id=current_user.id).first_or_404()
    
    # Reverter saldo
    if transaction.account_id:
        account = Account.query.get(transaction.account_id)
        if transaction.type == 'income':
            account.current_balance -= transaction.amount
        else:
            account.current_balance += transaction.amount
    
    # Remover arquivo anexo se existir
    if transaction.attachment:
        try:
            os.remove(os.path.join(app.config['UPLOAD_FOLDER'], transaction.attachment))
        except:
            pass
    
    db.session.delete(transaction)
    db.session.commit()
    
    flash('Transação excluída com sucesso!', 'success')
    return redirect(url_for('transactions'))


@app.route('/attachment/<filename>')
@login_required
def view_attachment(filename):
    """Visualizar ou baixar anexo"""
    return send_file(os.path.join(app.config['UPLOAD_FOLDER'], filename))


# ==================== PARCELAS ====================

@app.route('/installments')
@login_required
def installments_list():
    status_filter = request.args.get('status', 'pending')
    
    query = Installment.query.filter_by(user_id=current_user.id)
    
    if status_filter == 'pending':
        query = query.filter_by(paid=False)
    elif status_filter == 'paid':
        query = query.filter_by(paid=True)
    
    installments = query.order_by(Installment.due_date.asc()).all()
    
    return render_template('installments.html', installments=installments, status_filter=status_filter)


@app.route('/installment/pay/<int:id>', methods=['POST'])
@login_required
def pay_installment(id):
    installment = Installment.query.filter_by(id=id, user_id=current_user.id).first_or_404()
    
    if installment.paid:
        flash('Parcela já foi paga!', 'warning')
        return redirect(url_for('installments_list'))
    
    installment.paid = True
    installment.paid_date = datetime.today().date()
    
    # Atualizar saldo da conta (se for débito)
    if installment.account_id:
        account = Account.query.get(installment.account_id)
        account.current_balance -= installment.amount
    
    db.session.commit()
    flash('Parcela paga com sucesso!', 'success')
    return redirect(url_for('installments_list'))


@app.route('/installment/unpay/<int:id>', methods=['POST'])
@login_required
def unpay_installment(id):
    installment = Installment.query.filter_by(id=id, user_id=current_user.id).first_or_404()
    
    if not installment.paid:
        flash('Parcela não está paga!', 'warning')
        return redirect(url_for('installments_list'))
    
    installment.paid = False
    installment.paid_date = None
    
    # Reverter saldo da conta (se for débito)
    if installment.account_id:
        account = Account.query.get(installment.account_id)
        account.current_balance += installment.amount
    
    db.session.commit()
    flash('Pagamento da parcela revertido!', 'success')
    return redirect(url_for('installments_list'))


# ==================== CONTAS ====================

@app.route('/accounts')
@login_required
def accounts():
    accounts_list = Account.query.filter_by(user_id=current_user.id).order_by(Account.created_at.desc()).all()
    return render_template('accounts.html', accounts=accounts_list)


@app.route('/account/add', methods=['GET', 'POST'])
@login_required
def add_account():
    if request.method == 'POST':
        initial_balance = float(request.form.get('initial_balance', 0))
        account = Account(
            user_id=current_user.id,
            name=request.form.get('name'),
            type=request.form.get('type'),
            initial_balance=initial_balance,
            current_balance=initial_balance,
            color=request.form.get('color', '#3B82F6'),
            icon=request.form.get('icon', 'bank')
        )
        
        db.session.add(account)
        db.session.commit()
        
        flash('Conta adicionada com sucesso!', 'success')
        return redirect(url_for('accounts'))
    
    return render_template('add_account.html')


@app.route('/account/edit/<int:id>', methods=['GET', 'POST'])
@login_required
def edit_account(id):
    account = Account.query.filter_by(id=id, user_id=current_user.id).first_or_404()
    
    if request.method == 'POST':
        account.name = request.form.get('name')
        account.type = request.form.get('type')
        account.color = request.form.get('color')
        account.icon = request.form.get('icon')
        account.active = request.form.get('active') == 'on'
        
        db.session.commit()
        flash('Conta atualizada com sucesso!', 'success')
        return redirect(url_for('accounts'))
    
    return render_template('edit_account.html', account=account)


# ==================== CARTÕES DE CRÉDITO ====================

@app.route('/credit-cards')
@login_required
def credit_cards():
    cards = CreditCard.query.filter_by(user_id=current_user.id).order_by(CreditCard.created_at.desc()).all()
    
    # Calcular dados de cada cartão
    cards_data = []
    for card in cards:
        start_date, end_date = card.get_current_invoice_period()
        current_invoice = card.get_invoice_total(start_date, end_date)
        available_limit = card.get_available_limit()
        
        cards_data.append({
            'card': card,
            'current_invoice': current_invoice,
            'available_limit': available_limit,
            'usage_percent': (current_invoice / card.limit * 100) if card.limit > 0 else 0
        })
    
    return render_template('credit_cards.html', cards_data=cards_data)


@app.route('/credit-card/add', methods=['GET', 'POST'])
@login_required
def add_credit_card():
    if request.method == 'POST':
        card = CreditCard(
            user_id=current_user.id,
            name=request.form.get('name'),
            limit=float(request.form.get('limit')),
            closing_day=int(request.form.get('closing_day')),
            due_day=int(request.form.get('due_day')),
            color=request.form.get('color', '#8B5CF6'),
            icon=request.form.get('icon', 'credit-card')
        )
        
        db.session.add(card)
        db.session.commit()
        
        flash('Cartão de crédito adicionado com sucesso!', 'success')
        return redirect(url_for('credit_cards'))
    
    return render_template('add_credit_card.html')


@app.route('/credit-card/edit/<int:id>', methods=['GET', 'POST'])
@login_required
def edit_credit_card(id):
    card = CreditCard.query.filter_by(id=id, user_id=current_user.id).first_or_404()
    
    if request.method == 'POST':
        card.name = request.form.get('name')
        card.limit = float(request.form.get('limit'))
        card.closing_day = int(request.form.get('closing_day'))
        card.due_day = int(request.form.get('due_day'))
        card.color = request.form.get('color')
        card.icon = request.form.get('icon')
        card.active = request.form.get('active') == 'on'
        
        db.session.commit()
        flash('Cartão atualizado com sucesso!', 'success')
        return redirect(url_for('credit_cards'))
    
    return render_template('edit_credit_card.html', card=card)


@app.route('/credit-card/invoice/<int:id>')
@login_required
def credit_card_invoice(id):
    card = CreditCard.query.filter_by(id=id, user_id=current_user.id).first_or_404()
    
    # Período da fatura
    start_date, end_date = card.get_current_invoice_period()
    
    # Transações da fatura
    transactions = Transaction.query.filter(
        Transaction.credit_card_id == id,
        Transaction.type == 'expense',
        Transaction.date >= start_date,
        Transaction.date < end_date
    ).order_by(Transaction.date.desc()).all()
    
    # Parcelas da fatura
    installments = Installment.query.filter(
        Installment.credit_card_id == id,
        Installment.due_date >= start_date,
        Installment.due_date < end_date
    ).order_by(Installment.due_date.desc()).all()
    
    total = card.get_invoice_total(start_date, end_date)
    
    return render_template('credit_card_invoice.html',
                         card=card,
                         start_date=start_date,
                         end_date=end_date,
                         transactions=transactions,
                         installments=installments,
                         total=total)


# ==================== TRANSFERÊNCIAS ====================

@app.route('/transfers')
@login_required
def transfers_list():
    transfers = Transfer.query.filter_by(user_id=current_user.id)\
        .order_by(Transfer.date.desc()).all()
    return render_template('transfers.html', transfers=transfers)


@app.route('/transfer/add', methods=['GET', 'POST'])
@login_required
def add_transfer():
    if request.method == 'POST':
        from_account_id = int(request.form.get('from_account_id'))
        to_account_id = int(request.form.get('to_account_id'))
        
        if from_account_id == to_account_id:
            flash('Não é possível transferir para a mesma conta!', 'error')
            return redirect(url_for('add_transfer'))
        
        amount = float(request.form.get('amount'))
        
        # Criar transferência
        transfer = Transfer(
            user_id=current_user.id,
            from_account_id=from_account_id,
            to_account_id=to_account_id,
            amount=amount,
            date=datetime.strptime(request.form.get('date'), '%Y-%m-%d').date(),
            description=request.form.get('description'),
            notes=request.form.get('notes')
        )
        
        db.session.add(transfer)
        
        # Atualizar saldos
        from_account = Account.query.get(from_account_id)
        to_account = Account.query.get(to_account_id)
        
        from_account.current_balance -= amount
        to_account.current_balance += amount
        
        db.session.commit()
        
        flash('Transferência realizada com sucesso!', 'success')
        return redirect(url_for('transfers_list'))
    
    accounts = Account.query.filter_by(user_id=current_user.id, active=True).all()
    return render_template('add_transfer.html', accounts=accounts)


@app.route('/transfer/delete/<int:id>', methods=['POST'])
@login_required
def delete_transfer(id):
    transfer = Transfer.query.filter_by(id=id, user_id=current_user.id).first_or_404()
    
    # Reverter saldos
    from_account = Account.query.get(transfer.from_account_id)
    to_account = Account.query.get(transfer.to_account_id)
    
    from_account.current_balance += transfer.amount
    to_account.current_balance -= transfer.amount
    
    db.session.delete(transfer)
    db.session.commit()
    
    flash('Transferência excluída com sucesso!', 'success')
    return redirect(url_for('transfers_list'))


# ==================== CATEGORIAS ====================

@app.route('/categories')
@login_required
def categories():
    categories_list = Category.query.filter_by(user_id=current_user.id).order_by(Category.type, Category.name).all()
    return render_template('categories.html', categories=categories_list)


@app.route('/category/add', methods=['GET', 'POST'])
@login_required
def add_category():
    if request.method == 'POST':
        category = Category(
            user_id=current_user.id,
            name=request.form.get('name'),
            type=request.form.get('type'),
            color=request.form.get('color', '#6B7280'),
            icon=request.form.get('icon', 'tag')
        )
        
        db.session.add(category)
        db.session.commit()
        
        flash('Categoria adicionada com sucesso!', 'success')
        return redirect(url_for('categories'))
    
    return render_template('add_category.html')


@app.route('/category/edit/<int:id>', methods=['GET', 'POST'])
@login_required
def edit_category(id):
    category = Category.query.filter_by(id=id, user_id=current_user.id).first_or_404()
    
    if request.method == 'POST':
        category.name = request.form.get('name')
        category.type = request.form.get('type')
        category.color = request.form.get('color')
        category.icon = request.form.get('icon')
        
        db.session.commit()
        flash('Categoria atualizada com sucesso!', 'success')
        return redirect(url_for('categories'))
    
    return render_template('edit_category.html', category=category)


# ==================== RELATÓRIOS ====================

@app.route('/reports')
@login_required
def reports():
    today = datetime.today()
    
    # Últimos 6 meses de dados
    months_data = []
    for i in range(5, -1, -1):
        month_date = today - timedelta(days=30 * i)
        month = month_date.month
        year = month_date.year
        
        income = db.session.query(func.sum(Transaction.amount)).filter(
            Transaction.user_id == current_user.id,
            Transaction.type == 'income',
            extract('month', Transaction.date) == month,
            extract('year', Transaction.date) == year
        ).scalar() or 0
        
        expense = db.session.query(func.sum(Transaction.amount)).filter(
            Transaction.user_id == current_user.id,
            Transaction.type == 'expense',
            Transaction.account_id.isnot(None),
            extract('month', Transaction.date) == month,
            extract('year', Transaction.date) == year
        ).scalar() or 0
        
        # Parcelas pagas
        installments_paid = db.session.query(func.sum(Installment.amount)).filter(
            Installment.user_id == current_user.id,
            Installment.paid == True,
            extract('month', Installment.paid_date) == month,
            extract('year', Installment.paid_date) == year,
            Installment.account_id.isnot(None)
        ).scalar() or 0
        
        expense += installments_paid
        
        months_data.append({
            'month': month_date.strftime('%b/%Y'),
            'income': income,
            'expense': expense,
            'balance': income - expense
        })
    
    # Despesas por categoria (ano atual)
    category_expenses = db.session.query(
        Category.name,
        Category.color,
        func.sum(Transaction.amount).label('total')
    ).join(Transaction).filter(
        Transaction.user_id == current_user.id,
        Transaction.type == 'expense',
        extract('year', Transaction.date) == today.year
    ).group_by(Category.id).order_by(func.sum(Transaction.amount).desc()).all()
    
    total_expense = sum(cat.total for cat in category_expenses)
    
    category_data = []
    for cat in category_expenses:
        percentage = (cat.total / total_expense * 100) if total_expense > 0 else 0
        category_data.append({
            'name': cat.name,
            'color': cat.color,
            'total': cat.total,
            'percentage': percentage
        })
    
    # Comprometimento futuro por mês
    future_months = []
    for i in range(3):
        future_date = today + timedelta(days=30 * (i + 1))
        month = future_date.month
        year = future_date.year
        
        commitment = db.session.query(func.sum(Installment.amount)).filter(
            Installment.user_id == current_user.id,
            Installment.paid == False,
            extract('month', Installment.due_date) == month,
            extract('year', Installment.due_date) == year
        ).scalar() or 0
        
        future_months.append({
            'month': future_date.strftime('%b/%Y'),
            'amount': commitment
        })
    
    return render_template('reports.html',
                         months_data=months_data,
                         category_data=category_data,
                         future_months=future_months)


# ==================== FUNÇÕES AUXILIARES ====================

def create_default_categories(user_id):
    """Cria categorias padrão para novos usuários"""
    default_categories = [
        # Receitas
        {'name': 'Salário', 'type': 'income', 'color': '#10B981', 'icon': 'briefcase'},
        {'name': 'Freelance', 'type': 'income', 'color': '#3B82F6', 'icon': 'code'},
        {'name': 'Investimentos', 'type': 'income', 'color': '#8B5CF6', 'icon': 'trending-up'},
        {'name': 'Outras Receitas', 'type': 'income', 'color': '#6B7280', 'icon': 'dollar-sign'},
        
        # Despesas
        {'name': 'Alimentação', 'type': 'expense', 'color': '#EF4444', 'icon': 'shopping-cart'},
        {'name': 'Transporte', 'type': 'expense', 'color': '#F59E0B', 'icon': 'car'},
        {'name': 'Moradia', 'type': 'expense', 'color': '#8B5CF6', 'icon': 'home'},
        {'name': 'Saúde', 'type': 'expense', 'color': '#EC4899', 'icon': 'heart'},
        {'name': 'Educação', 'type': 'expense', 'color': '#3B82F6', 'icon': 'book'},
        {'name': 'Lazer', 'type': 'expense', 'color': '#10B981', 'icon': 'smile'},
        {'name': 'Contas', 'type': 'expense', 'color': '#6B7280', 'icon': 'file-text'},
        {'name': 'Outras Despesas', 'type': 'expense', 'color': '#6B7280', 'icon': 'more-horizontal'},
    ]
    
    for cat_data in default_categories:
        category = Category(user_id=user_id, **cat_data)
        db.session.add(category)
    
    db.session.commit()


if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(host='0.0.0.0', port=5000, debug=True)
    #app.run(debug=True)
