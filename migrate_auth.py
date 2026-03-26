from database import engine, Base
import models

def migrate():
    print("正在建立新的驗證與授權資料表...")
    # create_all 只會建立不存在的資料表，不會影響現有資料
    Base.metadata.create_all(bind=engine)
    print("✅ 資料表建立完成（或已存在）。")

if __name__ == "__main__":
    migrate()
