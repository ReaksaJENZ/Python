from flask import Blueprint, render_template, request, redirect, url_for, session, flash
from utils import allowed_file, send_telegram_message
import sqlite3
import os
from werkzeug.utils import secure_filename

routes_bp = Blueprint('routes_bp', __name__)

@routes_bp.route('/admin/add_product', methods=['GET', 'POST'])
def add_product():
    if request.method == 'POST':
        title = request.form.get('title', '').strip()
        description = request.form.get('details', '').strip()
        price = request.form.get('price', '').strip()
        category = request.form.get('category', '').strip()
        image = request.files.get('image')
        image_url = request.form.get('image_url', '').strip()

        # Validate required fields (except image)
        if not title or not description or not price or not category:
            flash('All fields except image are required.', 'danger')
            return render_template('admin/add_product.html')

        image_filename = None
        if image_url:
            image_filename = image_url
        elif image and image.filename:
            if not allowed_file(image.filename):
                flash('Invalid image file type. Allowed: png, jpg, jpeg, gif.', 'danger')
                return render_template('admin/add_product.html')
            image_filename = secure_filename(image.filename)
            image_path = os.path.join(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'static', 'images'), image_filename)
            try:
                image.save(image_path)
            except Exception as e:
                flash(f'Image upload failed: {e}', 'danger')
                return render_template('admin/add_product.html')
        else:
            image_filename = ''

        try:
            conn = sqlite3.connect('su79_database.sqlite3')
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO products (title, price, description, image, category) VALUES (?, ?, ?, ?, ?)",
                (title, price, description, image_filename, category)
            )
            conn.commit()
            conn.close()
            flash('Product added successfully!', 'success')
            return redirect(url_for('routes_bp.add_product'))
        except Exception as e:
            import traceback
            print('DB Insert Error:', traceback.format_exc())
            flash(f'Failed to add product: {e}', 'danger')
            return render_template('admin/add_product.html')

    return render_template('admin/add_product.html')

@routes_bp.route('/checkout', methods=['GET', 'POST'])
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

        # Only show first item for summary
        item = cart[0]
        img_src = item['image'] if item['image'].startswith('http') else '/static/images/' + item['image']

        # Save order data for invoice
        session['last_order'] = {
            'cart': cart,
            'total': total,
            'shipping': shipping,
            'tax': tax,
            'grand_total': grand_total,
            'customer_name': customer_name,
            'customer_email': customer_email,
            'customer_phone': customer_phone
        }

        # Send Telegram notification (optional)
        send_telegram_message(
            f"\U0001F6D2 New Order by {customer_name}\n"
            f"\U0001F4E7 {customer_email}\n\U0001F4DE {customer_phone}\n\U0001F4B5 Total: ${grand_total}"
        )

        # Clear cart after order
        session.pop('cart', None)

        flash('Order placed and Telegram notification sent!', 'success')
        return redirect(url_for('routes_bp.cart'))

    return render_template('checkout.html', cart=cart, total=total)

@routes_bp.route('/')
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

@routes_bp.route('/add-to-cart', methods=['POST'])
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
    return redirect(url_for('routes_bp.cart'))

@routes_bp.route('/cart')
def cart():
    cart = session.get('cart', [])
    total = sum(item['price'] * item['quantity'] for item in cart)
    # In your cart.html, use /static/images/{{ item.image }} for the image src
    return render_template('cart.html', cart=cart, total=total, cart_total=total)

@routes_bp.route('/update-cart', methods=['POST'])
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
    return redirect(url_for('routes_bp.cart'))

@routes_bp.route('/remove-item', methods=['POST'])
def remove_item():
    product_id = request.form.get('id')

    cart = session.get('cart', [])
    cart = [item for item in cart if item['id'] != product_id]
    session['cart'] = cart
    return redirect(url_for('routes_bp.cart'))

@routes_bp.route('/clear-cart')
def clear_cart():
    session.pop('cart', None)
    return redirect(url_for('routes_bp.cart'))

@routes_bp.route('/login', methods=['GET', 'POST'])
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
            return redirect(url_for('routes_bp.add_product'))  # Redirect to add product page
        else:
            flash('Invalid username or password', 'danger')
            return render_template('admin/login.html')

    return render_template('admin/login.html')

@routes_bp.route('/logout')
def logout():
    session.clear()
    flash('Logged out successfully', 'success')
    return redirect(url_for('routes_bp.login'))

@routes_bp.route('/admin')
def admin():
    if 'user_id' not in session:
        flash('You must log in first', 'warning')
        return redirect(url_for('routes_bp.login'))

    conn = sqlite3.connect('su79_database.sqlite3')
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM products")
    products = cursor.fetchall()
    conn.close()

    products_list = [dict(p) for p in products]
    # In your admin/index.html, use /static/images/{{ product.image }} for the image src
    return render_template('admin/index.html', products=products_list)
