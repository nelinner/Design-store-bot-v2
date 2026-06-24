import asyncio, logging, re, urllib.request, os
from datetime import datetime
from io import BytesIO
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup, BufferedInputFile
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.enums import ParseMode
from aiogram.client.default import DefaultBotProperties
from playwright.async_api import async_playwright

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

BOT_TOKEN = "8985680067:AAHROlAyLyMNf91fXw-IdtwQRJxcwda7OG8"
CHANNEL_USERNAME = "@tgdesignstore"
CHANNEL_ID = "@tgdesignstore"
REVIEWS_CHANNEL = "@otzdesingstore"
ADMIN_USERNAME = "nelinner"

MAIN_MENU_IMAGE = "https://ibb.co/RpCTX9X0"
DIRECT_PURCHASE_IMAGE = "https://ibb.co/V0Chtymv"

SELLERS = {
    "linner": {"name":"Linner","description":"💎 Профессиональный дизайнер каналов и логотипов","image_url":"https://ibb.co/8LXw3Fw8",
              "fields":{"Username":"@nelinner","Портфолио":"@worklinner","Отзывы":"@otzlinner","Прайс":"https://t.me/pricedesignstore/2"}},
    "loz": {"name":"Loz","description":"🎨 Креативный дизайн и уникальный стиль","image_url":"https://ibb.co/Xk5NGtd0",
           "fields":{"Username":"@loz306","Портфолио":"@lozportfolio","Отзывы":"Вручение от руководителя","Прайс":"Узнавать в лс"}},
    "rassvet": {"name":"Рассвет","description":"🌅 Стильные решения для твоего проекта","image_url":"https://ibb.co/Tqc8D19p",
               "fields":{"Username":"@PACBETTT","Портфолио":"https://t.me/rasvetDesignn","Отзывы":"вручение от руководителя","Прайс":"https://t.me/pricedesignstore/3"}},
    "omut": {"name":"Омут сомнений // asc ","description":"🌀 Минимализм и атмосферный дизайн","image_url":"https://ibb.co/4nVRrgp9",
            "fields":{"Username":"@xaywd","Портфолио":"https://t.me/movaningfx","Отзывы":"вручение от руководителя","Прайс":"https://t.me/pricedesignstore/4"}},
}

RULES_TEXT = (
    "📃 <b>Регламент магазина</b>\n\n"
    "1. Перед покупкой обязательно ознакомьтесь с портфолио и отзывами продавца.\n"
    "2. Все сделки проводятся только через официальных продавцов, указанных в боте.\n"
    "3. Запрещено передавать контакты продавцов третьим лицам без согласования.\n"
    "4. Магазин не несёт ответственности за качество работ, если вы обратились к исполнителю "
    "напрямую, минуя этот бот.\n"
    "5. Любые споры решаются через руководителя @nelinner.\n"
    "6. Сохраняйте все чеки и переписки до завершения сделки.\n\n"
    "Нарушение регламента может привести к блокировке доступа к боту."
)

SUPPORT_TEXT = (
    "📞 <b>Поддержка бота</b>\n\n"
    "Если у вас возникли вопросы, проблемы с ботом или нужна консультация — "
    "напишите руководителю: <b>@nelinner</b>\n\n"
    "Пожалуйста, опишите вашу проблему максимально подробно, приложите скриншоты при необходимости."
)

DIRECT_PURCHASE_TEXT = (
    "🛍️ <b>Покупка дизайна от нашего магазина через нашего бота</b>\n"
    "— мы добавили возможность покупать товар напрямую у магазина, и вы также можете "
    "приобрести товар с дизайном как у отдельных продавцов, и также напрямую от магазина\n\n"
    "📃 Теперь вы можете выбирать между продавцами, и магазином и решать где именно "
    "тебе покупать наши услуги\n\n"
    "🛍️ <b>Price</b>\n"
    "1. Аватарка = 90₽\n"
    "2. Баннер = 90₽\n"
    "3. Шапка профиля = 100₽\n"
    "4. Оформление для VK/TG каналов = 110₽\n"
    "5. Превью для видео = 90₽\n"
    "6. Другой дизайн = 95₽\n\n"
    "‼️ При покупке этих услуг, мы редактируем только два раза дизайн. "
    "Если за два исправление вам все не нравится то уже приносим извинения и "
    "взять работу такую какую уже есть. Но есть исключения мы можем изменить "
    "некоторые элементы на дизайне которые вы не хотите видеть"
)

