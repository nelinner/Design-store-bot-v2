import asyncio
import logging
from typing import Optional
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
    CallbackQueryHandler,
    MessageHandler,
    filters,
    ContextTypes,
)
from telegram.error import BadRequest, Forbidden
import aiohttp
from bs4 import BeautifulSoup

# Включаем логирование
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)

# ===== НАСТРОЙКИ =====
BOT_TOKEN = "8985680067:AAHROlAyLyMNf91fXw-IdtwQRJxcwda7OG8"
CHANNEL_USERNAME = "@tgdesignstore"
CHANNEL_ID = "@tgdesignstore"
ADMIN_USERNAME = "nelinner"  # без @

# Все ссылки на изображения – можно использовать обычные ссылки ibb.co (страницы), бот сам достанет прямые ссылки
MAIN_MENU_IMAGE = "https://ibb.co/RpCTX9X0"          # Главное меню
BUY_DESIGN_IMAGE = "https://ibb.co/C5MTqxQ9"         # Раздел «Купить дизайн»

# ===== ДАННЫЕ ПРОДАВЦОВ =====
SELLERS = {
    "linner": {
        "name": "Linner",
        "description": "💎 Профессиональный дизайнер каналов и логотипов",
        "image_url": "https://ibb.co/8LXw3Fw8",
        "fields": {
            "Username": "@nelinner",
            "Портфолио": "@worklinner",
            "Отзывы": "@otzlinner",
            "Прайс": "https://t.me/pricedesignstore/2",
        },
    },
    "loz": {
        "name": "Loz",
        "description": "🎨 Креативный дизайн и уникальный стиль",
        "image_url": "https://ibb.co/Xk5NGtd0",
        "fields": {
            "Username": "@loz306",
            "Портфолио": "@lozportfolio",
            "Отзывы": "Вручение от руководителя",
            "Прайс": "Узнавать в лс",
        },
    },
    "r1polz": {
        "name": "r1polZ",
        "description": "🚀 Оформление со стилем",
        "image_url": "https://ibb.co/8J6HGnk",
        "fields": {
            "Username": "@m9Zzzzuta",
            "Портфолио": "узнавать в лс",
            "Отзывы": "вручение от руководителя",
            "Прайс": "узнавать в лс",
        },
    },
    "rassvet": {
        "name": "Рассвет",
        "description": "🌅 Стильные решения для твоего проекта",
        "image_url": "https://ibb.co/Tqc8D19p",
        "fields": {
            "Username": "@PACBETTT",
            "Портфолио": "https://t.me/rasvetDesignn",
            "Отзывы": "вручение от руководителя",
            "Прайс": "https://t.me/pricedesignstore/3",
        },
    },
    "omut": {
        "name": "Омут сомнений // asc ",
        "description": "🌀 Минимализм и атмосферный дизайн, и оформление каналов",
        "image_url": "https://ibb.co/4nVRrgp9",
        "fields": {
            "Username": "@xaywd",
            "Портфолио": "https://t.me/movaningfx",
            "Отзывы": "вручение от руководителя",
            "Прайс": "https://t.me/pricedesignstore/4",
        },
    },
}

# ===== ТЕКСТЫ =====
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

# ===== КЭШ И ЗАГОЛОВКИ ДЛЯ ПАРСИНГА =====
url_cache = {}

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.5",
    "Referer": "https://ibb.co/",
}

async def get_direct_image_url(ibb_url: str) -> Optional[str]:
    if "i.ibb.co" in ibb_url:
        return ibb_url
    if ibb_url in url_cache:
        return url_cache[ibb_url]
    if "ibb.co" not in ibb_url:
        return ibb_url

    try:
        async with aiohttp.ClientSession(headers=HEADERS) as session:
            async with session.get(ibb_url, timeout=15) as response:
                if response.status != 200:
                    logger.warning(f"Не удалось загрузить страницу {ibb_url} (статус {response.status})")
                    return None
                html = await response.text()

        soup = BeautifulSoup(html, 'html.parser')
        direct_url = None

        meta_og = soup.find('meta', property='og:image')
        if meta_og and meta_og.get('content'):
            direct_url = meta_og['content']

        if not direct_url:
            meta_secure = soup.find('meta', property='og:image:secure_url')
            if meta_secure and meta_secure.get('content'):
                direct_url = meta_secure['content']

        if not direct_url:
            link_rel = soup.find('link', rel='image_src')
            if link_rel and link_rel.get('href'):
                direct_url = link_rel['href']

        if not direct_url:
            for link in soup.find_all('a', href=True):
                if 'i.ibb.co' in link['href']:
                    direct_url = link['href']
                    break

        if direct_url:
            url_cache[ibb_url] = direct_url
            return direct_url

        logger.warning(f"Не найдена прямая ссылка на странице {ibb_url}")
        return ibb_url

    except Exception as e:
        logger.error(f"Ошибка при парсинге {ibb_url}: {e}")
        return ibb_url

