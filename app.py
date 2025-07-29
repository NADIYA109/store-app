from flask import Flask, render_template, request, redirect
from db_config import app, mysql

@app.route('/')
def home():
    return redirect('/item')

# Add Item
@app.route('/item', methods=['GET', 'POST'])
def item():
    error = None
    success = None
    cur = mysql.connection.cursor()

    if request.method == 'POST':
        name = request.form['name'].strip()
        type_ = request.form['type'].strip()
        price = request.form['price'].strip()

        #Backend validation
        if not name or not type_ or not price:
            error = "All fields are required."
        else:
            try:
                price = float(price)
                cur.execute("INSERT INTO items(name, type, price) VALUES(%s, %s, %s)", (name, type_, price))
                mysql.connection.commit()
                success = "Item added successfully!"
            except Exception as e:
                error = f"Something went wrong: {str(e)}"

    cur.execute("SELECT * FROM items")
    items = cur.fetchall()
    cur.close()
    return render_template('item_form.html', items=items, error=error, success=success)


#Edit Item 
@app.route('/item/edit/<int:item_id>', methods=['GET', 'POST'])
def edit_item(item_id):
    error = None
    cur = mysql.connection.cursor()

    if request.method == 'POST':
        name = request.form['name'].strip()
        type_ = request.form['type'].strip()
        price = request.form['price'].strip()

        if not name or not type_ or not price:
            error = "All fields are required."
        else:
            try:
                price = float(price)
                cur.execute("""
                    UPDATE items 
                    SET name = %s, type = %s, price = %s 
                    WHERE item_id = %s
                """, (name, type_, price, item_id))
                mysql.connection.commit()
                cur.close()
                return redirect('/item')
            except Exception as e:
                error = f"Update failed: {str(e)}"

    # GET request → fetch item to edit
    cur.execute("SELECT * FROM items WHERE item_id = %s", (item_id,))
    item = cur.fetchone()
    cur.close()
    return render_template('edit_item.html', item=item, error=error)


#Delete Item
@app.route('/item/delete/<int:item_id>')
def delete_item(item_id):
    cur = mysql.connection.cursor()
    try:
        # Step 1: Delete from purchase_items where this item is used
        cur.execute("DELETE FROM purchase_items WHERE item_id = %s", (item_id,))

        # Step 2: Delete from inventory where this item is stored
        cur.execute("DELETE FROM inventory WHERE item_id = %s", (item_id,))

        # Step 3: Now delete from items table
        cur.execute("DELETE FROM items WHERE item_id = %s", (item_id,))
        
        mysql.connection.commit()
    except Exception as e:
        mysql.connection.rollback()
        return f"Error while deleting item: {str(e)}"
    finally:
        cur.close()
    return redirect('/item')




# Add Inventory
@app.route('/inventory', methods=['GET', 'POST'])
def inventory():
    error = None
    success = None
    cur = mysql.connection.cursor()

    # fetch item dropdown
    cur.execute("SELECT item_id, name FROM items")
    items = cur.fetchall()

    if request.method == 'POST':
        item_id = request.form['item_id']
        quantity = request.form['quantity'].strip()

        if not item_id or not quantity:
            error = "All fields are required."
        else:
            try:
                quantity = int(quantity)
                if quantity <= 0:
                    error = "Quantity must be a positive number."
                else:
                    cur.execute("INSERT INTO inventory (item_id, quantity_available) VALUES (%s, %s)", (item_id, quantity))
                    mysql.connection.commit()
                    success = "Inventory added successfully!"
            except Exception as e:
                error = f"Something went wrong: {str(e)}"

    # fetch all inventory for display
    cur.execute("""
        SELECT i.inventory_id, it.name, i.quantity_available 
        FROM inventory i
        JOIN items it ON i.item_id = it.item_id
    """)
    inventory = cur.fetchall()
    cur.close()

    return render_template('inventory_form.html', items=items, inventory=inventory, error=error, success=success)


# Edit Inventory
@app.route('/inventory/edit/<int:inventory_id>', methods=['GET', 'POST'])
def edit_inventory(inventory_id):
    error = None
    cur = mysql.connection.cursor()

    if request.method == 'POST':
        item_id = request.form['item_id']
        quantity = request.form['quantity'].strip()

        if not item_id or not quantity:
            error = "All fields are required."
        else:
            try:
                quantity = int(quantity)
                if quantity <= 0:
                    error = "Quantity must be a positive number."
                else:
                    cur.execute("""
                        UPDATE inventory 
                        SET item_id = %s, quantity_available = %s 
                        WHERE inventory_id = %s
                    """, (item_id, quantity, inventory_id))
                    mysql.connection.commit()
                    cur.close()
                    return redirect('/inventory')
            except Exception as e:
                error = f"Update failed: {str(e)}"

    # GET → fetch current item
    cur.execute("SELECT * FROM inventory WHERE inventory_id = %s", (inventory_id,))
    current_item = cur.fetchone()

    # fetch all items for dropdown
    cur.execute("SELECT item_id, name FROM items")
    items = cur.fetchall()
    cur.close()

    return render_template("edit_inventory.html", current_item=current_item, items=items, error=error)


