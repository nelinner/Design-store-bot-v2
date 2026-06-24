import asyncio, logging, re, urllib.request
from datetime import datetime
from io import BytesIO
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup, FSInputFile
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

# HTML-шаблон (твой макет) с подключением Google Fonts
HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="ru">
<head>
<meta charset="UTF-8">
<title>Review Card</title>
<link href="https://fonts.googleapis.com/css2?family=Montserrat:wght@400;500;700;800&display=swap" rel="stylesheet">
<style>
  *{margin:0;padding:0;box-sizing:border-box}
  body{width:1024px;height:1024px;overflow:hidden;font-family:'Montserrat',sans-serif;
       background:radial-gradient(circle at 20% 20%, rgba(0,255,180,.15), transparent 35%),
                 radial-gradient(circle at 80% 60%, rgba(0,255,180,.12), transparent 30%),
                 linear-gradient(135deg,#031313,#071717,#0a1010);color:white}
  .wrapper{position:relative;width:100%;height:100%}
  .light-1{position:absolute;width:500px;height:1200px;background:rgba(0,255,180,.05);transform:rotate(30deg);left:250px;top:-100px;filter:blur(40px)}
  .light-2{position:absolute;width:400px;height:1000px;background:rgba(0,255,180,.04);transform:rotate(-20deg);right:100px;top:-100px;filter:blur(40px)}
  .logo{position:absolute;top:30px;left:50%;transform:translateX(-50%);font-size:72px;font-family:cursive;color:#7cffc9;text-shadow:0 0 10px rgba(124,255,201,.5),0 0 25px rgba(124,255,201,.4)}
  .title{position:absolute;left:55px;top:150px}
  .title h1{font-size:82px;font-weight:800;line-height:1}
  .title p{margin-top:-5px;font-size:30px;font-weight:500}
  .makeby{position:absolute;right:45px;top:120px;text-align:center}
  .makeby .top{color:#7cffc9;font-size:54px;font-weight:800}
  .makeby .btn{margin-top:15px;width:300px;height:90px;border-radius:45px;display:flex;justify-content:center;align-items:center;font-size:42px;font-weight:800;color:white;background:linear-gradient(180deg,#b5d7be,#728e7a);box-shadow:0 0 20px rgba(255,255,255,.15),inset 0 3px 10px rgba(255,255,255,.25)}
  .review-box{position:absolute;left:60px;top:340px;width:860px;height:430px;border-radius:50px;background:linear-gradient(180deg,rgba(180,180,180,.95),rgba(90,90,90,.92));border:5px solid rgba(255,255,255,.8);box-shadow:0 0 35px rgba(255,255,255,.15),inset 0 1px 20px rgba(255,255,255,.15)}
  .profile{display:flex;align-items:center;gap:20px;padding:35px}
  .avatar{width:90px;height:90px;border-radius:50%;background:radial-gradient(circle at 50% 35%, #88ffbc 0 20px, transparent 21px),radial-gradient(circle at 50% 78%, #88ffbc 0 32px, transparent 33px),#051111;border:2px solid rgba(255,255,255,.15);box-shadow:0 0 15px rgba(124,255,201,.4)}
  .user-info{display:flex;flex-direction:column}
  .role{font-size:54px;font-weight:700}
  .username{display:inline-flex;align-items:center;height:45px;padding:0 20px;border-radius:25px;background:rgba(255,255,255,.35);color:white;font-size:30px;font-weight:700}
  .separator{width:760px;height:4px;background:rgba(255,255,255,.2);margin:0 auto}
  .review-text{padding:35px 45px;font-size:42px;font-weight:700;line-height:1.5;max-width:760px;word-break:break-word}
  .date{position:absolute;width:100%;text-align:center;top:790px;font-style:italic}
  .date .label{font-size:34px}
  .date .value{font-size:56px}
  .footer{position:absolute;width:100%;bottom:40px;text-align:center;font-size:56px;font-weight:800}
  .ceo{position:absolute;left:30px;bottom:30px;font-size:22px;font-weight:700}
</style>
</head>
<body>
<div class="wrapper">
<div class="light-1"></div><div class="light-2"></div>
<div class="logo">Design store</div>
<div class="title"><h1>Отзывы</h1><p>// Мнение клиентов</p></div>
<div class="makeby"><div class="top">MAKE BY</div><div class="btn">DESIGN STORE</div></div>
<div class="review-box">
<div class="profile">
<div class="avatar"></div>
<div class="user-info">
<div class="role">Покупатель</div>
<div class="username">{{username}}</div>
</div>
</div>
<div class="separator"></div>
<div class="review-text">{{review_text}}</div>
</div>
<div class="date"><div class="label">дата с отзывом</div><div class="value">{{review_date}}</div></div>
<div class="footer">T.ME/TGDESIGNSTORE</div>
<div class="ceo">CEO: @NELINNER</div>
</div>
</body>
</html>
"""

# Кэш прямых ссылок
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

# Инициализация бота и диспетчера
bot = Bot(token=BOT_TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
dp = Dispatcher()

# Глобальное хранилище состояний (для простоты – в памяти)
user_data = {}
bot_data = {"announcement": "", "users": set()}

# Проверка подписки
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

# Клавиатуры
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

# Команда /start
@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    bot_data["users"].add(message.chat.id)
    if not await require_submission(message): return
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

# Обработчик всех callback
@dp.callback_query()
async def handle_callback(callback: types.CallbackQuery):
    data = callback.data
    uid = callback.from_user.id
    username = callback.from_user.username

    # Проверка подписки для всех действий, кроме некоторых
    if data not in ("check_sub",) and not data.startswith("field_") and data != "leave_review":
        if not await require_submission(None, callback): return

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

    # Оставить отзыв
    elif data == "leave_review":
        if not await is_subscribed(uid):
            await callback.answer("❌ Сначала подпишитесь на канал!", show_alert=True)
            return
        user_data[uid] = {"review_step": "awaiting_screenshot"}
        await callback.message.delete()
        await bot.send_message(uid, "📸 Пожалуйста, отправьте скриншот, подтверждающий покупку.")

# Обработчик фото (для скриншота отзыва)
@dp.message(F.photo)
async def handle_photo(message: types.Message):
    uid = message.from_user.id
    if uid not in user_data or user_data[uid].get("review_step") != "awaiting_screenshot":
        return
    # Сохраняем file_id самого большого фото
    user_data[uid]["review_screenshot"] = message.photo[-1].file_id
    user_data[uid]["review_step"] = "awaiting_text"
    await message.answer("✏️ Теперь напишите текст отзыва.")

# Обработчик текста (объявления и текст отзыва)
@dp.message(F.text)
async def handle_text(message: types.Message):
    uid = message.from_user.id
    username = message.from_user.username or "user"

    # Объявление админа
    if username.lower() == ADMIN_USERNAME and user_data.get(uid, {}).get("awaiting_announcement"):
        user_data[uid]["awaiting_announcement"] = False
        text = message.text
        if not text:
            await message.answer("❌ Пустой текст.")
            return
        bot_data["announcement"] = text
        await message.answer("✅ Объявление сохранено! Рассылаем...")
        # Рассылка всем пользователям
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
        if not review_text:
            await message.answer("❌ Текст не может быть пустым.")
            return
        screenshot_id = user_data[uid].pop("review_screenshot", None)
        user_data[uid]["review_step"] = None

        # Генерация HTML-карточки через Playwright
        review_date = datetime.now().strftime("%d.%m.%Y")
        display_username = f"@{message.from_user.username}" if message.from_user.username else "Пользователь"
        html_content = HTML_TEMPLATE.replace("{{username}}", display_username)\
                                     .replace("{{review_text}}", review_text)\
                                     .replace("{{review_date}}", review_date)

        try:
            async with async_playwright() as p:
                browser = await p.chromium.launch()
                page = await browser.new_page(viewport={"width": 1024, "height": 1024})
                await page.set_content(html_content, wait_until="networkidle")
                screenshot = await page.screenshot(full_page=False, type="png")
                await browser.close()
        except Exception as e:
            logger.error(f"Playwright render error: {e}")
            await message.answer("❌ Ошибка генерации карточки. Попробуйте позже.")
            return

        # Отправка в канал с отзывами
        try:
            # Карточка
            photo_io = BytesIO(screenshot)
            photo_io.name = "review_card.png"
            await bot.send_photo(REVIEWS_CHANNEL, FSInputFile(photo_io),
                                 caption=f"Отзыв от {display_username}")
            # Скриншот (если есть)
            if screenshot_id:
                await bot.send_photo(REVIEWS_CHANNEL, screenshot_id, caption="📎 Скриншот покупки")
            await message.answer("✅ Ваш отзыв опубликован! Спасибо!")
        except Exception as e:
            logger.error(f"Posting review failed: {e}")
            await message.answer("❌ Не удалось опубликовать отзыв. Попробуйте позже.")
        return

async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
