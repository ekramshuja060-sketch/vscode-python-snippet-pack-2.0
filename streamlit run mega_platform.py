# mega_platform_pro_online.py
import streamlit as st
import sqlite3
import hashlib
import random
from datetime import datetime
import asyncio
import threading
import queue
import uuid

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
c.execute('''CREATE TABLE IF NOT EXISTS chat_rooms 
             (id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT, created_by TEXT)''')
c.execute('''CREATE TABLE IF NOT EXISTS chat_messages 
             (id INTEGER PRIMARY KEY AUTOINCREMENT, room TEXT, sender TEXT, content TEXT, time TEXT)''')
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

# === شبیه‌ساز ChatGPT ===
class ChatGPTSimulator:
    @staticmethod
    def generate_poem(topic):
        poems = [
            f"زندگی و {topic}، بازی و امید، هر لحظه یک قصه جدید.",
            f"{topic} در دل شب، مثل نور ستاره‌ها، می‌درخشد و می‌ماند در خاطره‌ها.",
            f"پرنده‌ای بر شاخه {topic} نشسته بود، آواز عشق و زندگی می‌خواند.",
            f"باد می‌وزد، برگ {topic} می‌رقصد، زمین نفس می‌کشد در سکوت شب."
        ]
        return random.choice(poems)

    @staticmethod
    def generate_story(topic):
        stories = [
            f"روزی روزگاری در دنیایی پر از {topic}، قهرمان ما سفر خود را آغاز کرد.",
            f"در شهری پر از {topic}، دو دوست تصمیم گرفتند رازهای دنیا را کشف کنند.",
            f"پادشاه {topic} بر تخت نشسته بود و به فکر صلح جهان بود.",
            f"جوانی با شنیدن نام {topic}، تصمیم گرفت دنیا را تغییر دهد."
        ]
        return random.choice(stories)

    @staticmethod
    def generate_advice(topic):
        advices = [
            f"برای موفقیت در {topic}، صبر و پشتکار لازم است.",
            f"{topic} را با عشق انجام دهید تا نتیجه بهتری بگیرید.",
            f"در زمینه {topic}، یادگیری مداوم رمز موفقیت است.",
            f"{topic} مانند رودخانه است، باید با جریان آن همراه شوید."
        ]
        return random.choice(advices)

chatgpt = ChatGPTSimulator()

# === سیستم چت آنلاین ===
class ChatSystem:
    def __init__(self):
        self.messages_queue = queue.Queue()
        self.active_users = {}
        self.chat_rooms = {
            "عمومی": [],
            "دوستانه": [],
            "تکنولوژی": [],
            "ورزشی": []
        }
    
    def send_message(self, room, sender, message):
        timestamp = datetime.now().strftime("%H:%M:%S")
        msg_data = {
            "room": room,
            "sender": sender,
            "message": message,
            "time": timestamp,
            "id": str(uuid.uuid4())
        }
        
        # ذخیره در دیتابیس
        c.execute("INSERT INTO chat_messages (room, sender, content, time) VALUES (?, ?, ?, ?)",
                  (room, sender, message, timestamp))
        conn.commit()
        
        # ارسال به صف
        self.messages_queue.put(msg_data)
        return msg_data
    
    def get_messages(self, room, limit=50):
        c.execute("SELECT sender, content, time FROM chat_messages WHERE room=? ORDER BY time DESC LIMIT ?", 
                  (room, limit))
        messages = c.fetchall()
        return [{"sender": m[0], "message": m[1], "time": m[2]} for m in messages[::-1]]
    
    def create_room(self, name, creator):
        if name not in self.chat_rooms:
            self.chat_rooms[name] = []
            c.execute("INSERT INTO chat_rooms (name, created_by) VALUES (?, ?)", (name, creator))
            conn.commit()
            return True
        return False
    
    def get_rooms(self):
        c.execute("SELECT name, created_by FROM chat_rooms")
        rooms = c.fetchall()
        return [{"name": r[0], "creator": r[1]} for r in rooms]

chat_system = ChatSystem()