# --- НОВЫЙ HTML-ШАБЛОН (твой) ---
HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="ru">
<head>
<meta charset="UTF-8">
<style>
*{margin:0;padding:0;box-sizing:border-box}
body{width:1080px;height:1080px;overflow:hidden;font-family:Arial,sans-serif;
     background:radial-gradient(circle at center,#103d39 0%,#031414 50%,#000000 100%)}
.container{position:relative;width:1080px;height:1080px}
.design{position:absolute;top:40px;left:350px;color:#7CFFD0;font-size:72px;font-style:italic}
.title{position:absolute;top:120px;left:60px;color:white;font-size:110px;font-weight:700}
.subtitle{position:absolute;top:240px;left:70px;color:white;font-size:42px}
.makeby{position:absolute;right:60px;top:120px;color:#7CFFD0;font-size:42px;font-weight:bold}
.badge{position:absolute;right:60px;top:180px;background:linear-gradient(180deg,#a4d8af,#6d9775);color:white;padding:18px 35px;border-radius:25px;font-size:40px;font-weight:bold}
.review{position:absolute;left:60px;top:330px;width:960px;min-height:450px;background:rgba(255,255,255,.35);border:4px solid rgba(255,255,255,.9);border-radius:40px;backdrop-filter:blur(8px);padding:30px}
.header{display:flex;align-items:center}
.avatar{width:100px;height:100px;border-radius:50%;background:radial-gradient(circle,#86ffd1,#337c67);margin-right:20px}
.name{color:white;font-size:56px;font-weight:bold}
.username{display:inline-block;margin-top:10px;background:#d8d8d8;color:white;padding:8px 20px;border-radius:20px;font-size:34px}
.line{margin:25px 0;height:2px;background:#bcbcbc}
.text{color:white;font-size:48px;line-height:1.5;white-space:pre-wrap}
.date{position:absolute;bottom:180px;width:100%;text-align:center;color:white;font-size:42px}
.footer{position:absolute;bottom:60px;width:100%;text-align:center;color:white;font-size:64px;font-weight:bold}
</style>
</head>
<body>
<div class="container">
<div class="design">Design store</div>
<div class="title">Отзывы</div>
<div class="subtitle">// Мнение клиентов</div>
<div class="makeby">MAKE BY</div>
<div class="badge">DESIGN STORE</div>
<div class="review">
<div class="header">
<div class="avatar"></div>
<div>
<div class="name">{name}</div>
<div class="username">{username}</div>
</div>
</div>
<div class="line"></div>
<div class="text">{review}</div>
</div>
<div class="date">Дата отзыва<br>{date}</div>
<div class="footer">T.ME/TGDESIGNSTORE</div>
</div>
</body>
</html>
"""

# --- Функция рендеринга (Playwright) ---
async def render_review_card(name: str, username: str, review: str, date: str) -> BytesIO:
    """Генерирует PNG-карточку отзыва в памяти и возвращает BytesIO."""
    html = HTML_TEMPLATE.format(name=name, username=username, review=review, date=date)
    async with async_playwright() as p:
        browser = await p.chromium.launch()
        page = await browser.new_page(viewport={"width": 1080, "height": 1080})
        await page.set_content(html)
        screenshot = await page.screenshot(full_page=True, type="png")
        await browser.close()
    return BytesIO(screenshot)

# --- Кэш прямых ссылок (для ibb.co) ---
url_cache = {}
def get_direct_image_url_sync(ibb_url):
    if "i.ibb.co" in ibb_url: return ibb_url
    if ibb_url in url_cache: return url_cache[ibb_url]
    if "ibb.co" not in ibb_url: return ibb_url
    try:
        req = urllib.request.Request(ibb_url, headers={"User-Agent":"Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=10) as resp: html = resp.read().decode()
        m = re.search(r'<meta[^>]+property=["\']og:image["\'][^>]+content=["\']([^"\']+)["\']', html)
        if not m: m = re.search(r'<link[^>]+rel=["\']image_src["\'][^>]+href=["\']([^"\']+)["\']', html)
        if not m: m = re.search(r'https?://i\.ibb\.co/[^\s"\'<>]+', html)
        direct = m.group(1) if m else ibb_url
        url_cache[ibb_url] = direct
        return direct
    except: return ibb_url
async def get_direct_image_url(url): return await asyncio.to_thread(get_direct_image_url_sync, url)

# --- Инициализация бота ---
bot = Bot(token=BOT_TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
dp = Dispatcher()

user_data = {}
bot_data = {"announcement": "", "users": set()}

# --- Проверка подписки ---
async def is_subscribed(user_id: int) -> bool:
    try:
        member = await bot.get_chat_member(chat_id=CHANNEL_ID, user_id=user_id)
        return member.status in ("member", "administrator", "creator")
    except: return False

async def require_subscription(event, callback: types.CallbackQuery = None):
    if callback:
        uid = callback.from_user.id
        if await is_subscribed(uid): return True
        await callback.answer("🔒 Подпишитесь на канал!", show_alert=True)
        return False
    else:
        uid = event.from_user.id
        if await is_subscribed(uid): return True
        kb = InlineKeyboardBuilder()
        kb.add(InlineKeyboardButton(text="✅ Проверить подписку", callback_data="check_sub"))
        await event.answer(f"🔒 Для использования бота подпишитесь на {CHANNEL_USERNAME} и нажмите кнопку.", reply_markup=kb.as_markup())
        return False

# --- Клавиатуры (без изменений) ---
def main_menu_kb(is_admin: bool = False):
    builder = InlineKeyboardBuilder()
    builder.row(InlineKeyboardButton(text="🛍️ Купить дизайн", callback_data="buy_design"))
    builder.row(
        InlineKeyboardButton(text="⭐ Отзывы магазина", url="https://t.me/otzdesingstore"),
        InlineKeyboardButton(text="🌐 Канал магазина", url="https://t.me/tgdesignstore")
    )
    builder.row(
        InlineKeyboardButton(text="📃 Регламент магазина", callback_data="rules"),
        InlineKeyboardButton(text="📞 Поддержка бота", callback_data="support")
    )
    builder.row(InlineKeyboardButton(text="✏️ Оставить отзыв", callback_data="leave_review"))
    if is_admin:
        builder.row(InlineKeyboardButton(text="🔧 Админ-панель", callback_data="admin_panel"))
    return builder.as_markup()

def buy_options_kb():
    builder = InlineKeyboardBuilder()
    builder.row(InlineKeyboardButton(text="🛍️ Купить у продавцов", callback_data="buy_from_sellers"))
    builder.row(InlineKeyboardButton(text="🏪 Купить от магазина", callback_data="buy_from_shop"))
    builder.row(InlineKeyboardButton(text="◀️ Назад", callback_data="back_to_main"))
    return builder.as_markup()

def shop_options_kb():
    builder = InlineKeyboardBuilder()
    builder.row(InlineKeyboardButton(text="💳 Купить напрямую", callback_data="buy_direct"))
    builder.row(InlineKeyboardButton(text="🛒 Купить через Playerok", url="https://playerok.com/profile/TG-Design-store/products"))
    builder.row(InlineKeyboardButton(text="◀️ Назад", callback_data="buy_design"))
    return builder.as_markup()

def sellers_kb():
    builder = InlineKeyboardBuilder()
    for key, seller in SELLERS.items():
        builder.row(InlineKeyboardButton(text=seller["name"], callback_data=f"seller_{key}"))
    builder.row(InlineKeyboardButton(text="◀️ Назад", callback_data="buy_design"))
    return builder.as_markup()

def seller_detail_kb(key):
    seller = SELLERS[key]
    builder = InlineKeyboardBuilder()
    for field, value in seller["fields"].items():
        if value.startswith(("http://", "https://", "@")):
            url = f"https://t.me/{value[1:]}" if value.startswith("@") else value
            builder.row(InlineKeyboardButton(text=field, url=url))
        else:
            builder.row(InlineKeyboardButton(text=field, callback_data=f"field_{key}_{field}"))
    builder.row(InlineKeyboardButton(text="◀️ Назад", callback_data="back_to_sellers"))
    return builder.as_markup()

def admin_panel_kb():
    builder = InlineKeyboardBuilder()
    builder.row(InlineKeyboardButton(text="📢 Объявления", callback_data="admin_announce"))
    builder.row(InlineKeyboardButton(text="🗑 Удалить объявление", callback_data="admin_clear_announce"))
    builder.row(InlineKeyboardButton(text="◀️ Назад", callback_data="back_to_main"))
    return builder.as_markup()

# --- Команда /start ---
@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    bot_data["users"].add(message.chat.id)
    if not await require_subscription(message): return
    await show_main_menu(message.chat.id, message.from_user.username)

async def show_main_menu(chat_id: int, username: str = None):
    is_adm = (username and username.lower() == ADMIN_USERNAME)
    ann = bot_data.get("announcement", "")
    if ann:
        await bot.send_message(chat_id, f"📢 {ann}", parse_mode=ParseMode.HTML)
    direct_url = await get_direct_image_url(MAIN_MENU_IMAGE)
    try:
        await bot.send_photo(chat_id, direct_url, caption="🏠 <b>Главное меню</b>",
                             reply_markup=main_menu_kb(is_adm))
    except:
        await bot.send_message(chat_id, "🏠 <b>Главное меню</b>", reply_markup=main_menu_kb(is_adm))

# --- Callback-обработчик ---
@dp.callback_query()
async def handle_callback(callback: types.CallbackQuery):
    data = callback.data
    uid = callback.from_user.id
    username = callback.from_user.username

    if data not in ("check_sub",) and not data.startswith("field_") and data != "leave_review":
        if not await require_subscription(None, callback): return

    # Админ-панель
    if data == "admin_panel":
        if not (username and username.lower() == ADMIN_USERNAME):
            await callback.answer("❌ Доступ запрещён", show_alert=True)
            return
        await callback.message.delete()
        await bot.send_message(uid, "🔧 <b>Админ-панель</b>", reply_markup=admin_panel_kb())
    elif data == "admin_announce":
        if not (username and username.lower() == ADMIN_USERNAME):
            await callback.answer("❌ Доступ запрещён", show_alert=True)
            return
        user_data[uid] = {"awaiting_announcement": True}
        await callback.message.delete()
        await bot.send_message(uid, "📢 Введите текст объявления (HTML-разметка работает). Для отмены /cancel")
    elif data == "admin_clear_announce":
        if not (username and username.lower() == ADMIN_USERNAME):
            await callback.answer("❌ Доступ запрещён", show_alert=True)
            return
        bot_data["announcement"] = ""
        await callback.answer("✅ Объявление удалено!")
        await callback.message.delete()
        await show_main_menu(uid, username)

    # Покупки
    elif data == "buy_design":
        await callback.message.delete()
        await bot.send_message(uid, "🛍️ <b>Выберите способ покупки:</b>", reply_markup=buy_options_kb())
    elif data == "buy_from_sellers":
        await callback.message.delete()
        await bot.send_message(uid, "🛍️ <b>Выберите продавца:</b>", reply_markup=sellers_kb())
    elif data == "buy_from_shop":
        await callback.message.delete()
        await bot.send_message(uid, "🏪 <b>Покупка от магазина</b>", reply_markup=shop_options_kb())
    elif data == "buy_direct":
        await callback.message.delete()
        direct_url = await get_direct_image_url(DIRECT_PURCHASE_IMAGE)
        kb = InlineKeyboardBuilder()
        kb.row(InlineKeyboardButton(text="📞 Менеджер @mngdesignstore", url="https://t.me/mngdesignstore"))
        kb.row(InlineKeyboardButton(text="◀️ Назад", callback_data="buy_from_shop"))
        try:
            await bot.send_photo(uid, direct_url, caption=DIRECT_PURCHASE_TEXT, reply_markup=kb.as_markup())
        except:
            await bot.send_message(uid, DIRECT_PURCHASE_TEXT, reply_markup=kb.as_markup())

    # Продавцы
    elif data.startswith("seller_"):
        key = data[7:]
        if key in SELLERS:
            seller = SELLERS[key]
            direct_url = await get_direct_image_url(seller["image_url"])
            caption = f"👤 <b>{seller['name']}</b>"
            if seller.get("description"): caption += f"\n{seller['description']}"
            await callback.message.delete()
            try:
                await bot.send_photo(uid, direct_url, caption=caption, reply_markup=seller_detail_kb(key))
            except:
                await bot.send_message(uid, caption, reply_markup=seller_detail_kb(key))
    elif data.startswith("field_"):
        _, key, field = data.split("_", 2)
        if key in SELLERS:
            text = SELLERS[key]["fields"].get(field, "Нет данных")
            await callback.answer(text, show_alert=True)

    # Навигация
    elif data == "back_to_main":
        await callback.message.delete()
        await show_main_menu(uid, username)
    elif data == "back_to_sellers":
        await callback.message.delete()
        await bot.send_message(uid, "🛍️ <b>Выберите продавца:</b>", reply_markup=sellers_kb())
    elif data == "check_sub":
        if await is_subscribed(uid):
            await callback.message.delete()
            await show_main_menu(uid, username)
        else:
            await callback.answer("❌ Вы всё ещё не подписаны на канал!", show_alert=True)
    elif data == "rules":
        await callback.message.delete()
        kb = InlineKeyboardBuilder()
        kb.row(InlineKeyboardButton(text="◀️ Назад", callback_data="back_to_main"))
        await bot.send_message(uid, RULES_TEXT, reply_markup=kb.as_markup())
    elif data == "support":
        await callback.message.delete()
        kb = InlineKeyboardBuilder()
        kb.row(InlineKeyboardButton(text="◀️ Назад", callback_data="back_to_main"))
        await bot.send_message(uid, SUPPORT_TEXT, reply_markup=kb.as_markup())

    # --- Оставить отзыв ---
    elif data == "leave_review":
        if not await is_subscribed(uid):
            await callback.answer("❌ Сначала подпишитесь на канал!", show_alert=True)
            return
        user_data[uid] = {"review_step": "awaiting_screenshot"}
        await callback.message.delete()
        await bot.send_message(uid, "📸 Пожалуйста, отправьте скриншот, подтверждающий покупку.")

# --- Обработчик фото (скриншот) ---
@dp.message(F.photo)
async def handle_photo(message: types.Message):
    uid = message.from_user.id
    if uid not in user_data or user_data[uid].get("review_step") != "awaiting_screenshot":
        return
    user_data[uid]["review_screenshot"] = message.photo[-1].file_id
    user_data[uid]["review_step"] = "awaiting_text"
    await message.answer("✏️ Теперь напишите текст отзыва.")

# --- Обработчик текста (объявления и текст отзыва) ---
@dp.message(F.text)
async def handle_text(message: types.Message):
    uid = message.from_user.id
    username = message.from_user.username or "user"

    # Объявление админа
    if username.lower() == ADMIN_USERNAME and user_data.get(uid, {}).get("awaiting_announcement"):
        user_data[uid]["awaiting_announcement"] = False
        text = message.text
        if not text: await message.answer("❌ Пустой текст."); return
        bot_data["announcement"] = text
        await message.answer("✅ Объявление сохранено! Рассылаем...")
        for chat_id in bot_data["users"].copy():
            try:
                await bot.send_message(chat_id, f"📢 {text}", parse_mode=ParseMode.HTML)
                await asyncio.sleep(0.05)
            except: pass
        await show_main_menu(uid, username)
        return

    # Текст отзыва
    if uid in user_data and user_data[uid].get("review_step") == "awaiting_text":
        review_text = message.text
        if not review_text: await message.answer("❌ Текст не может быть пустым."); return
        screenshot_id = user_data[uid].pop("review_screenshot", None)
        user_data[uid]["review_step"] = None

        # Генерация карточки (Playwright)
        review_date = datetime.now().strftime("%d.%m.%Y")
        display_username = f"@{message.from_user.username}" if message.from_user.username else "Пользователь"
        try:
            img_io = await render_review_card(
                name="Покупатель",
                username=display_username,
                review=review_text,
                date=review_date
            )
        except Exception as e:
            logger.error(f"Playwright render error: {e}")
            await message.answer("❌ Ошибка генерации карточки. Попробуйте позже.")
            return

        # Отправка в канал
        try:
            await bot.send_photo(REVIEWS_CHANNEL, BufferedInputFile(img_io.read(), filename="review.png"),
                                 caption=f"Отзыв от {display_username}")
            if screenshot_id:
                await bot.send_photo(REVIEWS_CHANNEL, screenshot_id, caption="📎 Скриншот покупки")
            await message.answer("✅ Ваш отзыв опубликован! Спасибо!")
        except Exception as e:
            logger.error(f"Posting review failed: {e}")
            await message.answer("❌ Не удалось опубликовать отзыв. Попробуйте позже.")

async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