# Delete Inventory
@app.route('/inventory/delete/<int:inventory_id>')
def delete_inventory(inventory_id):
    cur = mysql.connection.cursor()
    cur.execute("DELETE FROM inventory WHERE inventory_id = %s", (inventory_id,))
    mysql.connection.commit()
    cur.close()
    return redirect('/inventory')



# Add Purchase with inventory update
from datetime import date
@app.route('/purchase', methods=['GET', 'POST'])
def purchase():
    error = None
    success = None
    cur = mysql.connection.cursor()

    cur.execute("SELECT item_id, name FROM items")
    items = cur.fetchall()

    if request.method == 'POST':
        item_ids = request.form.getlist('item_id')
        quantities = request.form.getlist('quantity')

        if not item_ids or not quantities or len(item_ids) != len(quantities):
            error = "Please select items and provide quantities."
        else:
            try:
                for item_id, qty in zip(item_ids, quantities):
                    if not item_id or not qty:
                        raise Exception("All selected items must have quantity.")
                    qty_int = int(qty)
                    if qty_int <= 0:
                        raise Exception("Quantity must be a positive number.")
                    cur.execute("SELECT i.name, iv.quantity_available FROM items i LEFT JOIN inventory iv ON i.item_id = iv.item_id WHERE i.item_id = %s", (item_id,))
                    result = cur.fetchone()
                    if not result or qty_int > result[1]:
                        raise Exception(f"Only {result[1]} '{result[0]}' in stock. Please adjust quantity.")
                cur.execute("INSERT INTO purchase (purchase_date) VALUES (%s)", (date.today(),))
                purchase_id = cur.lastrowid

                for item_id, qty in zip(item_ids, quantities):
                    qty_int = int(qty)
                    cur.execute(
                        "INSERT INTO purchase_items (purchase_id, item_id, quantity) VALUES (%s, %s, %s)",
                        (purchase_id, item_id, qty_int)
                    )
                    cur.execute("UPDATE inventory SET quantity_available = quantity_available - %s WHERE item_id = %s",
                                (qty_int, item_id))

                mysql.connection.commit()
                success = "Purchase saved successfully and inventory updated!"
            except Exception as e:
                mysql.connection.rollback()
                error = f"Something went wrong: {str(e)}"

    cur.execute("SELECT purchase_id, purchase_date FROM purchase")
    purchases = cur.fetchall()
    cur.close()
    return render_template('purchase_form.html', items=items, purchases=purchases, error=error, success=success)

# Edit Purchase
@app.route('/purchase/edit/<int:purchase_id>', methods=['GET', 'POST'])
def edit_purchase(purchase_id):
    error = None
    success = None
    cur = mysql.connection.cursor()

    if request.method == 'POST':
        item_ids = request.form.getlist('item_id')
        quantities = request.form.getlist('quantity')

        if not item_ids or not quantities or len(item_ids) != len(quantities):
            error = "Please select at least one item and provide valid quantities."
        else:
            try:
                stock_errors = []

                # Reverse the previous purchase from inventory
                cur.execute("SELECT item_id, quantity FROM purchase_items WHERE purchase_id = %s", (purchase_id,))
                previous_items = cur.fetchall()
                for item_id, qty in previous_items:
                    cur.execute("UPDATE inventory SET quantity_available = quantity_available + %s WHERE item_id = %s", (qty, item_id))

                # Delete old purchase_items first
                cur.execute("DELETE FROM purchase_items WHERE purchase_id = %s", (purchase_id,))

                # Validate all new entries before making changes
                validated_items = []
                for item_id, qty in zip(item_ids, quantities):
                    if item_id and qty:
                        qty_int = int(qty)
                        if qty_int <= 0:
                            stock_errors.append("Quantity must be a positive number.")
                            continue

                        # Check available stock
                        cur.execute("""
                            SELECT i.name, COALESCE(iv.quantity_available, 0)
                            FROM items i
                            LEFT JOIN inventory iv ON i.item_id = iv.item_id
                            WHERE i.item_id = %s
                        """, (item_id,))
                        result = cur.fetchone()

                        if not result:
                            stock_errors.append(f"Item ID {item_id} not found.")
                        elif qty_int > result[1]:
                            stock_errors.append(f"Only {result[1]} '{result[0]}' in stock.")

                        validated_items.append((item_id, qty_int))

                if stock_errors:
                    raise Exception(" | ".join(stock_errors))

                # If all good then insert new records
                for item_id, qty_int in validated_items:
                    cur.execute("""
                        INSERT INTO purchase_items (purchase_id, item_id, quantity)
                        VALUES (%s, %s, %s)
                    """, (purchase_id, item_id, qty_int))

                    cur.execute("UPDATE inventory SET quantity_available = quantity_available - %s WHERE item_id = %s",
                                (qty_int, item_id))

                mysql.connection.commit()
                success = "Purchase updated successfully!"
                return redirect('/purchase')

            except Exception as e:
                mysql.connection.rollback()
                error = f"Update failed: {str(e)}"

    # GET → fetch all items
    cur.execute("SELECT item_id, name FROM items")
    items = cur.fetchall()

    # fetch existing purchase items
    cur.execute("SELECT item_id, quantity FROM purchase_items WHERE purchase_id = %s", (purchase_id,))
    purchase_items = cur.fetchall()
    selected_items = {item[0]: item[1] for item in purchase_items}

    cur.close()
    return render_template("edit_purchase.html", items=items, selected_items=selected_items, error=error)


