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
    
def print_sale_report(conn: sqlite3.Connection) -> None:
    """print_sale_report(conn: sqlite3.Connection) -> None
    查詢並顯示所有銷售報表，按銷售編號排序。"""
    cursor = conn.cursor()
    cursor.execute("""
        SELECT sale.sid, sale.sdate, member.mname, book.btitle,
               book.bprice, sale.sqty, sale.sdiscount, sale.stotal
        FROM sale
        JOIN member ON sale.mid = member.mid
        JOIN book ON sale.bid = book.bid
        ORDER BY sale.sid
    """)
    rows = cursor.fetchall()
    if not rows:
        print("目前沒有銷售資料。")
        return

    print("\n" + "="*20 + " 銷售報表 " + "="*20)

    for idx, row in enumerate(rows, 1):
        print(f"\n銷售 #{idx}")
        print(f"銷售編號: {row['sid']}")
        print(f"銷售日期: {row['sdate']}")
        print(f"會員姓名: {row['mname']}")
        print(f"書籍標題: {row['btitle']}")
        print("-"*50)
        print("單價\t數量\t折扣\t小計")
        print("-"*50)
        print(f"{row['bprice']}\t{row['sqty']}\t{row['sdiscount']}\t{row['stotal']:,}")
        print("-"*50)
        print(f"銷售總額: {row['stotal']:,}")
        print("="*50)

def update_sale(conn: sqlite3.Connection) -> None:
    """update_sale(conn: sqlite3.Connection) -> None
    顯示銷售記錄列表，提示使用者輸入要更新的銷售編號和新的折扣金額，重新計算總額"""
    cursor = conn.cursor()
    cursor.execute("""
        SELECT sale.sid, member.mname, sale.sdate, book.bprice, sale.sqty
        FROM sale
        JOIN member ON sale.mid = member.mid
        JOIN book ON sale.bid = book.bid
        ORDER BY sale.sid
    """)
    sales = cursor.fetchall()

    print("\n======== 銷售記錄列表 ========")
    for sale in sales:
        print(f"銷售編號: {sale['sid']} - 會員: {sale['mname']} - 日期: {sale['sdate']}")
    print("================================")

    choice = input("請輸入要更新的銷售編號 (輸入數字或按 Enter 取消): ")
    if not choice:
        return

    try:
        sid = int(choice)
        matched_sale = None
        for sale in sales:
            if sale["sid"] == sid:
                matched_sale = sale
                break

        if not matched_sale:
            print("錯誤：找不到該銷售編號")
            return

        bprice = matched_sale["bprice"]
        sqty = matched_sale["sqty"]

        discount = int(input("請輸入新的折扣金額："))
        if discount < 0:
            print("錯誤：折扣金額不能為負數")
            return
        stotal = (bprice * sqty) - discount

        cursor.execute("UPDATE sale SET sdiscount = ?, stotal = ? WHERE sid = ?", (discount, stotal, sid))
        conn.commit()
        print(f"=> 銷售編號 {sid} 已更新！(銷售總額: {stotal:,})")
    except ValueError:
        print("錯誤：請輸入有效的數字")


def delete_sale(conn: sqlite3.Connection) -> None:
    """delete_sale(conn: sqlite3.Connection) -> None
    顯示銷售記錄列表，提示使用者輸入要刪除的銷售編號，執行刪除操作並提交"""
    cursor = conn.cursor()
    cursor.execute("""
        SELECT sale.sid, member.mname, sale.sdate
        FROM sale
        JOIN member ON sale.mid = member.mid
        ORDER BY sale.sid
    """)
    sales = cursor.fetchall()

    print("\n======== 銷售記錄列表 ========")
    for i, sale in enumerate(sales, 1):
        print(f"{i}. 銷售編號: {sale['sid']} - 會員: {sale['mname']} - 日期: {sale['sdate']}")
    print("================================")

    choice = input("請輸入要刪除的銷售編號 (輸入數字或按 Enter 取消): ")
    if not choice:
        return

    try:
        sid = int(choice)
        found = False
        for sale in sales:
            if sale["sid"] == sid:
                found = True
                break

        if not found:
            print("錯誤：找不到該銷售編號")
            return

        cursor.execute("DELETE FROM sale WHERE sid = ?", (sid,))
        conn.commit()
        print(f"=> 銷售編號 {sid} 已刪除")
    except ValueError:
        print("錯誤：請輸入有效的數字")

def main() -> None:
    """main() -> None
    程式主流程，包含選單迴圈和各功能的呼叫"""
    with connect_db() as conn:
        initialize_db(conn)

        while True:
            print("""
***************選單***************
1. 新增銷售記錄
2. 顯示銷售報表
3. 更新銷售記錄
4. 刪除銷售記錄
5. 離開
**********************************
            """)
            choice = input("請選擇操作項目(Enter 離開)：")
            if not choice or choice == "5":
                break
            elif choice == "1":
                sdate = input("請輸入銷售日期 (YYYY-MM-DD)：")
                mid = input("請輸入會員編號：")
                bid = input("請輸入書籍編號：")

                try:
                    sqty = int(input("請輸入購買數量："))
                    sdiscount = int(input("請輸入折扣金額："))
                except ValueError:
                    print("=> 錯誤：數量或折扣必須為整數，請重新輸入")
                    continue

                success, message = add_sale(conn, sdate, mid, bid, sqty, sdiscount)
                print("=>", message)
            elif choice == "2":
                print_sale_report(conn)
            elif choice == "3":
                update_sale(conn)
            elif choice == "4":
                delete_sale(conn)
            else:
                print("=> 請輸入有效的選項（1-5）")


# 測試新增
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

# 測試顯示
def test_print_sale_report():
    import sqlite3

    conn = sqlite3.connect("bookstore.db")
    conn.row_factory = sqlite3.Row  # 讓 row 可以用欄位名稱

    print("\n📄 銷售報表測試")
    print_sale_report(conn)

    conn.close()


#測試改銷售紀錄
def test_update_sale_function():
    conn = sqlite3.connect("bookstore.db")
    conn.row_factory = sqlite3.Row

    update_sale(conn)

    conn.close()


#測試刪除
def test_delete_sale_function():
    conn = sqlite3.connect("bookstore.db")
    conn.row_factory = sqlite3.Row  # 讓資料可以用欄位名稱取用

    delete_sale(conn)

    conn.close()


# 放在主程式入口點
if __name__ == "__main__":
    #manual_test_add_sale()
    #test_print_sale_report()
    #test_update_sale_function()
    #test_delete_sale_function()
    main()