# === سیستم بازی ===
class GameSystem:
    @staticmethod
    def play_guess_number(user, number):
        secret = random.randint(1, 100)
        score = max(0, 100 - abs(secret - number) * 10)
        
        c.execute("INSERT INTO games (user, game, score, time) VALUES (?, ?, ?, ?)",
                  (user, "Guess Number", score, datetime.now().isoformat()))
        conn.commit()
        
        return {
            "secret": secret,
            "score": score,
            "message": f"عدد مخفی {secret} بود! شما {number} گفتید. امتیاز: {score}"
        }
    
    @staticmethod
    def play_trivia(user, answer):
        questions = [
            {"question": "پایتخت ایران کجاست؟", "answer": "تهران", "score": 100},
            {"question": "بزرگترین سیاره منظومه شمسی؟", "answer": "مشتری", "score": 100},
            {"question": "نویسنده شاهنامه؟", "answer": "فردوسی", "score": 100},
        ]
        q = random.choice(questions)
        
        if answer.lower() == q["answer"].lower():
            score = q["score"]
            message = f"درست جواب دادید! امتیاز: {score}"
        else:
            score = 0
            message = f"پاسخ صحیح: {q['answer']}"
        
        c.execute("INSERT INTO games (user, game, score, time) VALUES (?, ?, ?, ?)",
                  (user, "Trivia", score, datetime.now().isoformat()))
        conn.commit()
        
        return {"score": score, "message": message, "question": q["question"]}
    
    @staticmethod
    def get_leaderboard():
        c.execute("SELECT user, SUM(score), COUNT(*) FROM games GROUP BY user ORDER BY SUM(score) DESC LIMIT 10")
        return c.fetchall()

game_system = GameSystem()

# === رابط کاربری Streamlit ===
st.set_page_config(
    page_title="مگا پلتفرم پرو آنلاین",
    layout="wide",
    initial_sidebar_state="expanded",
    page_icon="🌐"
)