# ===== КЛАВИАТУРЫ =====
def build_main_menu_keyboard(is_admin: bool = False):
    keyboard = [
        [InlineKeyboardButton("🛍️ Купить дизайн", callback_data="buy_design")],
        [
            InlineKeyboardButton("⭐ Отзывы магазина", url="https://t.me/otzdesingstore"),
            InlineKeyboardButton("🌐 Канал магазина", url="https://t.me/tgdesignstore"),
        ],
        [
            InlineKeyboardButton("📃 Регламент магазина", callback_data="rules"),
            InlineKeyboardButton("📞 Поддержка бота", callback_data="support"),
        ],
    ]
    if is_admin:
        keyboard.append([InlineKeyboardButton("🔧 Админ-панель", callback_data="admin_panel")])
    return InlineKeyboardMarkup(keyboard)

def build_sellers_keyboard():
    buttons = []
    for key, seller in SELLERS.items():
        buttons.append([InlineKeyboardButton(seller["name"], callback_data=f"seller_{key}")])
    buttons.append([InlineKeyboardButton("◀️ Назад", callback_data="back_to_main")])
    return InlineKeyboardMarkup(buttons)

def build_seller_detail_keyboard(seller_key: str):
    seller = SELLERS[seller_key]
    keyboard = []
    for field_name, value in seller["fields"].items():
        if value.startswith("http://") or value.startswith("https://") or value.startswith("@"):
            url = f"https://t.me/{value[1:]}" if value.startswith("@") else value
            keyboard.append([InlineKeyboardButton(field_name, url=url)])
        else:
            callback_data = f"field_{seller_key}_{field_name}"
            keyboard.append([InlineKeyboardButton(field_name, callback_data=callback_data)])
    keyboard.append([InlineKeyboardButton("◀️ Назад", callback_data="back_to_sellers")])
    return InlineKeyboardMarkup(keyboard)

def build_admin_panel_keyboard():
    keyboard = [
        [InlineKeyboardButton("📢 Объявления", callback_data="admin_announce")],
        [InlineKeyboardButton("🗑 Удалить объявление", callback_data="admin_clear_announce")],
        [InlineKeyboardButton("◀️ Назад", callback_data="back_to_main")],
    ]
    return InlineKeyboardMarkup(keyboard)

# ===== ПРОВЕРКА ПОДПИСКИ =====
async def is_subscribed(user_id: int, context: ContextTypes.DEFAULT_TYPE) -> bool:
    try:
        member = await context.bot.get_chat_member(chat_id=CHANNEL_ID, user_id=user_id)
        return member.status in ("member", "administrator", "creator")
    except BadRequest as e:
        logger.warning(f"Ошибка проверки подписки: {e}")
        return False

async def require_subscription(update: Update, context: ContextTypes.DEFAULT_TYPE) -> bool:
    query = update.callback_query
    user_id = query.from_user.id if query else update.message.from_user.id
    if await is_subscribed(user_id, context):
        return True

    keyboard = InlineKeyboardMarkup(
        [[InlineKeyboardButton("✅ Проверить подписку", callback_data="check_sub")]]
    )
    text = (
        "🔒 Для использования бота необходимо быть подписанным на канал "
        f"{CHANNEL_USERNAME}.\nПодпишись и нажми кнопку ниже."
    )
    if query:
        try:
            await query.message.delete()
        except BadRequest:
            pass
        await context.bot.send_message(
            chat_id=query.message.chat_id, text=text, reply_markup=keyboard
        )
    else:
        await update.message.reply_text(text, reply_markup=keyboard)
    return False

# ===== ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ =====
def is_admin(update: Update) -> bool:
    username = update.effective_user.username
    return username and username.lower() == ADMIN_USERNAME

def register_user(context: ContextTypes.DEFAULT_TYPE, chat_id: int):
    """Добавляет пользователя в список для рассылок."""
    if 'users' not in context.bot_data:
        context.bot_data['users'] = set()
    context.bot_data['users'].add(chat_id)

