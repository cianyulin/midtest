import sqlite3

def connect_db() -> sqlite3.Connection:
    """connect_db() -> sqlite3.Connection
    建立並返回 SQLite 資料庫連線，設置 row_factory = sqlite3.Row"""
    conn = sqlite3.connect('bookstore.db')
    conn.row_factory = sqlite3.Row
    return conn

def initialize_db(conn: sqlite3.Connection) -> None:
    """initialize_db(conn: sqlite3.Connection) -> None
    檢查並建立資料表，插入初始資料。"""
    cursor = conn.cursor()
    # 建立資料表（不含 INSERT）
    cursor.executescript("""
    CREATE TABLE IF NOT EXISTS member (
        mid TEXT PRIMARY KEY,
        mname TEXT NOT NULL,
        mphone TEXT NOT NULL,
        memail TEXT
    );

    CREATE TABLE IF NOT EXISTS book (
        bid TEXT PRIMARY KEY,
        btitle TEXT NOT NULL,
        bprice INTEGER NOT NULL,
        bstock INTEGER NOT NULL
    );

    CREATE TABLE IF NOT EXISTS sale (
        sid INTEGER PRIMARY KEY AUTOINCREMENT,
        sdate TEXT NOT NULL,
        mid TEXT NOT NULL,
        bid TEXT NOT NULL,
        sqty INTEGER NOT NULL,
        sdiscount INTEGER NOT NULL,
        stotal INTEGER NOT NULL
    );
    """)

    # 檢查資料是否已存在（這邊用 member 表來當作判斷依據）
    cursor.execute("SELECT COUNT(*) FROM member")
    member_count = cursor.fetchone()[0]

    if member_count == 0:
        cursor.executescript("""
        INSERT INTO member VALUES ('M001', 'Alice', '0912-345678', 'alice@example.com');
        INSERT INTO member VALUES ('M002', 'Bob', '0923-456789', 'bob@example.com');
        INSERT INTO member VALUES ('M003', 'Cathy', '0934-567890', 'cathy@example.com');

        INSERT INTO book VALUES ('B001', 'Python Programming', 600, 50);
        INSERT INTO book VALUES ('B002', 'Data Science Basics', 800, 30);
        INSERT INTO book VALUES ('B003', 'Machine Learning Guide', 1200, 20);

        INSERT INTO sale (sdate, mid, bid, sqty, sdiscount, stotal) VALUES ('2024-01-15', 'M001', 'B001', 2, 100, 1100);
        INSERT INTO sale (sdate, mid, bid, sqty, sdiscount, stotal) VALUES ('2024-01-16', 'M002', 'B002', 1, 50, 750);
        INSERT INTO sale (sdate, mid, bid, sqty, sdiscount, stotal) VALUES ('2024-01-17', 'M001', 'B003', 3, 200, 3400);
        INSERT INTO sale (sdate, mid, bid, sqty, sdiscount, stotal) VALUES ('2024-01-18', 'M003', 'B001', 1, 0, 600);
        """)
        print("初始資料已新增。")
    else:
        print("資料已存在，跳過初始資料建立。")

    # 儲存變更
    conn.commit()

def add_sale(conn: sqlite3.Connection, sdate: str, mid: str, bid: str, sqty_input, sdiscount_input) -> tuple[bool, str]:
    """
    新增銷售記錄，驗證會員、書籍編號和庫存，計算總額並更新庫存。
    sqty_input 和 sdiscount_input 是原始輸入，將轉換為 int。
    """

    try:
        if len(sdate) != 10 or sdate.count("-") != 2:
            return False, "錯誤：日期格式不正確"

        # 將 sqty 和 sdiscount 嘗試轉為整數
        try:
            sqty = int(sqty_input)
            sdiscount = int(sdiscount_input)
        except ValueError:
            return False, "錯誤：數量與折扣金額必須是整數"

        if sqty <= 0:
            return False, "錯誤：數量必須為正整數"
        if sdiscount < 0:
            return False, "錯誤：折扣金額不能為負數"

        cursor = conn.cursor()
        cursor.execute("PRAGMA foreign_keys = ON;")  # 確保外鍵啟用

        # 查會員
        cursor.execute("SELECT * FROM member WHERE mid = ?", (mid,))
        member = cursor.fetchone()

        # 查書籍
        cursor.execute("SELECT * FROM book WHERE bid = ?", (bid,))
        book = cursor.fetchone()

        if not member or not book:
            return False, "錯誤：會員編號或書籍編號無效"

        if sqty > book["bstock"]:
            return False, f"錯誤：書籍庫存不足 (現有庫存: {book['bstock']})"

        stotal = (book["bprice"] * sqty) - sdiscount

        try:
            cursor.execute("BEGIN")
            cursor.execute("""
                INSERT INTO sale (sdate, mid, bid, sqty, sdiscount, stotal)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (sdate, mid, bid, sqty, sdiscount, stotal))
            cursor.execute("UPDATE book SET bstock = bstock - ? WHERE bid = ?", (sqty, bid))
            conn.commit()
            return True, f"銷售記錄已新增！(銷售總額: {stotal:,})"
        except sqlite3.Error:
            conn.rollback()
            return False, "錯誤：新增銷售失敗"

    except sqlite3.DatabaseError:
        return False, "資料庫錯誤"

# 測試
def manual_test_add_sale():
    import sqlite3

    conn = sqlite3.connect("bookstore.db")
    conn.row_factory = sqlite3.Row  # 讓資料可以用欄位名稱存取

    print("📚 新增銷售紀錄 - 手動輸入測試")

    sdate = input("輸入銷售日期 (YYYY-MM-DD)：")
    mid = input("輸入會員編號：")
    bid = input("輸入書籍編號：")

    try:
        sqty = int(input("輸入數量 (正整數)："))
        sdiscount = int(input("輸入折扣金額 (>= 0)："))
    except ValueError:
        print("❌ 輸入錯誤：數量和折扣金額必須為整數")
        conn.close()
        return

    success, message = add_sale(conn, sdate, mid, bid, sqty, sdiscount)
    if success:
        print("✅ 成功！", message)
    else:
        print("❌ 失敗：", message)

    conn.close()

# 放在主程式入口點
if __name__ == "__main__":
    manual_test_add_sale()
