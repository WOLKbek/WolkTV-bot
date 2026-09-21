import aiosqlite
from typing import Optional, Dict, Any

class Database:
    def __init__(self, db_path: str = "cinema_bot.db"):
        self.db_path = db_path

    async def init_db(self):
        """Jadvallarni yaratish va bazani sozlash"""
        async with aiosqlite.connect(self.db_path) as db:
            # Foydalanuvchilar jadvali
            await db.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    user_id INTEGER PRIMARY KEY,
                    full_name TEXT,
                    username TEXT
                )
            """)

            # Kinolar jadvali
            await db.execute("""
                CREATE TABLE IF NOT EXISTS movies (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    code TEXT UNIQUE NOT NULL,
                    title TEXT NOT NULL,
                    description TEXT,
                    file_id TEXT NOT NULL,
                    views INTEGER DEFAULT 0
                )
            """)
            await db.commit()

    async def add_user(self, user_id: int, full_name: str, username: Optional[str] = None):
        """Foydalanuvchini bazaga saqlash"""
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute(
                "INSERT OR IGNORE INTO users (user_id, full_name, username) VALUES (?, ?, ?)",
                (user_id, full_name, username)
            )
            await db.commit()

    async def add_movie(self, code: str, title: str, description: str, file_id: str) -> bool:
        """Yangi kino qo'shish"""
        try:
            async with aiosqlite.connect(self.db_path) as db:
                await db.execute(
                    "INSERT INTO movies (code, title, description, file_id) VALUES (?, ?, ?, ?)",
                    (code, title, description, file_id)
                )
                await db.commit()
                return True
        except aiosqlite.IntegrityError:
            return False

    async def get_movie_by_code(self, code: str) -> Optional[Dict[str, Any]]:
        """Kino kodi bo'yicha izlash"""
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            async with db.execute("SELECT * FROM movies WHERE code = ?", (code,)) as cursor:
                movie = await cursor.fetchone()
                if movie:
                    await db.execute("UPDATE movies SET views = views + 1 WHERE code = ?", (code,))
                    await db.commit()
                    return dict(movie)
                return None