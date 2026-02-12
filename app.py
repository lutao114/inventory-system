import os
import sqlite3
import shutil
from datetime import datetime, timedelta
from flask import Flask, render_template, request, redirect, url_for, flash, session, send_from_directory, make_response
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from functools import wraps
from openpyxl import Workbook
from openpyxl.styles import Font, Alignment

app = Flask(__name__)
app.secret_key = 'your-strong-secret-key-change-in-production'
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['BACKUP_FOLDER'] = 'backups'
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
os.makedirs(app.config['BACKUP_FOLDER'], exist_ok=True)

DATABASE = 'inventory.db'


def get_db():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    """初始化数据库：创建表 + 插入默认 admin 用户"""
    with get_db() as conn:
        # 创建 items 表
        conn.execute('''
            CREATE TABLE IF NOT EXISTS items (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                brand TEXT NOT NULL,
                model TEXT NOT NULL,
                quantity INTEGER NOT NULL DEFAULT 0,
                remark TEXT
            )
        ''')

        # 创建 users 表
        conn.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL
            )
        ''')

        # 如果 users 表为空，插入默认用户
        cur = conn.execute('SELECT COUNT(*) FROM users')
        if cur.fetchone()[0] == 0:
            pwd_hash = generate_password_hash('admin123')
            conn.execute("INSERT INTO users (username, password_hash) VALUES ('admin', ?)", (pwd_hash,))

        # 创建 stock_logs 表
        conn.execute('''
            CREATE TABLE IF NOT EXISTS stock_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                action TEXT NOT NULL,
                item_id INTEGER NOT NULL,
                item_name TEXT NOT NULL,
                item_brand TEXT NOT NULL,
                item_model TEXT NOT NULL,
                quantity INTEGER NOT NULL,
                operation_date TEXT NOT NULL,
                delivery_company TEXT,
                tracking_number TEXT,
                install_location TEXT,
                remark TEXT,
                photo_path TEXT,
                operator TEXT NOT NULL,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        conn.commit()


def ensure_database_initialized():
    """确保数据库文件和所有表都存在，否则重建"""
    if not os.path.exists(DATABASE):
        init_db()
        return

    # 检查 users 表是否存在（通过 sqlite_master）
    try:
        with sqlite3.connect(DATABASE) as conn:
            cur = conn.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='users'")
            if not cur.fetchone():
                raise sqlite3.OperationalError("users table missing")
    except sqlite3.OperationalError:
        # 表缺失或数据库损坏，重建
        try:
            os.remove(DATABASE)
        except FileNotFoundError:
            pass
        init_db()


# >>>>>>>>>> 执行数据库初始化（只在模块加载时运行一次） <<<<<<<<<<
ensure_database_initialized()
# >>>>>>>>>> 结束 <<<<<<<<<<


def backup_database():
    today = datetime.now().strftime("%Y%m%d")
    backup_file = os.path.join(app.config['BACKUP_FOLDER'], f"inventory_{today}.db")
    if not os.path.exists(backup_file):
        shutil.copy2(DATABASE, backup_file)
        cutoff = datetime.now() - timedelta(days=7)
        for fname in os.listdir(app.config['BACKUP_FOLDER']):
            if fname.startswith("inventory_") and fname.endswith(".db"):
                try:
                    date_str = fname[11:19]
                    file_date = datetime.strptime(date_str, "%Y%m%d")
                    if file_date < cutoff:
                        os.remove(os.path.join(app.config['BACKUP_FOLDER'], fname))
                except Exception:
                    pass


def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user' not in session:
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        with get_db() as conn:
            cur = conn.execute('SELECT * FROM users WHERE username = ?', (username,))
            user = cur.fetchone()
        if user and check_password_hash(user['password_hash'], password):
            session['user'] = username
            flash('登录成功！', 'success')
            return redirect(url_for('index'))
        else:
            flash('用户名或密码错误！', 'danger')
    return render_template('login.html')


@app.route('/logout')
def logout():
    session.pop('user', None)
    flash('已退出登录', 'info')
    return redirect(url_for('login'))


@app.route('/change_password', methods=['GET', 'POST'])
@login_required
def change_password():
    if request.method == 'POST':
        old = request.form['old_password']
        new = request.form['new_password']
        confirm = request.form['confirm_password']
        if not (old and new and confirm):
            flash('请填写所有字段', 'danger')
            return redirect(url_for('change_password'))
        if new != confirm:
            flash('新密码与确认密码不一致', 'danger')
            return redirect(url_for('change_password'))
        with get_db() as conn:
            cur = conn.execute('SELECT password_hash FROM users WHERE username = ?', (session['user'],))
            user = cur.fetchone()
            if not check_password_hash(user['password_hash'], old):
                flash('原密码错误', 'danger')
                return redirect(url_for('change_password'))
            new_hash = generate_password_hash(new)
            conn.execute('UPDATE users SET password_hash = ? WHERE username = ?', (new_hash, session['user']))
            conn.commit()
        flash('密码修改成功！请重新登录', 'success')
        session.pop('user', None)
        return redirect(url_for('login'))
    return render_template('change_password.html')


