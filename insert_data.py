import sqlite3
from werkzeug.security import generate_password_hash

DB_FILE = "food_mall.db"
ADMIN_USERNAME = "admin"
ADMIN_PASSWORD = "admin"

conn = sqlite3.connect(DB_FILE)
cur = conn.cursor()

cur.execute("SELECT COUNT(*) FROM admin_users")
if cur.fetchone()[0] == 0:
    cur.execute(
        "INSERT INTO admin_users (username, password_hash) VALUES (?, ?)",
        (ADMIN_USERNAME, generate_password_hash(ADMIN_PASSWORD))
    )

cur.execute("SELECT COUNT(*) FROM tables")
if cur.fetchone()[0] == 0:
    cur.executemany(
        "INSERT INTO tables (table_number) VALUES (?)",
        [(i,) for i in range(1, 11)]
    )

cur.execute("SELECT COUNT(*) FROM outlets")
if cur.fetchone()[0] == 0:
    outlets = [
        ("Dosa Corner", "South Indian"),
        ("Vada Pav Hub", "Maharashtrian"),
        ("Misal House", "Maharashtrian"),
        ("Bhakri & Zunka", "Maharashtrian"),
        ("Chaat Adda", "Street Food"),
        ("Sweet Corner", "Desserts")
    ]
    cur.executemany(
        "INSERT INTO outlets (outlet_name, category) VALUES (?, ?)",
        outlets
    )

cur.execute("SELECT COUNT(*) FROM food_items")
if cur.fetchone()[0] == 0:
    items = [
        (1, "Plain Dosa", "Crisp dosa served with chutney", "https://images.unsplash.com/photo-1504674900247-0877df9cc836?auto=format&fit=crop&w=1200&q=80", 50),
        (1, "Masala Dosa", "Potato masala filling", "https://images.unsplash.com/photo-1476224203421-9ac39bcb3327?auto=format&fit=crop&w=1200&q=80", 70),
        (1, "Idli", "Steamed rice cakes", "https://images.unsplash.com/photo-1504754524776-8f4f37790ca0?auto=format&fit=crop&w=1200&q=80", 30),
        (1, "Uttapam", "Topped with veggies", "https://images.unsplash.com/photo-1482049016688-2d3e1b311543?auto=format&fit=crop&w=1200&q=80", 60),
        (2, "Classic Vada Pav", "Mumbai street classic", "https://images.unsplash.com/photo-1567206563064-6f60f40a2b57?auto=format&fit=crop&w=1200&q=80", 25),
        (2, "Cheese Vada Pav", "Cheesy twist", "https://images.unsplash.com/photo-1550547660-d9450f859349?auto=format&fit=crop&w=1200&q=80", 40),
        (2, "Spicy Vada Pav", "Extra chutney kick", "https://images.unsplash.com/photo-1565299624946-b28f40a0ae38?auto=format&fit=crop&w=1200&q=80", 30),
        (2, "Butter Vada Pav", "Buttery toasted bun", "https://images.unsplash.com/photo-1546069901-eacef0df6022?auto=format&fit=crop&w=1200&q=80", 35),
        (3, "Misal Pav", "Spicy misal with farsan", "https://images.unsplash.com/photo-1482049016688-2d3e1b311543?auto=format&fit=crop&w=1200&q=80", 60),
        (3, "Special Misal", "Extra spice & toppings", "https://images.unsplash.com/photo-1481931098730-318b6f776db0?auto=format&fit=crop&w=1200&q=80", 80),
        (3, "Usal Pav", "Mild curry with pav", "https://images.unsplash.com/photo-1499636136210-6f4ee915583e?auto=format&fit=crop&w=1200&q=80", 50),
        (3, "Tarri Misal", "Puneri style tarri", "https://images.unsplash.com/photo-1504674900247-0877df9cc836?auto=format&fit=crop&w=1200&q=80", 70),
        (4, "Zunka Bhakri", "Traditional combo", "https://images.unsplash.com/photo-1504754524776-8f4f37790ca0?auto=format&fit=crop&w=1200&q=80", 80),
        (4, "Thecha Bhakri", "Spicy thecha", "https://images.unsplash.com/photo-1482049016688-2d3e1b311543?auto=format&fit=crop&w=1200&q=80", 70),
        (4, "Pithla Bhakri", "Pithla with bhakri", "https://images.unsplash.com/photo-1476224203421-9ac39bcb3327?auto=format&fit=crop&w=1200&q=80", 75),
        (4, "Solkadhi", "Cooling kokum drink", "https://images.unsplash.com/photo-1464306076886-da185f7f9ed5?auto=format&fit=crop&w=1200&q=80", 25),
        (5, "Pani Puri", "Tangy water shots", "https://images.unsplash.com/photo-1481931098730-318b6f776db0?auto=format&fit=crop&w=1200&q=80", 40),
        (5, "Bhel Puri", "Crispy puffed rice", "https://images.unsplash.com/photo-1499028344343-cd173ffc68a9?auto=format&fit=crop&w=1200&q=80", 45),
        (5, "Sev Puri", "Crunchy sev topping", "https://images.unsplash.com/photo-1482049016688-2d3e1b311543?auto=format&fit=crop&w=1200&q=80", 50),
        (5, "Dahi Puri", "Sweet yogurt filling", "https://images.unsplash.com/photo-1504754524776-8f4f37790ca0?auto=format&fit=crop&w=1200&q=80", 55),
        (6, "Shrikhand", "Sweetened yogurt", "https://images.unsplash.com/photo-1499636136210-6f4ee915583e?auto=format&fit=crop&w=1200&q=80", 60),
        (6, "Puran Poli", "Stuffed sweet flatbread", "https://images.unsplash.com/photo-1464306076886-da185f7f9ed5?auto=format&fit=crop&w=1200&q=80", 70),
        (6, "Gulab Jamun", "Warm syrup balls", "https://images.unsplash.com/photo-1499028344343-cd173ffc68a9?auto=format&fit=crop&w=1200&q=80", 50),
        (6, "Basundi", "Rich milk dessert", "https://images.unsplash.com/photo-1481931098730-318b6f776db0?auto=format&fit=crop&w=1200&q=80", 65)
    ]
    cur.executemany(
        "INSERT INTO food_items (outlet_id, item_name, description, image_url, price) VALUES (?, ?, ?, ?, ?)",
        items
    )

conn.commit()
conn.close()

print("✅ Sample data inserted")