async def broadcast_announcement(context: ContextTypes.DEFAULT_TYPE, text: str):
    """Рассылает объявление всем пользователям из сохранённого списка."""
    users = context.bot_data.get('users', set())
    if not users:
        return

    logger.info(f"Рассылка объявления {len(users)} пользователям")
    message = f"📢 {text}"

    for chat_id in list(users):
        try:
            await context.bot.send_message(chat_id=chat_id, text=message, parse_mode="HTML")
            # Небольшая задержка, чтобы не упереться в лимиты (30 сообщений в секунду)
            await asyncio.sleep(0.05)
        except Forbidden:
            # Пользователь заблокировал бота — удаляем его из списка
            logger.warning(f"Пользователь {chat_id} заблокировал бота, удаляю из рассылки")
            users.discard(chat_id)
        except BadRequest as e:
            logger.error(f"Ошибка отправки объявления пользователю {chat_id}: {e}")
        except Exception as e:
            logger.error(f"Неизвестная ошибка при отправке {chat_id}: {e}")

# ===== ОБРАБОТЧИКИ КОМАНД =====
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    # Сохраняем пользователя
    register_user(context, update.message.chat_id)

    if not await is_subscribed(update.message.from_user.id, context):
        keyboard = InlineKeyboardMarkup(
            [[InlineKeyboardButton("✅ Проверить подписку", callback_data="check_sub")]]
        )
        await update.message.reply_text(
            f"🔒 Для использования бота подпишитесь на канал {CHANNEL_USERNAME} и нажмите кнопку.",
            reply_markup=keyboard,
        )
        return

    await show_main_menu(update, context, chat_id=update.message.chat_id)

async def show_main_menu(
    update: Update, context: ContextTypes.DEFAULT_TYPE, chat_id: int
) -> None:
    """
    Отправляет главное меню: сначала отдельное сообщение с объявлением (если задано),
    затем фото с кнопками.
    """
    is_admin_user = is_admin(update)
    announcement = context.bot_data.get("announcement", "")

    # Отправляем объявление отдельным сообщением, если оно есть
    if announcement:
        try:
            await context.bot.send_message(
                chat_id=chat_id,
                text=f"📢 {announcement}",
                parse_mode="HTML",
            )
        except BadRequest as e:
            logger.error(f"Ошибка отправки объявления: {e}")

    # Отправляем фото с кнопками
    caption = "🏠 <b>Главное меню</b>"
    direct_url = await get_direct_image_url(MAIN_MENU_IMAGE)
    if direct_url:
        try:
            await context.bot.send_photo(
                chat_id=chat_id,
                photo=direct_url,
                caption=caption,
                parse_mode="HTML",
                reply_markup=build_main_menu_keyboard(is_admin=is_admin_user),
            )
            return
        except BadRequest as e:
            logger.error(f"Ошибка при отправке главного меню: {e}")

    # Запасной текстовый вариант
    await context.bot.send_message(
        chat_id=chat_id,
        text=caption,
        parse_mode="HTML",
        reply_markup=build_main_menu_keyboard(is_admin=is_admin_user),
    )