@app.route('/')
@login_required
def index():
    return redirect(url_for('inventory'))


@app.route('/in', methods=['GET', 'POST'])
@login_required
def stock_in():
    if request.method == 'POST':
        name = request.form['name'].strip()
        brand = request.form['brand'].strip()
        model = request.form['model'].strip()
        quantity = int(request.form['quantity'])
        operation_date = request.form['operation_date']
        delivery_company = request.form.get('delivery_company', '').strip()
        tracking_number = request.form.get('tracking_number', '').strip()
        remark = request.form.get('remark', '').strip()

        with get_db() as conn:
            cur = conn.execute(
                'SELECT * FROM items WHERE name = ? AND brand = ? AND model = ?',
                (name, brand, model)
            )
            item = cur.fetchone()
            if item:
                new_qty = item['quantity'] + quantity
                conn.execute(
                    'UPDATE items SET quantity = ? WHERE id = ?',
                    (new_qty, item['id'])
                )
                item_id = item['id']
            else:
                conn.execute(
                    'INSERT INTO items (name, brand, model, quantity, remark) VALUES (?, ?, ?, ?, ?)',
                    (name, brand, model, quantity, remark)
                )
                item_id = cur.lastrowid
                new_qty = quantity

            conn.execute('''
                INSERT INTO stock_logs (
                    action, item_id, item_name, item_brand, item_model,
                    quantity, operation_date, delivery_company, tracking_number,
                    install_location, remark, photo_path, operator
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                'in', item_id, name, brand, model, quantity, operation_date,
                delivery_company, tracking_number, None, remark, None, session['user']
            ))
            conn.commit()
        flash(f'入库成功！当前库存：{new_qty}', 'success')
        return redirect(url_for('stock_in'))
    return render_template('in.html')

# ===== 新增：用于出库页面的级联下拉数据 API =====

@app.route('/api/names')
@login_required
def get_names():
    """获取所有唯一的设备名称"""
    with get_db() as conn:
        rows = conn.execute('SELECT DISTINCT name FROM items ORDER BY name').fetchall()
    names = [row['name'] for row in rows]
    return {'names': names}

@app.route('/api/brands/<name>')
@login_required
def get_brands(name):
    """根据设备名称获取品牌列表"""
    with get_db() as conn:
        rows = conn.execute(
            'SELECT DISTINCT brand FROM items WHERE name = ? ORDER BY brand',
            (name,)
        ).fetchall()
    brands = [row['brand'] for row in rows]
    return {'brands': brands}

@app.route('/api/models/<name>/<brand>')
@login_required
def get_models(name, brand):
    """根据名称和品牌获取型号列表"""
    with get_db() as conn:
        rows = conn.execute(
            'SELECT DISTINCT model FROM items WHERE name = ? AND brand = ? ORDER BY model',
            (name, brand)
        ).fetchall()
    models = [row['model'] for row in rows]
    return {'models': models}

@app.route('/api/item/<name>/<brand>/<model>')
@login_required
def get_item_info(name, brand, model):
    """获取具体设备的库存信息"""
    with get_db() as conn:
        item = conn.execute(
            'SELECT id, quantity, remark FROM items WHERE name = ? AND brand = ? AND model = ?',
            (name, brand, model)
        ).fetchone()
    if item:
        return {
            'id': item['id'],
            'quantity': item['quantity'],
            'remark': item['remark']
        }
    else:
        return {'error': '设备不存在'}, 404

@app.route('/out', methods=['GET', 'POST'])
@login_required
def stock_out():
    if request.method == 'POST':
        name = request.form['name'].strip()
        brand = request.form['brand'].strip()
        model = request.form['model'].strip()
        quantity = int(request.form['quantity'])
        operation_date = request.form['operation_date']
        install_location = request.form.get('install_location', '').strip()
        remark = request.form.get('remark', '').strip()
        photo = request.files.get('photo')
        photo_path = None
        if photo and photo.filename:
            filename = secure_filename(photo.filename)
            timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
            ext = filename.rsplit('.', 1)[-1] if '.' in filename else 'jpg'
            save_name = f"out_{timestamp}.{ext}"
            photo.save(os.path.join(app.config['UPLOAD_FOLDER'], save_name))
            photo_path = f"uploads/{save_name}"

        with get_db() as conn:
            cur = conn.execute(
                'SELECT * FROM items WHERE name = ? AND brand = ? AND model = ?',
                (name, brand, model)
            )
            item = cur.fetchone()
            if not item:
                flash('该设备不存在，请先入库！', 'danger')
                return redirect(url_for('stock_out'))
            if item['quantity'] < quantity:
                flash(f'库存不足！当前仅剩 {item["quantity"]} 件', 'danger')
                return redirect(url_for('stock_out'))
            new_qty = item['quantity'] - quantity
            conn.execute(
                'UPDATE items SET quantity = ? WHERE id = ?',
                (new_qty, item['id'])
            )
            conn.execute('''
                INSERT INTO stock_logs (
                    action, item_id, item_name, item_brand, item_model,
                    quantity, operation_date, delivery_company, tracking_number,
                    install_location, remark, photo_path, operator
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                'out', 
                item['id'], 
                name, 
                brand, 
                model, 
                quantity, 
                operation_date,
                None,  # delivery_company
                None,  # tracking_number
                install_location,
                remark,
                photo_path,
                session['user']
            ))
            conn.commit()
        flash(f'出库成功！剩余库存：{new_qty}', 'success')
        return redirect(url_for('stock_out'))
    return render_template('out.html')