# Delete Purchase with inventory restore
@app.route('/purchase/delete/<int:purchase_id>')
def delete_purchase(purchase_id):
    cur = mysql.connection.cursor()

    cur.execute("SELECT item_id, quantity FROM purchase_items WHERE purchase_id = %s", (purchase_id,))
    items_to_restore = cur.fetchall()
    for item_id, qty in items_to_restore:
        cur.execute("UPDATE inventory SET quantity_available = quantity_available + %s WHERE item_id = %s",
                    (qty, item_id))

    cur.execute("DELETE FROM purchase_items WHERE purchase_id = %s", (purchase_id,))
    cur.execute("DELETE FROM shipping WHERE purchase_id = %s", (purchase_id,))
    cur.execute("DELETE FROM purchase WHERE purchase_id = %s", (purchase_id,))

    mysql.connection.commit()
    cur.close()
    return redirect('/purchase')


# Add Shipping
@app.route('/shipping', methods=['GET', 'POST'])
def shipping():
    error = None
    success = None
    cur = mysql.connection.cursor()

    cur.execute("SELECT purchase_id FROM purchase")
    purchases = cur.fetchall()

    if request.method == 'POST':
        purchase_id = request.form.get('purchase_id')
        address = request.form.get('address', '').strip()
        status = request.form.get('status', '').strip()

        # Validation
        if not purchase_id or not address or not status:
            error = "All fields are required."
        else:
            try:
                cur.execute("INSERT INTO shipping (purchase_id, address, status) VALUES (%s, %s, %s)",
                            (purchase_id, address, status))
                mysql.connection.commit()
                success = "Shipping details saved successfully!"
            except Exception as e:
                mysql.connection.rollback()
                error = f"Something went wrong: {str(e)}"

    cur.execute("SELECT * FROM shipping")
    shipping = cur.fetchall()
    cur.close()
    return render_template('shipping_form.html', purchases=purchases, shipping=shipping, error=error, success=success)


# Edit Shipping
@app.route('/shipping/edit/<int:shipping_id>', methods=['GET', 'POST'])
def edit_shipping(shipping_id):
    error = None
    success = None
    cur = mysql.connection.cursor()

    if request.method == 'POST':
        purchase_id = request.form.get('purchase_id')
        address = request.form.get('address', '').strip()
        status = request.form.get('status', '').strip()

        if not purchase_id or not address or not status:
            error = "All fields are required."
        else:
            try:
                cur.execute("""
                    UPDATE shipping 
                    SET purchase_id = %s, address = %s, status = %s 
                    WHERE shipping_id = %s
                """, (purchase_id, address, status, shipping_id))
                mysql.connection.commit()
                success = "Shipping updated successfully!"
                return redirect('/shipping')
            except Exception as e:
                mysql.connection.rollback()
                error = f"Update failed: {str(e)}"

    cur.execute("SELECT * FROM shipping WHERE shipping_id = %s", (shipping_id,))
    shipping = cur.fetchone()

    cur.execute("SELECT purchase_id FROM purchase")
    purchases = cur.fetchall()
    cur.close()

    return render_template("edit_shipping.html", shipping=shipping, purchases=purchases, error=error)

# Delete Shipping
@app.route('/shipping/delete/<int:shipping_id>')
def delete_shipping(shipping_id):
    cur = mysql.connection.cursor()
    cur.execute("DELETE FROM shipping WHERE shipping_id = %s", (shipping_id,))
    mysql.connection.commit()
    cur.close()
    return redirect('/shipping')


# Display Data 
@app.route('/display')
def display():
    cur = mysql.connection.cursor()
    cur.execute("""
        SELECT 
            i.name,
            i.type,
            i.price,
            pi.quantity,
            p.purchase_date,
            COALESCE(s.address, '-') AS address,
            COALESCE(s.status, '-') AS status
        FROM purchase_items pi
        JOIN items i ON pi.item_id = i.item_id
        JOIN purchase p ON pi.purchase_id = p.purchase_id
        LEFT JOIN shipping s 
            ON s.purchase_id = p.purchase_id
            AND s.shipping_id = (
                SELECT MIN(shipping_id) 
                FROM shipping 
                WHERE purchase_id = p.purchase_id
            )
    """)
    data = cur.fetchall()
    cur.close()
    return render_template('display.html', data=data)


# Run App
if __name__ == '__main__':
    app.run(debug=True)