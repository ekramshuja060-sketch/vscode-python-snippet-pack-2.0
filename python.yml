y# mega_platform_pro_online.py
import streamlit as st
import sqlite3
import hashlib
import random
from datetime import datetime

# === اتصال به دیتابیس SQLite ===
conn = sqlite3.connect('mega_platform_pro_online.db', check_same_thread=False)
c = conn.cursor()

# ایجاد جدول‌ها
c.execute('''CREATE TABLE IF NOT EXISTS users
             (id INTEGER PRIMARY KEY AUTOINCREMENT, username TEXT UNIQUE, password TEXT, bio TEXT)''')
c.execute('''CREATE TABLE IF NOT EXISTS follow
             (follower TEXT, following TEXT)''')
c.execute('''CREATE TABLE IF NOT EXISTS posts
             (id INTEGER PRIMARY KEY AUTOINCREMENT, user TEXT, content TEXT, type TEXT, time TEXT)''')
c.execute('''CREATE TABLE IF NOT EXISTS books
             (id INTEGER PRIMARY KEY AUTOINCREMENT, user TEXT, book TEXT)''')
c.execute('''CREATE TABLE IF NOT EXISTS games
             (id INTEGER PRIMARY KEY AUTOINCREMENT, user TEXT, game TEXT, score INTEGER, time TEXT)''')
c.execute('''CREATE TABLE IF NOT EXISTS messages
             (id INTEGER PRIMARY KEY AUTOINCREMENT, sender TEXT, receiver TEXT, content TEXT, time TEXT)''')
conn.commit()

# === توابع کمکی ===
def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

def create_user(username, password, bio=""):
    try:
        c.execute("INSERT INTO users (username, password, bio) VALUES (?, ?, ?)",
                  (username, hash_password(password), bio))
        conn.commit()
        return True
    except sqlite3.IntegrityError:
        return False

def authenticate_user(username, password):
    c.execute("SELECT * FROM users WHERE username=? AND password=?",
              (username, hash_password(password)))
    return c.fetchone() is not None

def follow_user(follower, following):
    c.execute("SELECT * FROM follow WHERE follower=? AND following=?", (follower, following))
    if c.fetchone() is None:
        c.execute("INSERT INTO follow (follower, following) VALUES (?, ?)", (follower, following))
        conn.commit()

def get_following(user):
    c.execute("SELECT following FROM follow WHERE follower=?", (user,))
    return [f[0] for f in c.fetchall()]

# === شبیه‌ساز ChatGPT ===
class ChatGPTSimulator:
    @staticmethod
    def generate_poem(topic):
        poems = [
            f"زندگی و {topic}، بازی و امید، هر لحظه یک قصه جدید.",
            f"{topic} در دل شب، مثل نور ستاره‌ها، می‌درخشد و می‌ماند در خاطره‌ها."
        ]
        return random.choice(poems)

    @staticmethod
    def generate_story(topic):
        stories = [
            f"روزی روزگاری در دنیایی پر از {topic}، قهرمان ما سفر خود را آغاز کرد.",
            f"در شهری پر از {topic}، دو دوست تصمیم گرفتند رازهای دنیا را کشف کنند."
        ]
        return random.choice(stories)

chatgpt = ChatGPTSimulator()

# === رابط کاربری Streamlit ===
st.set_page_config(page_title="پلتفرم حرفه‌ای آنلاین", layout="wide")
st.title("🌐 پلتفرم حرفه‌ای آنلاین (شبکه اجتماعی)")

# --- Login / Register ---
if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False

if not st.session_state.logged_in:
    st.subheader("ورود یا ثبت‌نام")
    username = st.text_input("نام کاربری")
    password = st.text_input("رمز عبور", type="password")
    bio = st.text_input("بیو (اختیاری)")

    col1, col2 = st.columns(2)
    with col1:
        if st.button("ثبت‌نام"):
            if create_user(username, password, bio):
                st.success("ثبت‌نام موفق! اکنون وارد شوید.")
            else:
                st.error("این نام کاربری قبلاً استفاده شده است.")
    with col2:
        if st.button("ورود"):
            if authenticate_user(username, password):
                st.session_state.logged_in = True
                st.session_state.username = username
                st.success(f"خوش آمدی {username}!")
            else:
                st.error("نام کاربری یا رمز عبور اشتباه است.")

