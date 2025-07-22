from sqlalchemy import text

def get_similar_products(db, user_vector, limit=10):
    sql = text("""
        SELECT id, name, vector_combined <-> :vec AS dist
        FROM products
        ORDER BY dist ASC
        LIMIT :limit
    """)
    result = db.execute(sql, {"vec": user_vector, "limit": limit}).fetchall()
    return [{"id": row[0], "name": row[1], "distance": row[2]} for row in result]
