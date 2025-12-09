# app.py
import streamlit as st
import sqlite3
import hashlib
import random
from datetime import datetime
import queue
import uuid

# === اتصال به دیتابیس SQLite ===
conn = sqlite3.connect('mega_platform.db', check_same_thread=False)
c = conn.cursor()

# ایجاد جدول‌ها
c.execute('''CREATE TABLE IF NOT EXISTS users 
             (id INTEGER PRIMARY KEY AUTOINCREMENT, 
              username TEXT UNIQUE, 
              password TEXT, 
              bio TEXT,
              created_at TEXT)''')

c.execute('''CREATE TABLE IF NOT EXISTS follow 
             (follower TEXT, 
              following TEXT,
              created_at TEXT)''')

c.execute('''CREATE TABLE IF NOT EXISTS posts 
             (id INTEGER PRIMARY KEY AUTOINCREMENT, 
              user TEXT, 
              content TEXT, 
              type TEXT, 
              likes INTEGER DEFAULT 0,
              time TEXT)''')

c.execute('''CREATE TABLE IF NOT EXISTS post_likes 
             (post_id INTEGER,
              user TEXT,
              created_at TEXT)''')

c.execute('''CREATE TABLE IF NOT EXISTS books 
             (id INTEGER PRIMARY KEY AUTOINCREMENT, 
              user TEXT, 
              book TEXT,
              added_at TEXT)''')

c.execute('''CREATE TABLE IF NOT EXISTS games 
             (id INTEGER PRIMARY KEY AUTOINCREMENT, 
              user TEXT, 
              game TEXT, 
              score INTEGER, 
              time TEXT)''')

c.execute('''CREATE TABLE IF NOT EXISTS messages 
             (id INTEGER PRIMARY KEY AUTOINCREMENT, 
              sender TEXT, 
              receiver TEXT, 
              content TEXT, 
              time TEXT)''')

c.execute('''CREATE TABLE IF NOT EXISTS chat_rooms 
             (id INTEGER PRIMARY KEY AUTOINCREMENT, 
              name TEXT, 
              created_by TEXT,
              created_at TEXT)''')

c.execute('''CREATE TABLE IF NOT EXISTS chat_messages 
             (id INTEGER PRIMARY KEY AUTOINCREMENT, 
              room TEXT, 
              sender TEXT, 
              content TEXT, 
              time TEXT)''')

conn.commit()

# === توابع کمکی ===
def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

