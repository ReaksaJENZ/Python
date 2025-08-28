import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from flask import Flask, render_template, request, redirect, url_for, session, flash
import requests
import sqlite3
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.secret_key = "741e4fa4-f067-4aec-b48d-deb18e9cca92"

# Image upload config
UPLOAD_FOLDER = os.path.join('static', 'images')
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


# Set upload folder for product images
UPLOAD_FOLDER = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'static', 'images')
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Admin add product route
@app.route('/admin/add_product', methods=['GET', 'POST'])
def add_product():
    if request.method == 'POST':
        title = request.form.get('title', '').strip()
        details = request.form.get('details', '').strip()
        price = request.form.get('price', '').strip()
        category = request.form.get('category', '').strip()
        image = request.files.get('image')
        image_url = request.form.get('image_url', '').strip()

        # Validate required fields (except image)
        if not title or not details or not price or not category:
            flash('All fields except image are required.', 'danger')
            return render_template('admin/add_product.html')

        image_filename = None
        # Prefer file upload if present
        if image and image.filename:
            if not allowed_file(image.filename):
                flash('Invalid image file type. Allowed: png, jpg, jpeg, gif.', 'danger')
                return render_template('admin/add_product.html')
            image_filename = secure_filename(image.filename)
            image_path = os.path.join(app.config['UPLOAD_FOLDER'], image_filename)
            try:
                image.save(image_path)
            except Exception as e:
                flash(f'Image upload failed: {e}', 'danger')
                return render_template('admin/add_product.html')
        elif image_url:
            image_filename = image_url
        else:
            flash('Please provide an image file or an image URL.', 'danger')
            return render_template('admin/add_product.html')

        # Save product to database
        try:
            conn = sqlite3.connect('su79_database.sqlite3')
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO products (title, price, description, image, category) VALUES (?, ?, ?, ?, ?)",
                (title, price, details, image_filename, category)
            )
            conn.commit()
            conn.close()
            flash('Product added successfully!', 'success')
            return redirect(url_for('add_product'))
        except Exception as e:
            import traceback
            print('DB Insert Error:', traceback.format_exc())
            flash(f'Failed to add product: {e}', 'danger')
            return render_template('admin/add_product.html')

    return render_template('admin/add_product.html')

BOT_TOKEN = "7691569932:AAFwVvML6mxYSGFuXIpNX0KIWV7fMa669aw"
CHAT_ID = "@koko2_168"


EMAIL_HOST = 'smtp.gmail.com'
EMAIL_PORT = 587
EMAIL_HOST_USER = 'your_email@gmail.com'  # Change to your email
EMAIL_HOST_PASSWORD = 'your_email_password'  # Change to your app password
EMAIL_RECEIVER = 'receiver_email@gmail.com'  # Change to receiver email


def send_telegram_message(message):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    data = {"chat_id": CHAT_ID, "text": message, "parse_mode": "HTML"}
    try:
        requests.post(url, data=data)
    except Exception as e:
        print("Telegram send error:", e)

# --- Helper: Send Email ---
def send_email(subject, body, to=None):
    msg = MIMEMultipart('alternative')
    msg['From'] = EMAIL_HOST_USER
    msg['To'] = to if to else EMAIL_RECEIVER
    msg['Subject'] = subject
    msg.attach(MIMEText(body, 'html'))
    try:
        server = smtplib.SMTP(EMAIL_HOST, EMAIL_PORT)
        server.starttls()
        server.login(EMAIL_HOST_USER, EMAIL_HOST_PASSWORD)
        server.sendmail(EMAIL_HOST_USER, msg['To'], msg.as_string())
        server.quit()
    except Exception as e:
        print("Email send error:", e)
# Add after clear_cart and before login


