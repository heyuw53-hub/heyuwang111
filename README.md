# TP 数据收集网站（Streamlit）

## 结构
```
Accueil.py              首页（学生填写须知）
pages/1_Polarographie.py  Polaro 表单
pages/2_UV-Visible.py     UV 表单
pages/3_Resultats_etudiants.py 学生结果页：本年分布 + 自己 binôme 的位置（红点）
pages/4_Resultats_enseignant.py 教师页（密码）：总览 / 组内 / 组间 / 年际比较 / 导出 Excel
config.py               所有字段、单位、校验范围、组别列表 —— 改表单只改这里
saisie.py               表单与标准化逻辑
incertitudes.py         每个 binôme 的不确定度（按 ECPM-TPSA-MOP-003）：Polaro 只算 B 类，UV 算 A 类 + B 类
db.py                   数据库（本地 SQLite，线上 PostgreSQL）
analysis.py             清洗、统计、作图、导出（改写自原来的三个脚本）
```

## 本地运行
```bash
pip install -r requirements.txt
cp .streamlit/secrets.toml.example .streamlit/secrets.toml   # 修改 ADMIN_PASSWORD
streamlit run Accueil.py
```
本地不设 DATABASE_URL 时自动使用 SQLite（tp_data.db）。

## 上线（免费）
1. **数据库**：在 supabase.com 新建项目 → Connect → 复制 *Session pooler* 的 URI，
   把开头 `postgresql://` 改成 `postgresql+psycopg2://`。表会在首次运行时自动创建。
2. **代码**：推送到 GitHub（`secrets.toml` 已在 .gitignore 中，不会被上传）。
3. **部署**：share.streamlit.io → New app → 主文件选 `Accueil.py`
   → Advanced settings → Secrets 粘贴：
   ```toml
   ADMIN_PASSWORD = "你的密码"
   DATABASE_URL = "postgresql+psycopg2://..."
   ```
4. 把网址（或二维码）发给学生。

注意：Supabase 免费项目连续 7 天无访问会暂停，TP 前登录后台确认一下；
Streamlit Cloud 应用长时间无人访问会休眠，第一次打开需要等几十秒。