def create_user(username, password, bio=""):
    try:
        c.execute("INSERT INTO users (username, password, bio, created_at) VALUES (?, ?, ?, ?)",
                  (username, hash_password(password), bio, datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
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
        c.execute("INSERT INTO follow (follower, following, created_at) VALUES (?, ?, ?)", 
                  (follower, following, datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
        conn.commit()
        return True
    return False

def get_following(user):
    c.execute("SELECT following FROM follow WHERE follower=?", (user,))
    return [f[0] for f in c.fetchall()]

def get_followers(user):
    c.execute("SELECT follower FROM follow WHERE following=?", (user,))
    return [f[0] for f in c.fetchall()]

def unfollow_user(follower, following):
    c.execute("DELETE FROM follow WHERE follower=? AND following=?", (follower, following))
    conn.commit()

def like_post(user, post_id):
    c.execute("SELECT * FROM post_likes WHERE post_id=? AND user=?", (post_id, user))
    if c.fetchone() is None:
        c.execute("INSERT INTO post_likes (post_id, user, created_at) VALUES (?, ?, ?)",
                  (post_id, user, datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
        c.execute("UPDATE posts SET likes = likes + 1 WHERE id=?", (post_id,))
        conn.commit()
        return True
    return False

def unlike_post(user, post_id):
    c.execute("DELETE FROM post_likes WHERE post_id=? AND user=?", (post_id, user))
    c.execute("UPDATE posts SET likes = likes - 1 WHERE id=?", (post_id,))
    conn.commit()

def get_user_info(username):
    c.execute("SELECT username, bio, created_at FROM users WHERE username=?", (username,))
    return c.fetchone()

# === شبیه‌ساز ChatGPT ===
class ChatGPTSimulator:
    @staticmethod
    def generate_poem(topic):
        poems = [
            f"در آسمان {topic} ستاره‌ای درخشید،\nقلب من از شوق آن آرام گرفت.",
            f"{topic} آمد و بهار شد،\nگل‌ها همه در بهار شکفتند.",
            f"ای {topic}، تو روشنی دلی،\nدر تاریکی شب‌ها تو چراغ راهی.",
            f"با نام {topic} آغاز کن،\nراهی به سوی روشنایی بیاب."
        ]
        return random.choice(poems)

    @staticmethod
    def generate_story(topic):
        stories = [
            f"روزی روزگاری در سرزمین {topic}، شاهزاده‌ای زندگی می‌کرد که...",
            f"در جنگل اسرارآمیز {topic}، موجوداتی عجیب و غریب سکونت داشتند...",
            f"ماجراجوی جوانی به نام علی، تصمیم گرفت راز {topic} را کشف کند...",
            f"در کهکشان دوردست، سیاره‌ای به نام {topic} وجود داشت که..."
        ]
        return random.choice(stories)

    @staticmethod
    def generate_quote():
        quotes = [
            "زندگی مانند دوچرخه سواری است، برای حفظ تعادل باید حرکت کرد.",
            "بزرگترین اشتباه این است که از اشتباه کردن بترسیم.",
            "موفقیت یعنی رفتن از شکستی به شکست دیگر بدون از دست دادن اشتیاق.",
            "آینده به کسانی تعلق دارد که به زیبایی رویاهایشان باور دارند."
        ]
        return random.choice(quotes)

chatgpt = ChatGPTSimulator()

# === سیستم چت ===
class ChatSystem:
    @staticmethod
    def send_message(room, sender, message):
        timestamp = datetime.now().strftime("%H:%M:%S")
        c.execute("INSERT INTO chat_messages (room, sender, content, time) VALUES (?, ?, ?, ?)",
                  (room, sender, message, timestamp))
        conn.commit()
        return {"sender": sender, "message": message, "time": timestamp}
    
    @staticmethod
    def get_messages(room, limit=50):
        c.execute("SELECT sender, content, time FROM chat_messages WHERE room=? ORDER BY id DESC LIMIT ?", 
                  (room, limit))
        messages = c.fetchall()
        return [{"sender": m[0], "message": m[1], "time": m[2]} for m in messages[::-1]]
    
    @staticmethod
    def create_room(name, creator):
        try:
            c.execute("INSERT INTO chat_rooms (name, created_by, created_at) VALUES (?, ?, ?)",
                      (name, creator, datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
            conn.commit()
            return True
        except:
            return False
    
    @staticmethod
    def get_rooms():
        c.execute("SELECT name, created_by FROM chat_rooms ORDER BY id DESC")
        return c.fetchall()

chat_system = ChatSystem()

# === سیستم بازی ===
class GameSystem:
    @staticmethod
    def play_guess_number(user, number):
        secret = random.randint(1, 100)
        score = max(0, 100 - abs(secret - number) * 10)
        
        c.execute("INSERT INTO games (user, game, score, time) VALUES (?, ?, ?, ?)",
                  (user, "حدس عدد", score, datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
        conn.commit()
        
        return {
            "secret": secret,
            "score": score,
            "message": f"عدد مخفی {secret} بود! شما {number} گفتید. 🎯"
        }
    
    @staticmethod
    def play_trivia(user, answer):
        questions = [
            {"question": "پایتخت ایران کجاست؟", "answer": "تهران", "score": 100},
            {"question": "بزرگترین سیاره منظومه شمسی؟", "answer": "مشتری", "score": 100},
            {"question": "نویسنده شاهنامه؟", "answer": "فردوسی", "score": 100},
            {"question": "بلندترین کوه جهان؟", "answer": "اورست", "score": 100},
            {"question": "رنگین کمان چند رنگ دارد؟", "answer": "هفت", "score": 100},
        ]
        q = random.choice(questions)
        
        if answer.lower() == q["answer"].lower():
            score = q["score"]
            message = f"🎉 درست جواب دادید! +{score} امتیاز"
        else:
            score = 0
            message = f"❌ پاسخ صحیح: {q['answer']}"
        
        c.execute("INSERT INTO games (user, game, score, time) VALUES (?, ?, ?, ?)",
                  (user, "سوال هوش", score, datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
        conn.commit()
        
        return {"score": score, "message": message, "question": q["question"]}
    
    @staticmethod
    def play_memory(user):
        score = random.randint(50, 100)
        c.execute("INSERT INTO games (user, game, score, time) VALUES (?, ?, ?, ?)",
                  (user, "حافظه تصویری", score, datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
        conn.commit()
        return {"score": score, "message": f"امتیاز شما در بازی حافظه: {score}"}
    
    @staticmethod
    def get_leaderboard(limit=10):
        c.execute("""
            SELECT user, SUM(score) as total_score, COUNT(*) as games_count 
            FROM games 
            GROUP BY user 
            ORDER BY total_score DESC 
            LIMIT ?
        """, (limit,))
        return c.fetchall()

game_system = GameSystem()

# === تنظیمات Streamlit ===
st.set_page_config(
    page_title="مگا پلتفرم پرو آنلاین",
    layout="wide",
    initial_sidebar_state="expanded",
    page_icon="🚀"
)

# استایل سفارشی
st.markdown("""
<style>
    /* استایل کلی */
    .main {
        padding: 1rem;
    }
    
    /* هدر */
    .main-header {
        font-size: 2.8rem;
        color: #1E88E5;
        text-align: center;
        margin-bottom: 2rem;
        font-weight: bold;
        text-shadow: 2px 2px 4px rgba(0,0,0,0.1);
    }
    
    /* سکشن‌ها */
    .section-header {
        font-size: 1.8rem;
        color: #0D47A1;
        margin-top: 1.5rem;
        margin-bottom: 1rem;
        padding-bottom: 0.5rem;
        border-bottom: 3px solid #1E88E5;
    }
    
    /* کارت‌ها */
    .card {
        background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%);
        padding: 1.5rem;
        border-radius: 15px;
        margin-bottom: 1rem;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        border-left: 5px solid #1E88E5;
    }
    
    /* پیام‌های چت */
    .message-bubble-own {
        background: linear-gradient(135deg, #DCF8C6 0%, #B9F6CA 100%);
        padding: 0.8rem 1.2rem;
        border-radius: 18px;
        margin: 0.5rem 0;
        max-width: 70%;
        margin-left: auto;
        text-align: right;
    }
    
    .message-bubble-other {
        background: white;
        padding: 0.8rem 1.2rem;
        border-radius: 18px;
        margin: 0.5rem 0;
        max-width: 70%;
        border: 1px solid #E0E0E0;
    }
    
    /* کارت بازی */
    .game-card {
        background: linear-gradient(135deg, #FFECB3 0%, #FFD54F 100%);
        padding: 1.5rem;
        border-radius: 15px;
        margin-bottom: 1rem;
        box-shadow: 0 4px 8px rgba(0,0,0,0.1);
    }
    
    /* دکمه‌ها */
    .stButton > button {
        border-radius: 10px;
        border: none;
        transition: all 0.3s;
    }
    
    .stButton > button:hover {
        transform: translateY(-2px);
        box-shadow: 0 4px 8px rgba(0,0,0,0.2);
    }
    
    /* جداول */
    .leaderboard-row {
        padding: 0.5rem;
        border-radius: 8px;
        margin: 0.3rem 0;
        background: rgba(255,255,255,0.1);
    }
    
    /* فونت فارسی */
    * {
        font-family: 'Vazir', 'Tahoma', sans-serif;
    }
</style>
""", unsafe_allow_html=True)

# --- مدیریت وضعیت session ---
if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False
    st.session_state.username = None
    st.session_state.current_page = "خانه"
    st.session_state.chat_room = "عمومی"
    st.session_state.refresh_chat = False
    st.session_state.game_type = None

# --- صفحه ورود/ثبت‌نام ---
def show_login_page():
    st.markdown('<h1 class="main-header">🚀 مگا پلتفرم پرو آنلاین</h1>', unsafe_allow_html=True)
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.markdown("""
        ### 🌟 به بزرگترین پلتفرم اجتماعی خوش آمدید!
        
        **ویژگی‌های پلتفرم:**
        - 💬 چت آنلاین و اتاق‌های گفتگو
        - 🎮 بازی‌های آنلاین جذاب
        - 📱 شبکه اجتماعی با امکانات کامل
        - 📚 کتابخانه شخصی
        - 👥 سیستم دنبال‌کردن کاربران
        - 🏆 جدول رده‌بندی
        - ✨ و بسیاری امکانات دیگر...
        
        **برای شروع، وارد شوید یا ثبت‌نام کنید.**
        """)
    
    with col2:
        tab1, tab2 = st.tabs(["🔐 ورود", "📝 ثبت‌نام"])
        
        with tab1:
            st.subheader("ورود به حساب")
            login_user = st.text_input("نام کاربری")
            login_pass = st.text_input("رمز عبور", type="password")
            
            if st.button("ورود", use_container_width=True, type="primary"):
                if login_user and login_pass:
                    if authenticate_user(login_user, login_pass):
                        st.session_state.logged_in = True
                        st.session_state.username = login_user
                        st.session_state.current_page = "خانه"
                        st.success(f"✅ خوش آمدید {login_user}!")
                        st.rerun()
                    else:
                        st.error("❌ نام کاربری یا رمز عبور اشتباه است")
                else:
                    st.warning("⚠️ لطفا اطلاعات را کامل وارد کنید")
        
        with tab2:
            st.subheader("ایجاد حساب جدید")
            reg_user = st.text_input("نام کاربری جدید")
            reg_pass = st.text_input("رمز عبور جدید", type="password")
            reg_pass2 = st.text_input("تکرار رمز عبور", type="password")
            reg_bio = st.text_area("بیوگرافی (اختیاری)")
            
            if st.button("ثبت‌نام", use_container_width=True):
                if reg_user and reg_pass:
                    if reg_pass == reg_pass2:
                        if create_user(reg_user, reg_pass, reg_bio):
                            st.success("✅ حساب کاربری با موفقیت ایجاد شد!")
                            st.info("اکنون می‌توانید وارد شوید")
                        else:
                            st.error("❌ این نام کاربری قبلاً ثبت شده است")
                    else:
                        st.error("❌ رمزهای عبور مطابقت ندارند")
                else:
                    st.warning("⚠️ لطفا اطلاعات را کامل وارد کنید")
    
    # آمار پلتفرم
    st.markdown("---")
    st.subheader("📊 آمار پلتفرم")
    
    col_stats1, col_stats2, col_stats3, col_stats4 = st.columns(4)
    
    with col_stats1:
        c.execute("SELECT COUNT(*) FROM users")
        user_count = c.fetchone()[0]
        st.metric("👥 کاربران", user_count, delta="+12%")
    
    with col_stats2:
        c.execute("SELECT COUNT(*) FROM posts")
        post_count = c.fetchone()[0]
        st.metric("📝 پست‌ها", post_count, delta="+8%")
    
    with col_stats3:
        c.execute("SELECT COUNT(*) FROM games")
        game_count = c.fetchone()[0]
        st.metric("🎮 بازی‌ها", game_count, delta="+15%")
    
    with col_stats4:
        c.execute("SELECT COUNT(*) FROM messages")
        msg_count = c.fetchone()[0]
        st.metric("💬 پیام‌ها", msg_count, delta="+20%")

# --- نوار کناری منو ---
def show_sidebar():
    with st.sidebar:
        st.markdown(f"### 👋 سلام {st.session_state.username}!")
        
        # اطلاعات کاربر
        user_info = get_user_info(st.session_state.username)
        if user_info:
            with st.expander("👤 اطلاعات حساب"):
                st.write(f"**نام کاربری:** {user_info[0]}")
                st.write(f"**بیوگرافی:** {user_info[1] if user_info[1] else 'تعیین نشده'}")
                st.write(f"**عضو از:** {user_info[2]}")
        
        st.markdown("---")
        
        # آمار کاربر
        followers = len(get_followers(st.session_state.username))
        following = len(get_following(st.session_state.username))
        
        col_f1, col_f2 = st.columns(2)
        with col_f1:
            st.metric("دنبال‌کننده", followers)
        with col_f2:
            st.metric("دنبال‌شونده", following)
        
        st.markdown("---")
        
        # منوی اصلی
        st.subheader("📍 منو")
        
        menu_items = {
            "🏠 خانه": "خانه",
            "👤 پروفایل": "پروفایل", 
            "💬 چت آنلاین": "چت",
            "🎮 بازی‌ها": "بازی",
            "📚 کتابخانه": "کتابخانه",
            "👥 کاربران": "کاربران",
            "⚙️ تنظیمات": "تنظیمات",
            "🏆 رده‌بندی": "رده‌بندی"
        }
        
        selected_page = st.radio(
            "انتخاب بخش:",
            list(menu_items.keys()),
            label_visibility="collapsed"
        )
        
        if menu_items[selected_page] != st.session_state.current_page:
            st.session_state.current_page = menu_items[selected_page]
            st.rerun()
        
        st.markdown("---")
        
        # دکمه خروج
        if st.button("🚪 خروج از حساب", use_container_width=True, type="secondary"):
            st.session_state.logged_in = False
            st.session_state.username = None
            st.rerun()
        
        # نمایش وضعیت آنلاین
        st.caption(f"🟢 آنلاین - {datetime.now().strftime('%H:%M')}")

# --- صفحه اصلی ---
def show_home_page():
    st.markdown('<h2 class="section-header">🏠 خانه - فید اخبار</h2>', unsafe_allow_html=True)
    
    # ارسال پست جدید
    with st.form("new_post_form", clear_on_submit=True):
        col_type, col_auto = st.columns([2, 1])
        with col_type:
            post_type = st.selectbox("نوع محتوا:", ["پست متنی", "شعر", "داستان", "نکته"])
        with col_auto:
            if post_type in ["شعر", "داستان"]:
                auto_generate = st.checkbox("تولید خودکار")
            else:
                auto_generate = False
        
        post_content = st.text_area("متن پست:", height=150, 
                                   placeholder="چه چیزی در ذهنت میگذره؟...")
        
        if auto_generate:
            topic = st.text_input("موضوع:")
            if topic and post_type == "شعر":
                if st.button("🎭 تولید شعر"):
                    post_content = chatgpt.generate_poem(topic)
                    st.text_area("شعر تولید شده:", post_content, height=150)
            elif topic and post_type == "داستان":
                if st.button("📖 تولید داستان"):
                    post_content = chatgpt.generate_story(topic)
                    st.text_area("داستان تولید شده:", post_content, height=150)
        
        col_submit, col_clear = st.columns(2)
        with col_submit:
            submit = st.form_submit_button("📤 ارسال پست", use_container_width=True)
        with col_clear:
            clear = st.form_submit_button("🧹 پاک کردن", use_container_width=True, type="secondary")
        
        if submit and post_content:
            type_map = {"پست متنی": "text", "شعر": "poem", "داستان": "story", "نکته": "tip"}
            c.execute("INSERT INTO posts (user, content, type, time) VALUES (?, ?, ?, ?)",
                      (st.session_state.username, post_content, type_map[post_type], 
                       datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
            conn.commit()
            st.success("✅ پست شما منتشر شد!")
            st.rerun()
    
    st.markdown("---")
    
    # نمایش پست‌ها
    st.subheader("📜 آخرین پست‌ها")
    
    # دنبال‌شوندگان + خود کاربر
    following = get_following(st.session_state.username)
    following.append(st.session_state.username)
    
    if following:
        placeholders = ", ".join(["?"] * len(following))
        c.execute(f"""
            SELECT id, user, content, type, time, likes 
            FROM posts 
            WHERE user IN ({placeholders}) 
            ORDER BY id DESC 
            LIMIT 20
        """, following)
        
        posts = c.fetchall()
        
        if posts:
            for post in posts:
                with st.container():
                    st.markdown('<div class="card">', unsafe_allow_html=True)
                    
                    # هدر پست
                    col_avatar, col_info, col_likes = st.columns([1, 4, 1])
                    with col_avatar:
                        st.markdown("👤")
                    with col_info:
                        st.markdown(f"**{post[1]}** · `{post[3]}` · {post[4]}")
                    with col_likes:
                        st.markdown(f"❤️ {post[5]}")
                    
                    # محتوای پست
                    st.markdown(f"> {post[2]}")
                    
                    # دکمه‌های تعامل
                    col_like, col_comment, col_share = st.columns(3)
                    with col_like:
                        liked = st.button(f"❤️ لایک ({post[5]})", key=f"like_{post[0]}", 
                                         use_container_width=True)
                        if liked:
                            like_post(st.session_state.username, post[0])
                            st.rerun()
                    
                    with col_comment:
                        st.button("💬 نظر", key=f"comment_{post[0]}", use_container_width=True)
                    
                    with col_share:
                        st.button("↪️ اشتراک", key=f"share_{post[0]}", use_container_width=True)
                    
                    st.markdown('</div>', unsafe_allow_html=True)
        else:
            st.info("📭 هنوز پستی وجود ندارد. اولین پست را شما ایجاد کنید!")
    else:
        st.warning("👥 شما هیچ کاربری را دنبال نکرده‌اید. به بخش 'کاربران' بروید.")

# --- صفحه پروفایل ---
def show_profile_page():
    st.markdown('<h2 class="section-header">👤 پروفایل کاربری</h2>', unsafe_allow_html=True)
    
    # اطلاعات کاربر
    user_info = get_user_info(st.session_state.username)
    
    col_info, col_stats = st.columns([2, 1])
    
    with col_info:
        st.markdown("### اطلاعات شخصی")
        
        if user_info:
            current_bio = user_info[1] if user_info[1] else ""
            new_bio = st.text_area("بیوگرافی:", value=current_bio, height=150,
                                 placeholder="درباره خودتان بنویسید...")
            
            if st.button("💾 ذخیره بیوگرافی", use_container_width=True):
                c.execute("UPDATE users SET bio=? WHERE username=?", 
                         (new_bio, st.session_state.username))
                conn.commit()
                st.success("✅ بیوگرافی به‌روز شد!")
                st.rerun()
    
    with col_stats:
        st.markdown("### 📊 آمار شما")
        
        # تعداد پست‌ها
        c.execute("SELECT COUNT(*) FROM posts WHERE user=?", (st.session_state.username,))
        post_count = c.fetchone()[0]
        
        # تعداد لایک‌ها
        c.execute("SELECT SUM(likes) FROM posts WHERE user=?", (st.session_state.username,))
        total_likes = c.fetchone()[0] or 0
        
        # تعداد بازی‌ها
        c.execute("SELECT COUNT(*) FROM games WHERE user=?", (st.session_state.username,))
        game_count = c.fetchone()[0]
        
        # امتیاز کل
        c.execute("SELECT SUM(score) FROM games WHERE user=?", (st.session_state.username,))
        total_score = c.fetchone()[0] or 0
        
        st.metric("📝 پست‌ها", post_count)
        st.metric("❤️ لایک‌ها", total_likes)
        st.metric("🎮 بازی‌ها", game_count)
        st.metric("🏆 امتیاز کل", total_score)
    
    st.markdown("---")
    
    # پست‌های کاربر
    st.subheader("📝 پست‌های اخیر شما")
    
    c.execute("SELECT id, content, type, time, likes FROM posts WHERE user=? ORDER BY id DESC LIMIT 10", 
              (st.session_state.username,))
    user_posts = c.fetchall()
    
    if user_posts:
        for post in user_posts:
            with st.expander(f"{post[3]} - {post[2]} (❤️ {post[4]})"):
                st.write(post[1])
                if st.button("🗑️ حذف", key=f"del_post_{post[0]}"):
                    c.execute("DELETE FROM posts WHERE id=?", (post[0],))
                    conn.commit()
                    st.rerun()
    else:
        st.info("📭 شما هنوز پستی منتشر نکرده‌اید.")

# --- صفحه چت آنلاین ---
def show_chat_page():
    st.markdown('<h2 class="section-header">💬 چت آنلاین</h2>', unsafe_allow_html=True)
    
    # انتخاب/ایجاد اتاق
    col_room, col_create = st.columns([3, 1])
    
    with col_room:
        rooms = chat_system.get_rooms()
        room_list = ["عمومی", "دوستانه", "ورزشی", "فناوری"] + [r[0] for r in rooms]
        selected_room = st.selectbox("انتخاب اتاق:", room_list, 
                                    index=room_list.index(st.session_state.chat_room) 
                                    if st.session_state.chat_room in room_list else 0)
        
        if selected_room != st.session_state.chat_room:
            st.session_state.chat_room = selected_room
            st.rerun()
    
    with col_create:
        with st.popover("➕ اتاق جدید"):
            new_room = st.text_input("نام اتاق:")
            if st.button("ایجاد", use_container_width=True) and new_room:
                if chat_system.create_room(new_room, st.session_state.username):
                    st.success(f"✅ اتاق {new_room} ایجاد شد!")
                else:
                    st.error("❌ این اتاق قبلاً وجود دارد")
    
    st.markdown(f"### 💬 اتاق: **{st.session_state.chat_room}**")
    
    # نمایش پیام‌ها
    chat_container = st.container(height=400)
    
    with chat_container:
        messages = chat_system.get_messages(st.session_state.chat_room, limit=50)
        
        if not messages:
            st.info("💭 هنوز پیامی در این اتاق ارسال نشده. اولین نفر باشید!")
        
        for msg in messages:
            if msg["sender"] == st.session_state.username:
                st.markdown(f'''
                <div class="message-bubble-own">
                    <div style="font-weight: bold; color: #2E7D32;">شما</div>
                    <div>{msg['message']}</div>
                    <div style="font-size: 0.8em; color: #666; text-align: left;">{msg['time']}</div>
                </div>
                ''', unsafe_allow_html=True)
            else:
                st.markdown(f'''
                <div class="message-bubble-other">
                    <div style="font-weight: bold; color: #1E88E5;">{msg['sender']}</div>
                    <div>{msg['message']}</div>
                    <div style="font-size: 0.8em; color: #666;">{msg['time']}</div>
                </div>
                ''', unsafe_allow_html=True)
    
    # ارسال پیام جدید
    col_msg, col_send = st.columns([4, 1])
    
    with col_msg:
        new_message = st.text_input("پیام شما:", key="new_message", 
                                   placeholder="پیام خود را بنویسید...",
                                   label_visibility="collapsed")
    
    with col_send:
        send_btn = st.button("📤 ارسال", use_container_width=True, type="primary")
    
    if send_btn and new_message:
        chat_system.send_message(st.session_state.chat_room, 
                                st.session_state.username, 
                                new_message)
        st.rerun()

# --- صفحه بازی‌ها ---
def show_games_page():
    st.markdown('<h2 class="section-header">🎮 بازی‌های آنلاین</h2>', unsafe_allow_html=True)
    
    tab1, tab2, tab3, tab4 = st.tabs(["🎯 حدس عدد", "🧠 سوال هوش", "🧩 حافظه", "🏆 امتیازات"])
    
    with tab1:
        st.markdown("### 🎯 بازی حدس عدد")
        st.markdown("""
        **قوانین بازی:**
        - عددی بین 1 تا 100 انتخاب کنید
        - هرچه نزدیک‌تر حدس بزنید، امتیاز بیشتری می‌گیرید
        - حداکثر امتیاز: 100
        """)
        
        guess = st.slider("عدد خود را انتخاب کنید:", 1, 100, 50)
        
        if st.button("🎯 حدس بزن!", use_container_width=True, type="primary"):
            result = game_system.play_guess_number(st.session_state.username, guess)
            
            st.markdown('<div class="game-card">', unsafe_allow_html=True)
            st.markdown(f"### نتیجه بازی")
            st.markdown(f"**{result['message']}**")
            
            col_score, col_secret = st.columns(2)
            with col_score:
                st.metric("🎖️ امتیاز شما", result['score'])
            with col_secret:
                st.metric("🔢 عدد مخفی", result['secret'])
            
            if result['score'] >= 80:
                st.balloons()
                st.success("🎉 عالی! امتیاز بالایی کسب کردید!")
            elif result['score'] >= 50:
                st.info("👍 خوب بود! ادامه دهید")
            else:
                st.warning("💪 دفعه بعد بهتر می‌شوید!")
            
            st.markdown('</div>', unsafe_allow_html=True)
    
    with tab2:
        st.markdown("### 🧠 مسابقه اطلاعات عمومی")
        
        if 'trivia_question' not in st.session_state:
            questions = [
                "پایتخت ایران کجاست؟",
                "بزرگترین سیاره منظومه شمسی چیست؟",
                "نویسنده شاهنامه کیست؟",
                "بلندترین کوه جهان چه نام دارد؟",
                "رنگین کمان چند رنگ دارد؟",
                "سردترین قاره جهان کدام است؟",
                "عنصر اصلی هوا چیست؟",
                "بزرگترین اقیانوس جهان کدام است؟"
            ]
            st.session_state.trivia_question = random.choice(questions)
        
        st.markdown(f"#### سوال: **{st.session_state.trivia_question}**")
        
        answer = st.text_input("پاسخ شما:")
        
        col_ans, col_new = st.columns(2)
        with col_ans:
            if st.button("✅ ثبت پاسخ", use_container_width=True) and answer:
                result = game_system.play_trivia(st.session_state.username, answer)
                
                st.markdown('<div class="game-card">', unsafe_allow_html=True)
                st.markdown(f"### {result['message']}")
                if result['score'] > 0:
                    st.metric("🎖️ امتیاز کسب شده", result['score'])
                    st.balloons()
                st.markdown('</div>', unsafe_allow_html=True)
        
        with col_new:
            if st.button("🔄 سوال جدید", use_container_width=True):
                del st.session_state.trivia_question
                st.rerun()
    
    with tab3:
        st.markdown("### 🧩 بازی حافظه تصویری")
        st.markdown("""
        **توضیحات بازی:**
        - کارت‌ها را به خاطر بسپارید
        - سپس جفت‌های مشابه را پیدا کنید
        - هر جفت درست = 10 امتیاز
        """)
        
        if st.button("🎮 شروع بازی حافظه", use_container_width=True, type="primary"):
            result = game_system.play_memory(st.session_state.username)
            
            st.markdown('<div class="game-card">', unsafe_allow_html=True)
            st.markdown(f"### {result['message']}")
            st.metric("🎖️ امتیاز شما", result['score'])
            
            if result['score'] >= 80:
                st.success("🎉 حافظه فوق‌العاده‌ای دارید!")
            elif result['score'] >= 60:
                st.info("👍 خوب بود! تمرین کنید بهتر می‌شوید")
            
            st.markdown('</div>', unsafe_allow_html=True)
    
    with tab4:
        st.markdown("### 🏆 امتیازات شما")
        
        c.execute("SELECT game, score, time FROM games WHERE user=? ORDER BY id DESC LIMIT 10", 
                  (st.session_state.username,))
        user_games = c.fetchall()
        
        if user_games:
            total_score = sum(g[1] for g in user_games)
            avg_score = total_score / len(user_games) if user_games else 0
            
            col_total, col_avg = st.columns(2)
            with col_total:
                st.metric("🎖️ امتیاز کل", total_score)
            with col_avg:
                st.metric("📊 میانگین", round(avg_score, 1))
            
            st.markdown("#### آخرین بازی‌ها:")
            for game in user_games:
                st.write(f"**{game[0]}** - امتیاز: {game[1]} - زمان: {game[2]}")
        else:
            st.info("🎯 هنوز بازی نکرده‌اید. بازی کنید و امتیاز کسب کنید!")

# --- صفحه کتابخانه ---
def show_library_page():
    st.markdown('<h2 class="section-header">📚 کتابخانه شخصی</h2>', unsafe_allow_html=True)
    
    col_add, col_view = st.columns([1, 2])
    
    with col_add:
        st.markdown("### افزودن کتاب")
        
        with st.form("add_book_form", clear_on_submit=True):
            book_title = st.text_input("عنوان کتاب:")
            book_author = st.text_input("نویسنده:")
            book_desc = st.text_area("توضیحات (اختیاری):", height=100)
            
            submitted = st.form_submit_button("➕ افزودن به کتابخانه", use_container_width=True)
            
            if submitted and book_title:
                book_info = f"{book_title}"
                if book_author:
                    book_info += f" - نویسنده: {book_author}"
                if book_desc:
                    book_info += f" | {book_desc}"
                
                c.execute("INSERT INTO books (user, book, added_at) VALUES (?, ?, ?)",
                         (st.session_state.username, book_info, 
                          datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
                conn.commit()
                st.success("✅ کتاب به کتابخانه اضافه شد!")
                st.rerun()
    
    with col_view:
        st.markdown("### کتاب‌های شما")
        
        c.execute("SELECT id, book, added_at FROM books WHERE user=? ORDER BY id DESC", 
                 (st.session_state.username,))
        books = c.fetchall()
        
        if books:
            for book in books:
                with st.expander(f"📖 {book[1].split('|')[0]}"):
                    st.write(f"**زمان اضافه شدن:** {book[2]}")
                    if "|" in book[1]:
                        st.write(f"**توضیحات:** {book[1].split('|')[1].strip()}")
                    
                    if st.button("🗑️ حذف", key=f"del_book_{book[0]}"):
                        c.execute("DELETE FROM books WHERE id=?", (book[0],))
                        conn.commit()
                        st.rerun()
        else:
            st.info("📚 کتابخانه شما خالی است. کتاب‌های مورد علاقه‌تان را اضافه کنید.")

# --- صفحه کاربران ---
def show_users_page():
    st.markdown('<h2 class="section-header">👥 کاربران پلتفرم</h2>', unsafe_allow_html=True)
    
    tab_follow, tab_following, tab_followers = st.tabs(["دنبال‌کردن", "دنبال‌شوندگان", "دنبال‌کنندگان"])
    
    with tab_follow:
        st.markdown("### سایر کاربران")
        
        c.execute("SELECT username, bio FROM users WHERE username!=? ORDER BY username", 
                 (st.session_state.username,))
        all_users = c.fetchall()
        
        if all_users:
            for user, bio in all_users:
                col_user, col_action = st.columns([3, 1])
                
                with col_user:
                    st.markdown(f"**👤 {user}**")
                    if bio:
                        st.caption(f"{bio[:80]}..." if len(bio) > 80 else bio)
                    else:
                        st.caption("بدون بیوگرافی")
                
                with col_action:
                    c.execute("SELECT * FROM follow WHERE follower=? AND following=?", 
                             (st.session_state.username, user))
                    is_following = c.fetchone() is not None
                    
                    if is_following:
                        if st.button("❌ آنفالو", key=f"unfollow_{user}"):
                            unfollow_user(st.session_state.username, user)
                            st.rerun()
                    else:
                        if st.button("➕ دنبال‌کردن", key=f"follow_{user}"):
                            follow_user(st.session_state.username, user)
                            st.rerun()
        else:
            st.info("👥 کاربر دیگری در پلتفرم وجود ندارد.")
    
    with tab_following:
        st.markdown("### افرادی که دنبال می‌کنید")
        
        following = get_following(st.session_state.username)
        
        if following:
            for user in following:
                col_user, col_action = st.columns([3, 1])
                with col_user:
                    st.write(f"👤 {user}")
                with col_action:
                    if st.button("❌ آنفالو", key=f"unfollow2_{user}"):
                        unfollow_user(st.session_state.username, user)
                        st.rerun()
        else:
            st.info("📭 شما هیچ کاربری را دنبال نمی‌کنید.")
    
    with tab_followers:
        st.markdown("### دنبال‌کنندگان شما")
        
        followers = get_followers(st.session_state.username)
        
        if followers:
            for user in followers:
                st.write(f"👤 {user}")
        else:
            st.info("📭 شما هنوز دنبال‌کننده‌ای ندارید.")

# --- صفحه رده‌بندی ---
def show_leaderboard_page():
    st.markdown('<h2 class="section-header">🏆 جدول رده‌بندی</h2>', unsafe_allow_html=True)
    
    leaderboard = game_system.get_leaderboard(limit=15)
    
    if leaderboard:
        st.markdown("### برترین بازیکنان")
        
        # نمایش 3 نفر اول با مدال
        if len(leaderboard) >= 3:
            cols = st.columns(3)
            medals = ["🥇", "🥈", "🥉"]
            
            for i in range(3):
                with cols[i]:
                    st.markdown(f"### {medals[i]}")
                    st.markdown(f"**{leaderboard[i][0]}**")
                    st.markdown(f"🎖️ **{leaderboard[i][1]}** امتیاز")
                    st.caption(f"🎮 {leaderboard[i][2]} بازی")
        
        st.markdown("---")
        
        # جدول کامل
        st.markdown("#### رده‌بندی کامل")
        
        for i, (user, score, games) in enumerate(leaderboard, 1):
            if i <= 3:
                continue
                
            col_rank, col_user, col_score, col_games = st.columns([1, 3, 2, 2])
            with col_rank:
                st.markdown(f"**{i}.**")
            with col_user:
                st.markdown(f"**{user}**")
            with col_score:
                st.markdown(f"🎖️ {score}")
            with col_games:
                st.markdown(f"🎮 {games}")
            
            if i < len(leaderboard):
                st.markdown("---")
    else:
        st.info("🏆 هنوز کسی بازی نکرده است. اولین نفر باشید!")

# --- صفحه تنظیمات ---
def show_settings_page():
    st.markdown('<h2 class="section-header">⚙️ تنظیمات حساب</h2>', unsafe_allow_html=True)
    
    tab1, tab2, tab3 = st.tabs(["حساب کاربری", "امنیت", "داده‌ها"])
    
    with tab1:
        st.markdown("### اطلاعات حساب")
        
        user_info = get_user_info(st.session_state.username)
        
        if user_info:
            st.write(f"**نام کاربری:** {user_info[0]}")
            st.write(f"**تاریخ عضویت:** {user_info[2]}")
        
        st.markdown("---")
        st.markdown("#### تغییر بیوگرافی")
        
        new_bio = st.text_area("بیوگرافی جدید:", height=100,
                              placeholder="درباره خودتان بنویسید...")
        
        if st.button("💾 ذخیره بیوگرافی", use_container_width=True):
            c.execute("UPDATE users SET bio=? WHERE username=?", 
                     (new_bio, st.session_state.username))
            conn.commit()
            st.success("✅ بیوگرافی به‌روز شد!")
    
    with tab2:
        st.markdown("### 🔒 امنیت و رمز عبور")
        
        current_pass = st.text_input("رمز عبور فعلی:", type="password")
        new_pass = st.text_input("رمز عبور جدید:", type="password")
        confirm_pass = st.text_input("تکرار رمز عبور جدید:", type="password")
        
        if st.button("🔄 تغییر رمز عبور", use_container_width=True, type="primary"):
            if not current_pass or not new_pass or not confirm_pass:
                st.error("❌ لطفا همه فیلدها را پر کنید")
            elif new_pass != confirm_pass:
                st.error("❌ رمزهای عبور جدید مطابقت ندارند")
            elif not authenticate_user(st.session_state.username, current_pass):
                st.error("❌ رمز عبور فعلی اشتباه است")
            else:
                c.execute("UPDATE users SET password=? WHERE username=?", 
                         (hash_password(new_pass), st.session_state.username))
                conn.commit()
                st.success("✅ رمز عبور با موفقیت تغییر کرد!")
    
    with tab3:
        st.markdown("### 🗑️ مدیریت داده‌ها")
        
        st.warning("⚠️ این عملیات قابل بازگشت نیست!")
        
        col1, col2 = st.columns(2)
        
        with col1:
            if st.button("🧹 پاک کردن تمام پست‌های من", use_container_width=True):
                c.execute("DELETE FROM posts WHERE user=?", (st.session_state.username,))
                conn.commit()
                st.success("✅ تمام پست‌های شما پاک شدند!")
        
        with col2:
            if st.button("🗑️ پاک کردن تاریخچه بازی", use_container_width=True):
                c.execute("DELETE FROM games WHERE user=?", (st.session_state.username,))
                conn.commit()
                st.success("✅ تاریخچه بازی‌ها پاک شد!")

# --- صفحه‌بندی اصلی ---
if not st.session_state.logged_in:
    show_login_page()
else:
    show_sidebar()
    
    # مسیریابی صفحات
    pages = {
        "خانه": show_home_page,
        "پروفایل": show_profile_page,
        "چت": show_chat_page,
        "بازی": show_games_page,
        "کتابخانه": show_library_page,
        "کاربران": show_users_page,
        "رده‌بندی": show_leaderboard_page,
        "تنظیمات": show_settings_page
    }
    
    current_page = st.session_state.current_page
    
    if current_page in pages:
        pages[current_page]()
    else:
        show_home_page()

# --- فوتر ---
st.markdown("---")
footer_col1, footer_col2, footer_col3 = st.columns(3)

with footer_col1:
    st.caption("🌐 مگا پلتفرم پرو آنلاین")

with footer_col2:
    status = "🟢 آنلاین" if st.session_state.logged_in else "🔴 آفلاین"
    st.caption(f"وضعیت: {status}")

with footer_col3:
    st.caption(f"🕐 {datetime.now().strftime('%Y/%m/%d - %H:%M:%S')}")

# === اجرای برنامه ===
if __name__ == "__main__":
    # این بخش فقط برای اجرای مستقیم فایل لازم است
    # در Streamlit Cloud خودکار اجرا می‌شود
    pass