# استایل سفارشی
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        color: #1E88E5;
        text-align: center;
        margin-bottom: 2rem;
    }
    .section-header {
        font-size: 1.8rem;
        color: #0D47A1;
        margin-top: 2rem;
        margin-bottom: 1rem;
        border-bottom: 2px solid #BBDEFB;
        padding-bottom: 0.5rem;
    }
    .card {
        background-color: #E3F2FD;
        padding: 1.5rem;
        border-radius: 10px;
        margin-bottom: 1rem;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    }
    .message-bubble {
        background-color: #E8F5E9;
        padding: 0.8rem;
        border-radius: 15px;
        margin-bottom: 0.5rem;
        max-width: 80%;
    }
    .message-sender {
        font-weight: bold;
        color: #2E7D32;
    }
    .game-card {
        background: linear-gradient(135deg, #FFECB3 0%, #FFE082 100%);
        padding: 1rem;
        border-radius: 10px;
        margin-bottom: 1rem;
    }
</style>
""", unsafe_allow_html=True)

# --- مدیریت وضعیت login ---
if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False
    st.session_state.username = None
    st.session_state.current_page = "home"
    st.session_state.chat_room = "عمومی"
    st.session_state.game_input = ""
    st.session_state.messages = []

# --- صفحه login/register ---
def show_login_page():
    st.markdown('<h1 class="main-header">🌐 مگا پلتفرم پرو آنلاین</h1>', unsafe_allow_html=True)
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown('<div class="card">', unsafe_allow_html=True)
        st.subheader("🔐 ورود به سیستم")
        login_username = st.text_input("نام کاربری", key="login_user")
        login_password = st.text_input("رمز عبور", type="password", key="login_pass")
        
        if st.button("ورود", use_container_width=True):
            if authenticate_user(login_username, login_password):
                st.session_state.logged_in = True
                st.session_state.username = login_username
                st.success(f"خوش آمدی {login_username}! 🎉")
                st.rerun()
            else:
                st.error("نام کاربری یا رمز عبور اشتباه است!")
        st.markdown('</div>', unsafe_allow_html=True)
    
    with col2:
        st.markdown('<div class="card">', unsafe_allow_html=True)
        st.subheader("📝 ثبت‌نام جدید")
        reg_username = st.text_input("نام کاربری جدید", key="reg_user")
        reg_password = st.text_input("رمز عبور جدید", type="password", key="reg_pass")
        reg_bio = st.text_area("بیوگرافی (اختیاری)", key="reg_bio")
        
        if st.button("ثبت‌نام", use_container_width=True):
            if create_user(reg_username, reg_password, reg_bio):
                st.success("ثبت‌نام موفق! ✅ اکنون وارد شوید.")
            else:
                st.error("این نام کاربری قبلاً استفاده شده است!")
        st.markdown('</div>', unsafe_allow_html=True)
    
    # نمایش آمار
    st.markdown("---")
    col_stats1, col_stats2, col_stats3 = st.columns(3)
    with col_stats1:
        c.execute("SELECT COUNT(*) FROM users")
        user_count = c.fetchone()[0]
        st.metric("👥 تعداد کاربران", user_count)
    with col_stats2:
        c.execute("SELECT COUNT(*) FROM posts")
        post_count = c.fetchone()[0]
        st.metric("📝 تعداد پست‌ها", post_count)
    with col_stats3:
        c.execute("SELECT COUNT(*) FROM games")
        game_count = c.fetchone()[0]
        st.metric("🎮 تعداد بازی‌ها", game_count)

# --- نوار کناری منو ---
def show_sidebar():
    with st.sidebar:
        st.markdown(f"### 👋 سلام {st.session_state.username}!")
        
        # اطلاعات کاربر
        c.execute("SELECT bio FROM users WHERE username=?", (st.session_state.username,))
        user_info = c.fetchone()
        if user_info and user_info[0]:
            st.info(f"📝 بیوگرافی: {user_info[0]}")
        
        # آمار سریع
        followers = len(get_followers(st.session_state.username))
        following = len(get_following(st.session_state.username))
        col1, col2 = st.columns(2)
        with col1:
            st.metric("دنبال‌کنندگان", followers)
        with col2:
            st.metric("دنبال‌شوندگان", following)
        
        st.markdown("---")
        
        # منوی اصلی
        menu_options = {
            "🏠 صفحه اصلی": "home",
            "📱 پروفایل": "profile",
            "📝 پست‌ها": "posts",
            "💬 چت آنلاین": "chat",
            "🎮 بازی‌ها": "games",
            "📚 کتابخانه": "library",
            "🌟 دنبال‌کردن": "follow",
            "⚙️ تنظیمات": "settings"
        }
        
        selected = st.radio(
            "منوی اصلی",
            list(menu_options.keys()),
            index=list(menu_options.values()).index(st.session_state.current_page) 
            if st.session_state.current_page in menu_options.values() else 0
        )
        
        st.session_state.current_page = menu_options[selected]
        
        st.markdown("---")
        
        # دکمه خروج
        if st.button("🚪 خروج از سیستم", use_container_width=True):
            st.session_state.logged_in = False
            st.session_state.username = None
            st.session_state.current_page = "home"
            st.rerun()

# --- صفحه اصلی ---
def show_home_page():
    st.markdown('<h2 class="section-header">🏠 فید اخبار و فعالیت‌ها</h2>', unsafe_allow_html=True)
    
    # پست جدید
    with st.form(key="new_post_form"):
        post_content = st.text_area("✍️ چه چیزی در ذهنت میگذره؟", height=100)
        post_type = st.selectbox("نوع پست:", ["پست معمولی", "شعر", "داستان", "نکته"])
        col1, col2 = st.columns(2)
        with col1:
            submit_post = st.form_submit_button("📤 ارسال پست", use_container_width=True)
        with col2:
            if post_type == "شعر":
                generate_poem = st.form_submit_button("🎭 تولید شعر خودکار", use_container_width=True)
            elif post_type == "داستان":
                generate_story = st.form_submit_button("📖 تولید داستان خودکار", use_container_width=True)
            else:
                generate_story = False
                generate_poem = False
        
        if submit_post and post_content:
            post_type_map = {"پست معمولی": "text", "شعر": "poem", "داستان": "story", "نکته": "tip"}
            c.execute("INSERT INTO posts (user, content, type, time) VALUES (?, ?, ?, ?)",
                      (st.session_state.username, post_content, post_type_map[post_type], 
                       datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
            conn.commit()
            st.success("پست شما منتشر شد! ✅")
            st.rerun()
        
        if generate_poem:
            topic = st.text_input("موضوع شعر را وارد کنید:")
            if topic:
                poem = chatgpt.generate_poem(topic)
                st.text_area("شعر تولید شده:", poem, height=150)
    
    st.markdown("---")
    
    # نمایش پست‌ها
    st.subheader("📜 آخرین پست‌ها")
    
    following_users = get_following(st.session_state.username)
    following_users.append(st.session_state.username)
    
    if following_users:
        placeholders = ", ".join(["?"] * len(following_users))
        c.execute(f"""
            SELECT user, content, type, time 
            FROM posts 
            WHERE user IN ({placeholders}) 
            ORDER BY id DESC 
            LIMIT 20
        """, following_users)
        
        posts = c.fetchall()
        
        if posts:
            for post in posts:
                with st.container():
                    st.markdown('<div class="card">', unsafe_allow_html=True)
                    
                    # هدر پست
                    col_avatar, col_info = st.columns([1, 10])
                    with col_avatar:
                        st.write("👤")
                    with col_info:
                        st.write(f"**{post[0]}** · {post[3]}")
                    
                    # محتوای پست
                    if post[2] == "poem":
                        st.markdown(f"*🎭 شعر:*\n\n{post[1]}")
                    elif post[2] == "story":
                        st.markdown(f"*📖 داستان:*\n\n{post[1]}")
                    elif post[2] == "tip":
                        st.markdown(f"*💡 نکته:*\n\n{post[1]}")
                    else:
                        st.write(post[1])
                    
                    # دکمه‌های تعامل
                    col_like, col_comment, col_share = st.columns(3)
                    with col_like:
                        st.button("❤️ لایک", key=f"like_{post[0]}_{post[3]}", use_container_width=True)
                    with col_comment:
                        st.button("💬 نظر", key=f"comment_{post[0]}_{post[3]}", use_container_width=True)
                    with col_share:
                        st.button("↪️ اشتراک", key=f"share_{post[0]}_{post[3]}", use_container_width=True)
                    
                    st.markdown('</div>', unsafe_allow_html=True)
        else:
            st.info("هنوز پستی وجود ندارد. اولین پست را شما ایجاد کنید!")
    else:
        st.warning("شما هیچ کاربری را دنبال نکرده‌اید. به بخش دنبال‌کردن بروید.")

# --- صفحه پروفایل ---
def show_profile_page():
    st.markdown('<h2 class="section-header">👤 پروفایل کاربری</h2>', unsafe_allow_html=True)
    
    col1, col2 = st.columns([1, 2])
    
    with col1:
        st.markdown("### اطلاعات شخصی")
        c.execute("SELECT bio FROM users WHERE username=?", (st.session_state.username,))
        bio = c.fetchone()[0]
        
        new_bio = st.text_area("بیوگرافی شما:", value=bio if bio else "", height=150)
        if st.button("💾 ذخیره تغییرات", use_container_width=True):
            c.execute("UPDATE users SET bio=? WHERE username=?", (new_bio, st.session_state.username))
            conn.commit()
            st.success("بیوگرافی به‌روز شد! ✅")
        
        # آمار کاربر
        st.markdown("---")
        st.markdown("### 📊 آمار شما")
        c.execute("SELECT COUNT(*) FROM posts WHERE user=?", (st.session_state.username,))
        post_count = c.fetchone()[0]
        c.execute("SELECT COUNT(*) FROM games WHERE user=?", (st.session_state.username,))
        game_count = c.fetchone()[0]
        c.execute("SELECT COUNT(*) FROM books WHERE user=?", (st.session_state.username,))
        book_count = c.fetchone()[0]
        
        st.metric("پست‌ها", post_count)
        st.metric("بازی‌ها", game_count)
        st.metric("کتاب‌ها", book_count)
    
    with col2:
        st.markdown("### فعالیت‌های اخیر")
        
        # آخرین پست‌ها
        st.markdown("#### 📝 آخرین پست‌های شما")
        c.execute("SELECT content, type, time FROM posts WHERE user=? ORDER BY id DESC LIMIT 5", 
                  (st.session_state.username,))
        user_posts = c.fetchall()
        
        if user_posts:
            for post in user_posts:
                with st.expander(f"{post[2]} - {post[1]}"):
                    st.write(post[0])
        else:
            st.info("هنوز پستی منتشر نکرده‌اید.")
        
        # آخرین بازی‌ها
        st.markdown("#### 🎮 آخرین بازی‌های شما")
        c.execute("SELECT game, score, time FROM games WHERE user=? ORDER BY id DESC LIMIT 5", 
                  (st.session_state.username,))
        user_games = c.fetchall()
        
        if user_games:
            for game in user_games:
                st.write(f"{game[2]}: {game[0]} - امتیاز: {game[1]}")
        else:
            st.info("هنوز بازی نکرده‌اید.")

# --- صفحه چت آنلاین ---
def show_chat_page():
    st.markdown('<h2 class="section-header">💬 چت آنلاین</h2>', unsafe_allow_html=True)
    
    # انتخاب اتاق چت
    col_rooms, col_create = st.columns([3, 1])
    
    with col_rooms:
        rooms = chat_system.get_rooms()
        room_names = ["عمومی", "دوستانه", "تکنولوژی", "ورزشی"] + [r["name"] for r in rooms]
        selected_room = st.selectbox("اتاق چت:", room_names, 
                                    index=room_names.index(st.session_state.chat_room) 
                                    if st.session_state.chat_room in room_names else 0)
        st.session_state.chat_room = selected_room
    
    with col_create:
        new_room = st.text_input("اتاق جدید:", placeholder="نام اتاق")
        if st.button("➕ ایجاد"):
            if new_room and chat_system.create_room(new_room, st.session_state.username):
                st.success(f"اتاق {new_room} ایجاد شد!")
                st.rerun()
    
    st.markdown(f"### اتاق: {st.session_state.chat_room}")
    
    # نمایش پیام‌ها
    chat_container = st.container(height=400)
    
    with chat_container:
        messages = chat_system.get_messages(st.session_state.chat_room, limit=30)
        
        for msg in messages:
            if msg["sender"] == st.session_state.username:
                st.markdown(f"""
                <div style="text-align: right; margin-bottom: 10px;">
                    <div style="background-color: #DCF8C6; padding: 10px; border-radius: 15px; display: inline-block; max-width: 70%;">
                        <strong>شما</strong> ({msg['time']}):<br>
                        {msg['message']}
                    </div>
                </div>
                """, unsafe_allow_html=True)
            else:
                st.markdown(f"""
                <div style="text-align: left; margin-bottom: 10px;">
                    <div style="background-color: #FFFFFF; padding: 10px; border-radius: 15px; display: inline-block; max-width: 70%;">
                        <strong>{msg['sender']}</strong> ({msg['time']}):<br>
                        {msg['message']}
                    </div>
                </div>
                """, unsafe_allow_html=True)
    
    # ارسال پیام جدید
    col_msg, col_btn = st.columns([4, 1])
    with col_msg:
        new_message = st.text_input("پیام شما:", key="new_chat_message", 
                                   placeholder="پیام خود را بنویسید...")
    with col_btn:
        send_button = st.button("📤 ارسال", use_container_width=True)
    
    if send_button and new_message:
        chat_system.send_message(st.session_state.chat_room, 
                                st.session_state.username, 
                                new_message)
        st.rerun()

# --- صفحه بازی‌ها ---
def show_games_page():
    st.markdown('<h2 class="section-header">🎮 بازی‌های آنلاین</h2>', unsafe_allow_html=True)
    
    tab1, tab2, tab3 = st.tabs(["🎯 بازی اعداد", "🧠 سوالات هوش", "🏆 جدول رده‌بندی"])
    
    with tab1:
        st.markdown("### 🎯 حدس عدد")
        st.write("عدد بین 1 تا 100 را حدس بزنید!")
        
        guess_number = st.number_input("عدد شما:", min_value=1, max_value=100, value=50)
        
        if st.button("🔍 حدس بزن", use_container_width=True):
            result = game_system.play_guess_number(st.session_state.username, guess_number)
            st.markdown('<div class="game-card">', unsafe_allow_html=True)
            st.write(f"**نتیجه:** {result['message']}")
            st.metric("امتیاز شما", result['score'])
            st.markdown('</div>', unsafe_allow_html=True)
    
    with tab2:
        st.markdown("### 🧠 مسابقه اطلاعات عمومی")
        
        if 'current_question' not in st.session_state:
            questions = [
                "پایتخت ایران کجاست؟",
                "بزرگترین سیاره منظومه شمسی چیست؟",
                "نویسنده شاهنامه کیست؟",
                "بلندترین کوه جهان چه نام دارد؟",
                "رنگین کمان چند رنگ دارد؟"
            ]
            st.session_state.current_question = random.choice(questions)
        
        st.write(f"**سوال:** {st.session_state.current_question}")
        
        answer = st.text_input("پاسخ شما:")
        
        col_ans, col_new = st.columns(2)
        with col_ans:
            if st.button("✅ ارسال پاسخ", use_container_width=True) and answer:
                result = game_system.play_trivia(st.session_state.username, answer)
                st.markdown('<div class="game-card">', unsafe_allow_html=True)
                st.write(f"**نتیجه:** {result['message']}")
                if result['score'] > 0:
                    st.balloons()
                st.markdown('</div>', unsafe_allow_html=True)
        
        with col_new:
            if st.button("🔄 سوال جدید", use_container_width=True):
                del st.session_state.current_question
                st.rerun()
    
    with tab3:
        st.markdown("### 🏆 جدول رده‌بندی")
        
        leaderboard = game_system.get_leaderboard()
        
        if leaderboard:
            st.markdown('<div class="card">', unsafe_allow_html=True)
            for i, (user, total_score, games_count) in enumerate(leaderboard, 1):
                emoji = "🥇" if i == 1 else "🥈" if i == 2 else "🥉" if i == 3 else f"{i}."
                
                col_rank, col_user, col_score, col_games = st.columns([1, 3, 2, 2])
                with col_rank:
                    st.write(f"**{emoji}**")
                with col_user:
                    st.write(f"**{user}**")
                with col_score:
                    st.write(f"🏅 {total_score}")
                with col_games:
                    st.write(f"🎮 {games_count}")
                
                if i < len(leaderboard):
                    st.markdown("---")
            st.markdown('</div>', unsafe_allow_html=True)
        else:
            st.info("هنوز کسی بازی نکرده است!")

# --- صفحه کتابخانه ---
def show_library_page():
    st.markdown('<h2 class="section-header">📚 کتابخانه شخصی</h2>', unsafe_allow_html=True)
    
    col_add, col_view = st.columns([1, 2])
    
    with col_add:
        st.markdown("### افزودن کتاب")
        book_title = st.text_input("عنوان کتاب:")
        book_author = st.text_input("نویسنده:")
        
        if st.button("➕ افزودن به کتابخانه", use_container_width=True) and book_title:
            c.execute("INSERT INTO books (user, book) VALUES (?, ?)", 
                     (st.session_state.username, f"{book_title} - {book_author}"))
            conn.commit()
            st.success("کتاب به کتابخانه اضافه شد! ✅")
            st.rerun()
    
    with col_view:
        st.markdown("### کتاب‌های شما")
        c.execute("SELECT book FROM books WHERE user=? ORDER BY id DESC", 
                 (st.session_state.username,))
        books = c.fetchall()
        
        if books:
            for i, book in enumerate(books):
                col_book, col_del = st.columns([5, 1])
                with col_book:
                    st.write(f"📖 {book[0]}")
                with col_del:
                    if st.button("🗑️", key=f"del_book_{i}", use_container_width=True):
                        c.execute("DELETE FROM books WHERE user=? AND book=?", 
                                 (st.session_state.username, book[0]))
                        conn.commit()
                        st.rerun()
        else:
            st.info("کتابی به کتابخانه اضافه نکرده‌اید.")

# --- صفحه دنبال‌کردن ---
def show_follow_page():
    st.markdown('<h2 class="section-header">🌟 دنبال‌کردن کاربران</h2>', unsafe_allow_html=True)
    
    tab1, tab2, tab3 = st.tabs(["👥 کاربران جدید", "✅ دنبال‌شوندگان", "❤️ دنبال‌کنندگان"])
    
    with tab1:
        st.markdown("### سایر کاربران")
        c.execute("SELECT username, bio FROM users WHERE username!=?", (st.session_state.username,))
        all_users = c.fetchall()
        
        if all_users:
            for user, bio in all_users:
                col_user, col_follow = st.columns([4, 1])
                with col_user:
                    st.write(f"**{user}**")
                    if bio:
                        st.caption(bio[:100] + "..." if len(bio) > 100 else bio)
                with col_follow:
                    c.execute("SELECT * FROM follow WHERE follower=? AND following=?", 
                             (st.session_state.username, user))
                    is_following = c.fetchone() is not None
                    
                    if is_following:
                        if st.button("❌ آنفالو", key=f"unfollow_{user}", use_container_width=True):
                            unfollow_user(st.session_state.username, user)
                            st.rerun()
                    else:
                        if st.button("➕ دنبال‌کردن", key=f"follow_{user}", use_container_width=True):
                            follow_user(st.session_state.username, user)
                            st.rerun()
        else:
            st.info("کاربر دیگری وجود ندارد.")
    
    with tab2:
        st.markdown("### افرادی که دنبال می‌کنید")
        following = get_following(st.session_state.username)
        
        if following:
            for user in following:
                col_user, col_unfollow = st.columns([4, 1])
                with col_user:
                    st.write(f"👤 {user}")
                with col_unfollow:
                    if st.button("❌ آنفالو", key=f"unfollow2_{user}", use_container_width=True):
                        unfollow_user(st.session_state.username, user)
                        st.rerun()
        else:
            st.info("شما هنوز کسی را دنبال نکرده‌اید.")
    
    with tab3:
        st.markdown("### دنبال‌کنندگان شما")
        followers = get_followers(st.session_state.username)
        
        if followers:
            for user in followers:
                st.write(f"👤 {user}")
        else:
            st.info("شما هنوز دنبال‌کننده‌ای ندارید.")

# --- صفحه تنظیمات ---
def show_settings_page():
    st.markdown('<h2 class="section-header">⚙️ تنظیمات</h2>', unsafe_allow_html=True)
    
    st.markdown("### تنظیمات حساب کاربری")
    
    # تغییر رمز عبور
    st.subheader("🔒 تغییر رمز عبور")
    current_pass = st.text_input("رمز عبور فعلی:", type="password")
    new_pass = st.text_input("رمز عبور جدید:", type="password")
    confirm_pass = st.text_input("تکرار رمز عبور جدید:", type="password")
    
    if st.button("🔄 تغییر رمز عبور", use_container_width=True):
        if authenticate_user(st.session_state.username, current_pass):
            if new_pass == confirm_pass:
                c.execute("UPDATE users SET password=? WHERE username=?", 
                         (hash_password(new_pass), st.session_state.username))
                conn.commit()
                st.success("رمز عبور با موفقیت تغییر کرد! ✅")
            else:
                st.error("رمزهای عبور جدید مطابقت ندارند!")
        else:
            st.error("رمز عبور فعلی اشتباه است!")
    
    st.markdown("---")
    
    # پاک کردن داده‌ها
    st.subheader("🗑️ مدیریت داده‌ها")
    
    if st.button("🧹 پاک کردن تمام پست‌های من", use_container_width=True):
        c.execute("DELETE FROM posts WHERE user=?", (st.session_state.username,))
        conn.commit()
        st.warning("تمام پست‌های شما پاک شدند!")
    
    st.markdown("---")
    
    # اطلاعات سیستم
    st.subheader("📊 اطلاعات سیستم")
    
    c.execute("SELECT COUNT(*) FROM users")
    total_users = c.fetchone()[0]
    c.execute("SELECT COUNT(*) FROM posts")
    total_posts = c.fetchone()[0]
    c.execute("SELECT COUNT(*) FROM messages")
    total_messages = c.fetchone()[0]
    
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("کاربران کل", total_users)
    with col2:
        st.metric("پست‌های کل", total_posts)
    with col3:
        st.metric("پیام‌های کل", total_messages)

# --- صفحه‌بندی اصلی ---
if not st.session_state.logged_in:
    show_login_page()
else:
    show_sidebar()
    
    # نمایش صفحه انتخابی
    pages = {
        "home": show_home_page,
        "profile": show_profile_page,
        "posts": show_home_page,  # همان صفحه اصلی
        "chat": show_chat_page,
        "games": show_games_page,
        "library": show_library_page,
        "follow": show_follow_page,
        "settings": show_settings_page
    }
    
    if st.session_state.current_page in pages:
        pages[st.session_state.current_page]()
    else:
        show_home_page()

# --- فوتر ---
st.markdown("---")
col_footer1, col_footer2, col_footer3 = st.columns(3)
with col_footer1:
    st.caption("🌐 مگا پلتفرم پرو آنلاین")
with col_footer2:
    st.caption(f"👤 کاربر: {st.session_state.username if st.session_state.logged_in else 'مهمان'}")
with col_footer3:
    st.caption(f"🕐 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