async def handle_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()

    # Сохраняем пользователя
    register_user(context, query.message.chat_id)

    data = query.data
    user_id = query.from_user.id

    if data != "check_sub" and not data.startswith("field_"):
        if not await require_subscription(update, context):
            return

    if not data.startswith("field_"):
        try:
            await query.message.delete()
        except BadRequest:
            pass

    # --- Админ-панель ---
    if data == "admin_panel":
        if not is_admin(update):
            await query.answer("❌ Доступ запрещён", show_alert=True)
            return
        await context.bot.send_message(
            chat_id=query.message.chat_id,
            text="🔧 <b>Админ-панель</b>",
            parse_mode="HTML",
            reply_markup=build_admin_panel_keyboard(),
        )
        return

    elif data == "admin_announce":
        if not is_admin(update):
            await query.answer("❌ Доступ запрещён", show_alert=True)
            return
        context.user_data["awaiting_announcement"] = True
        await context.bot.send_message(
            chat_id=query.message.chat_id,
            text="📢 Введите текст объявления (HTML-разметка работает).\nДля отмены отправьте /cancel",
        )
        return

    elif data == "admin_clear_announce":
        if not is_admin(update):
            await query.answer("❌ Доступ запрещён", show_alert=True)
            return
        context.bot_data["announcement"] = ""
        await query.answer("✅ Объявление удалено!", show_alert=True)
        # Возвращаемся в главное меню (без объявления)
        await show_main_menu(update, context, chat_id=query.message.chat_id)
        return

    # --- Остальная логика ---
    if data == "check_sub":
        if await is_subscribed(user_id, context):
            try:
                await query.message.delete()
            except BadRequest:
                pass
            await show_main_menu(update, context, chat_id=query.message.chat_id)
        else:
            await query.answer("❌ Вы всё ещё не подписаны на канал!", show_alert=True)

    elif data == "buy_design":
        direct_url = await get_direct_image_url(BUY_DESIGN_IMAGE)
        if direct_url:
            try:
                await context.bot.send_photo(
                    chat_id=query.message.chat_id,
                    photo=direct_url,
                    caption="🛍️ <b>Выберите продавца дизайна:</b>",
                    parse_mode="HTML",
                    reply_markup=build_sellers_keyboard(),
                )
                return
            except BadRequest:
                pass
        await context.bot.send_message(
            chat_id=query.message.chat_id,
            text="🛍️ <b>Выберите продавца дизайна:</b>",
            parse_mode="HTML",
            reply_markup=build_sellers_keyboard(),
        )

    elif data.startswith("seller_"):
        seller_key = data[len("seller_"):]
        if seller_key in SELLERS:
            seller = SELLERS[seller_key]
            direct_url = await get_direct_image_url(seller["image_url"])

            caption = f"👤 <b>{seller['name']}</b>"
            if seller.get("description"):
                caption += f"\n{seller['description']}"

            if direct_url:
                try:
                    await context.bot.send_photo(
                        chat_id=query.message.chat_id,
                        photo=direct_url,
                        caption=caption,
                        parse_mode="HTML",
                        reply_markup=build_seller_detail_keyboard(seller_key),
                    )
                    return
                except BadRequest:
                    pass
            await context.bot.send_message(
                chat_id=query.message.chat_id,
                text=caption,
                parse_mode="HTML",
                reply_markup=build_seller_detail_keyboard(seller_key),
            )

    elif data.startswith("field_"):
        _, seller_key, field_name = data.split("_", 2)
        seller = SELLERS.get(seller_key)
        if seller:
            text = seller["fields"].get(field_name, "Информация отсутствует")
            await query.answer(text, show_alert=True)

    elif data == "back_to_main":
        await show_main_menu(update, context, chat_id=query.message.chat_id)

    elif data == "back_to_sellers":
        direct_url = await get_direct_image_url(BUY_DESIGN_IMAGE)
        if direct_url:
            try:
                await context.bot.send_photo(
                    chat_id=query.message.chat_id,
                    photo=direct_url,
                    caption="🛍️ <b>Выберите продавца дизайна:</b>",
                    parse_mode="HTML",
                    reply_markup=build_sellers_keyboard(),
                )
                return
            except BadRequest:
                pass
        await context.bot.send_message(
            chat_id=query.message.chat_id,
            text="🛍️ <b>Выберите продавца дизайна:</b>",
            parse_mode="HTML",
            reply_markup=build_sellers_keyboard(),
        )

    elif data == "rules":
        keyboard = InlineKeyboardMarkup(
            [[InlineKeyboardButton("◀️ Назад", callback_data="back_to_main")]]
        )
        await context.bot.send_message(
            chat_id=query.message.chat_id,
            text=RULES_TEXT,
            parse_mode="HTML",
            reply_markup=keyboard,
        )

    elif data == "support":
        keyboard = InlineKeyboardMarkup(
            [[InlineKeyboardButton("◀️ Назад", callback_data="back_to_main")]]
        )
        await context.bot.send_message(
            chat_id=query.message.chat_id,
            text=SUPPORT_TEXT,
            parse_mode="HTML",
            reply_markup=keyboard,
        )

    else:
        await query.answer("Неизвестная команда", show_alert=True)

# --- Обработчик текстовых сообщений (для объявлений) ---
async def handle_announcement_text(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Сохраняет текст объявления и моментально рассылает его всем пользователям."""
    if not is_admin(update) or not context.user_data.get("awaiting_announcement"):
        return

    context.user_data["awaiting_announcement"] = False
    text = update.message.text

    if not text:
        await update.message.reply_text("❌ Объявление не может быть пустым.")
        return

    # Сохраняем объявление
    context.bot_data["announcement"] = text
    await update.message.reply_text("✅ Объявление сохранено! Начинаю рассылку...")

    # Мгновенная рассылка всем пользователям (в фоне)
    asyncio.create_task(broadcast_announcement(context, text))

    # Показываем обновлённое главное меню админу (объявление будет отдельным постом)
    await show_main_menu(update, context, chat_id=update.message.chat_id)

async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE) -> None:
    logger.error(msg="Exception while handling an update:", exc_info=context.error)

def main() -> None:
    application = Application.builder().token(BOT_TOKEN).build()

    application.add_handler(CommandHandler("start", start))
    application.add_handler(CallbackQueryHandler(handle_callback))

    application.add_handler(
        MessageHandler(
            filters.TEXT & ~filters.COMMAND & filters.User(username=ADMIN_USERNAME),
            handle_announcement_text,
        )
    )

    application.add_error_handler(error_handler)
    logger.info("Бот запущен...")
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == "__main__":
    main()