# --- بخش اصلی بعد از login ---
if st.session_state.logged_in:
    user = st.session_state.username
    st.subheader(f"سلام {user}!")

    # پروفایل و دنبال کردن
    st.header("👤 پروفایل شما")
    c.execute("SELECT bio FROM users WHERE username=?", (user,))
    bio = c.fetchone()[0]
    st.write(f"بیو: {bio}")

    st.subheader("دنبال کردن کاربران")
    c.execute("SELECT username FROM users WHERE username!=?", (user,))
    all_users = [u[0] for u in c.fetchall()]
    for u in all_users:
        if st.button(f"دنبال کردن {u}"):
            follow_user(user, u)
            st.success(f"شما {u} را دنبال کردید!")

    # فید شخصی
    st.header("📝 فید شخصی")
    following_users = get_following(user)
    following_users.append(user)  # شامل پست‌های خود
    if following_users:
        placeholders = []
        for fu in following_users:
            c.execute("SELECT content, type, time FROM posts WHERE user=? ORDER BY id DESC", (fu,))
            posts = c.fetchall()
            for p in posts:
                st.write(f"[{p[2]}] {fu} ({p[1]}): {p[0]}")
    else:
        st.write("شما هیچ کاربری را دنبال نکرده‌اید.")

    # ارسال پست، شعر، داستان
    st.header("ارسال محتوا")
    post_text = st.text_area("پست جدید")
    if st.button("ارسال پست"):
        c.execute("INSERT INTO posts (user, content, type, time) VALUES (?, ?, ?, ?)",
                  (user, post_text, "text", datetime.now().isoformat()))
        conn.commit()
        st.success("پست ارسال شد!")

    poem_topic = st.text_input("موضوع شعر")
    if st.button("ارسال شعر"):
        poem = chatgpt.generate_poem(poem_topic)
        c.execute("INSERT INTO posts (user, content, type, time) VALUES (?, ?, ?, ?)",
                  (user, poem, "poem", datetime.now().isoformat()))
        conn.commit()
        st.success("شعر ارسال شد!")

    story_topic = st.text_input("موضوع داستان")
    if st.button("ارسال داستان"):
        story = chatgpt.generate_story(story_topic)
        c.execute("INSERT INTO posts (user, content, type, time) VALUES (?, ?, ?, ?)",
                  (user, story, "story", datetime.now().isoformat()))
        conn.commit()
        st.success("داستان ارسال شد!")

    # کتابخانه
    st.header("📚 کتابخانه شخصی")
    book_name = st.text_input("افزودن کتاب جدید")
    if st.button("اضافه کردن کتاب"):
        c.execute("INSERT INTO books (user, book) VALUES (?, ?)", (user, book_name))
        conn.commit()
        st.success(f"{book_name} اضافه شد!")
    c.execute("SELECT book FROM books WHERE user=?", (user,))
    books = c.fetchall()
    for b in books:
        st.write(f"- {b[0]}")

    # بازی آنلاین
    st.header("🎮 بازی‌ها")
    game_name = st.text_input("نام بازی")
    if st.button("بازی کن"):
        score = random.randint(0, 100)
        c.execute("INSERT INTO games (user, game, score, time) VALUES (?, ?, ?, ?)",
                  (user, game_name, score, datetime.now().isoformat()))
        conn.commit()
        st.success(f"{game_name} بازی شد! امتیاز: {score}")

    # جدول رده‌بندی
    st.subheader("🏆 جدول رده‌بندی")
    c.execute("SELECT user, SUM(score) FROM games GROUP BY user ORDER BY SUM(score) DESC")
    leaderboard = c.fetchall()
    for i, l in enumerate(leaderboard, start=1):
        st.write(f"{i}. {l[0]} - مجموع امتیاز: {l[1]}")

    # پیام خصوصی
    st.header("💌 پیام خصوصی")
    receiver_name = st.text_input("گیرنده پیام")
    message_content = st.text_area("پیام")
    if st.button("ارسال پیام"):
        c.execute("INSERT INTO messages (sender, receiver, content, time) VALUES (?, ?, ?, ?)",
                  (user, receiver_name, message_content, datetime.now().isoformat()))
        conn.commit()
        st.success("پیام ارسال شد!")
    st.subheader("پیام‌های دریافتی")
    c.execute("SELECT sender, content, time FROM messages WHERE receiver=? ORDER BY id DESC", (user,))
    messages = c.fetchall()
    for m in messages:
        st.write(f"[{m[2]}] {m[0]} -> شما: {m[1]}")

    # خروج
    if st.button("خروج"):
        st.session_state.logged_in = False
        st.experimental_rerun()