@app.route('/checkout', methods=['GET', 'POST'])
def checkout():
        cart = session.get('cart', [])
        total = sum(item['price'] * item['quantity'] for item in cart)
        if request.method == 'POST' and cart:
                customer_name = request.form.get('customer_name', '').strip()
                customer_email = request.form.get('customer_email', '').strip()
                customer_phone = request.form.get('customer_phone', '').strip()
                if not customer_name or not customer_email or not customer_phone:
                        flash('Please fill in all customer details.', 'danger')
                        return render_template('checkout.html', cart=cart, total=total)

                shipping = 4.95
                tax = round(total * 0.085, 2)
                grand_total = total + shipping + tax
                # Only show first item for summary (like screenshot)
                item = cart[0]
                img_src = item['image'] if item['image'].startswith('http') else '/static/images/' + item['image']
                order_html = f"""
<div style='font-family:sans-serif;max-width:500px;margin:auto;'>
    <h3 style='text-align:center;margin-bottom:16px;border-bottom:1px solid #eee;padding-bottom:8px;'>Your Order Summary</h3>
    <div style='display:flex;align-items:flex-start;margin-bottom:18px;'>
        <img src='{img_src}' style='width:110px;border-radius:8px;margin-right:18px;'>
        <div style='flex:1;'>
            <b>{item['title']}</b><br>
            Size: {item.get('size', '-') if 'size' in item else '-'}<br>
            Color: {item.get('color', '-') if 'color' in item else '-'}<br>
            Quantity: {item['quantity']}<br>
        </div>
        <div style='font-weight:bold;font-size:1.1em;'>${item['price']*item['quantity']:.2f}</div>
    </div>
    <table style='width:100%;font-size:1.1em;margin-bottom:18px;'>
        <tr><td>Subtotal</td><td style='text-align:right;'>${total:.2f}</td></tr>
        <tr><td>Shipping</td><td style='text-align:right;'>${shipping:.2f}</td></tr>
        <tr><td>Tax</td><td style='text-align:right;'>${tax:.2f}</td></tr>
        <tr style='font-weight:bold;font-size:1.2em;'><td>Total</td><td style='text-align:right;'>${grand_total:.2f}</td></tr>
    </table>
    <div style='font-size:1em;margin-bottom:8px;'><b>Name:</b> {customer_name}<br><b>Email:</b> {customer_email}<br><b>Phone:</b> {customer_phone}</div>
</div>
                """
                # Send Telegram notification
                # List all product names in the order
                product_names = ', '.join([item['title'] for item in cart])
                message = (
                    f"🛒 New Order by {customer_name}\n"
                    f"🛍️ Product(s): {product_names}\n"
                    f"📧 {customer_email}\n📞 {customer_phone}\n"
                    f"💵 Total: ${grand_total:.2f}"
                )
                send_telegram_message(message)
                session.pop('cart', None)
                return render_template('checkout.html', success=True)
        return render_template('checkout.html', cart=cart, total=total)


# Protect admin routes
@app.before_request
def protect_admin_routes():
    protected_paths = ['/admin', '/product']
    if any(request.path.startswith(p) for p in protected_paths) and not session.get('user_id'):
        flash('You must log in first', 'warning')
        return redirect(url_for('login'))
    return None

@app.route('/')
def home():
    products = []
    try:
        conn = sqlite3.connect('su79_database.sqlite3')
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM products")
        products = [dict(row) for row in cursor.fetchall()]
        conn.close()
    except Exception as e:
        print("Error fetching data from database:", e)
    # Each product's image is just the filename, use /static/images/<filename> in template
    return render_template('home.html', products=products)

@app.route('/add-to-cart', methods=['POST'])
def add_to_cart():
    product_id = request.form.get('id')
    title = request.form.get('title')
    price = float(request.form.get('price'))

    # Fetch image from database
    conn = sqlite3.connect('su79_database.sqlite3')
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute("SELECT image FROM products WHERE id=?", (product_id,))
    row = cursor.fetchone()
    image = row['image'] if row and 'image' in row.keys() else 'default.jpg'
    conn.close()

    cart = session.get('cart', [])

    for item in cart:
        if item['id'] == product_id:
            item['quantity'] += 1
            break
    else:
        cart.append({'id': product_id, 'title': title, 'price': price, 'quantity': 1, 'image': image})

    session['cart'] = cart
    return redirect(url_for('cart'))

@app.route('/cart')
def cart():
    cart = session.get('cart', [])
    total = sum(item['price'] * item['quantity'] for item in cart)
    # In your cart.html, use /static/images/{{ item.image }} for the image src
    return render_template('cart.html', cart=cart, total=total, cart_total=total)

@app.route('/update-cart', methods=['POST'])
def update_cart():
    product_id = request.form.get('id')
    action = request.form.get('action')

    cart = session.get('cart', [])

    for item in cart:
        if item['id'] == product_id:
            if action == 'increase':
                item['quantity'] += 1
            elif action == 'decrease':
                item['quantity'] -= 1
                if item['quantity'] <= 0:
                    cart.remove(item)
            break

    session['cart'] = cart
    return redirect(url_for('cart'))

@app.route('/remove-item', methods=['POST'])
def remove_item():
    product_id = request.form.get('id')

    cart = session.get('cart', [])
    cart = [item for item in cart if item['id'] != product_id]
    session['cart'] = cart
    return redirect(url_for('cart'))

@app.route('/clear-cart')
def clear_cart():
    session.pop('cart', None)
    return redirect(url_for('cart'))


# Login route
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')

        conn = sqlite3.connect('su79_database.sqlite3')
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM admin WHERE username=? AND password=?", (username, password))
        user = cursor.fetchone()
        conn.close()

        if user:
            session['user_id'] = user['id']
            session['username'] = user['username']
            return redirect(url_for('add_product'))  # Redirect to add product page
        else:
            flash('Invalid username or password', 'danger')
            return render_template('admin/login.html')

    return render_template('admin/login.html')

# Logout route
@app.route('/logout')
def logout():
    session.clear()
    flash('Logged out successfully', 'success')
    return redirect(url_for('login'))

# Admin dashboard
@app.route('/admin')
def admin():
    if 'user_id' not in session:
        flash('You must log in first', 'warning')
        return redirect(url_for('login'))

    conn = sqlite3.connect('su79_database.sqlite3')
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM products")
    products = cursor.fetchall()
    conn.close()
    products_list = [dict(p) for p in products]
    # In your admin/index.html, use /static/images/{{ product.image }} for the image src
    return render_template('admin/index.html', products=products_list)

if __name__ == '__main__':
    app.run(debug=True)