@app.route('/inventory')
@login_required
def inventory():
    search = request.args.get('search', '').strip()
    
    with get_db() as conn:
        if search:
            query = '''
                SELECT id, name, brand, model, quantity, remark
                FROM items
                WHERE name LIKE ? OR model LIKE ?
                ORDER BY name, brand, model
            '''
            params = (f'%{search}%', f'%{search}%')
            items = conn.execute(query, params).fetchall()
        else:
            query = '''
                SELECT id, name, brand, model, quantity, remark
                FROM items
                ORDER BY name, brand, model
            '''
            items = conn.execute(query).fetchall()
    
    return render_template('inventory.html', items=items, search=search)


@app.route('/edit/<int:item_id>', methods=['GET', 'POST'])
@login_required
def edit(item_id):
    with get_db() as conn:
        item = conn.execute('SELECT * FROM items WHERE id = ?', (item_id,)).fetchone()
        if not item:
            flash('设备不存在！', 'danger')
            return redirect(url_for('inventory'))
        if request.method == 'POST':
            name = request.form['name'].strip()
            brand = request.form['brand'].strip()
            model = request.form['model'].strip()
            remark = request.form.get('remark', '').strip()
            conn.execute(
                'UPDATE items SET name = ?, brand = ?, model = ?, remark = ? WHERE id = ?',
                (name, brand, model, remark, item_id)
            )
            conn.commit()
            flash('设备信息更新成功！', 'success')
            return redirect(url_for('inventory'))
    return render_template('edit.html', item=item)


@app.route('/logs')
@login_required
def logs():
    action_filter = request.args.get('action', '')
    name_filter = request.args.get('name', '').strip()
    
    query = "SELECT * FROM stock_logs WHERE 1=1"
    params = []
    if action_filter in ['in', 'out']:
        query += " AND action = ?"
        params.append(action_filter)
    if name_filter:
        query += " AND item_name LIKE ?"
        params.append(f'%{name_filter}%')
    query += " ORDER BY timestamp DESC LIMIT 200"
    
    with get_db() as conn:
        log_list = conn.execute(query, params).fetchall()
    return render_template('logs.html', logs=log_list, action_filter=action_filter, name_filter=name_filter)


@app.route('/export_inventory')
@login_required
def export_inventory():
    wb = Workbook()
    ws = wb.active
    ws.title = "库存清单"
    
    headers = ["ID", "设备名称", "品牌", "型号", "数量", "备注"]
    ws.append(headers)
    for cell in ws[1]:
        cell.font = Font(bold=True)
        cell.alignment = Alignment(horizontal="center")
    
    with get_db() as conn:
        items = conn.execute('SELECT * FROM items ORDER BY name, brand, model').fetchall()
    for item in items:
        ws.append([
            item['id'],
            item['name'],
            item['brand'],
            item['model'],
            item['quantity'],
            item['remark'] or ''
        ])
    
    for col in ws.columns:
        max_length = 0
        column = col[0].column_letter
        for cell in col:
            try:
                if len(str(cell.value)) > max_length:
                    max_length = len(str(cell.value))
            except:
                pass
        adjusted_width = min(max_length + 2, 50)
        ws.column_dimensions[column].width = adjusted_width

    from io import BytesIO
    output = BytesIO()
    wb.save(output)
    output.seek(0)
    response = make_response(output.read())
    response.headers["Content-Disposition"] = f"attachment; filename=inventory_{datetime.now().strftime('%Y%m%d')}.xlsx"
    response.headers["Content-type"] = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    return response


@app.route('/backup_db')
@login_required
def backup_db():
    backup_database()
    flash('数据库已备份！', 'success')
    return redirect(url_for('logs'))


@app.route('/uploads/<filename>')
def uploaded_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)


if __name__ == '__main__':
    # 开发模式下也确保初始化
    ensure_database_initialized()
    backup_database()
    app.run(host='0.0.0.0', port=8000, debug=True)