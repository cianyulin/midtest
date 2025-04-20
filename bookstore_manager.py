import sqlite3

# 連接資料庫（如果檔案不存在就會自動建立）
conn = sqlite3.connect('bookstore.db')
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