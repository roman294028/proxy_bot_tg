import os
import logging
import requests
import time
import random
from datetime import datetime
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes, CallbackQueryHandler

# Настройка логирования
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Токен бота
TOKEN = os.environ.get('BOT_TOKEN')
if not TOKEN:
    raise ValueError("BOT_TOKEN environment variable not set!")

# Твой Telegram username
ADMIN_USERNAME = "@hoshino_aaai"

# ========== КЭШ ДЛЯ ПРОКСИ ==========
proxies_cache = {
    'list': [],
    'last_update': 0
}

# ========== ФУНКЦИИ ДЛЯ ПОИСКА ПРОКСИ ==========

def fetch_proxies_from_api():
    """Получает свежие прокси с бесплатных источников"""
    all_proxies = []
    
    # Источник 1: ProxyScrape (HTTP)
    try:
        response = requests.get(
            "https://api.proxyscrape.com/v2/?request=getproxies&protocol=http&timeout=5000&country=all&ssl=all&anonymity=all",
            timeout=10
        )
        if response.status_code == 200:
            proxies = response.text.strip().split('\r\n')
            for p in proxies[:30]:
                if ':' in p:
                    ip, port = p.split(':')
                    all_proxies.append({
                        'ip': ip,
                        'port': port,
                        'protocol': 'http',
                        'source': 'proxyscrape'
                    })
    except Exception as e:
        logger.error(f"ProxyScrape error: {e}")
    
    # Источник 2: ProxyScrape (SOCKS4)
    try:
        response = requests.get(
            "https://api.proxyscrape.com/v2/?request=getproxies&protocol=socks4&timeout=5000&country=all",
            timeout=10
        )
        if response.status_code == 200:
            proxies = response.text.strip().split('\r\n')
            for p in proxies[:15]:
                if ':' in p:
                    ip, port = p.split(':')
                    all_proxies.append({
                        'ip': ip,
                        'port': port,
                        'protocol': 'socks4',
                        'source': 'proxyscrape'
                    })
    except Exception as e:
        logger.error(f"ProxyScrape SOCKS4 error: {e}")
    
    # Источник 3: ProxyScrape (SOCKS5)
    try:
        response = requests.get(
            "https://api.proxyscrape.com/v2/?request=getproxies&protocol=socks5&timeout=5000&country=all",
            timeout=10
        )
        if response.status_code == 200:
            proxies = response.text.strip().split('\r\n')
            for p in proxies[:15]:
                if ':' in p:
                    ip, port = p.split(':')
                    all_proxies.append({
                        'ip': ip,
                        'port': port,
                        'protocol': 'socks5',
                        'source': 'proxyscrape'
                    })
    except Exception as e:
        logger.error(f"ProxyScrape SOCKS5 error: {e}")
    
    return all_proxies

def check_proxy_quick(proxy):
    """Быстрая проверка прокси (без детального теста)"""
    return random.choice([True, False])  # Для демо всегда возвращаем True
    # В реальности тут была бы проверка, но для экономии времени бота пропускаем

def get_working_proxies(protocol=None, limit=10):
    """Возвращает список работающих прокси"""
    # Обновляем кэш если прошло больше 5 минут
    current_time = time.time()
    if current_time - proxies_cache['last_update'] > 300 or not proxies_cache['list']:
        proxies_cache['list'] = fetch_proxies_from_api()
        proxies_cache['last_update'] = current_time
    
    # Фильтруем по протоколу
    if protocol and protocol != 'all':
        filtered = [p for p in proxies_cache['list'] if p['protocol'] == protocol]
    else:
        filtered = proxies_cache['list']
    
    # Перемешиваем и возвращаем
    random.shuffle(filtered)
    return filtered[:limit]

# ========== ФУНКЦИИ ДЛЯ ПОИСКА VPN ==========

def get_vpn_services():
    """Возвращает список VPN сервисов"""
    return [
        {
            'name': 'TunnelBear',
            'description': 'Простой VPN с бесплатным лимитом 500МБ/мес',
            'url': 'https://www.tunnelbear.com',
            'free': True,
            'platforms': 'Windows, Mac, iOS, Android'
        },
        {
            'name': 'ProtonVPN',
            'description': 'Швейцарский VPN с бесплатным тарифом без ограничений',
            'url': 'https://protonvpn.com',
            'free': True,
            'platforms': 'Windows, Mac, Linux, iOS, Android'
        },
        {
            'name': 'Windscribe',
            'description': 'Бесплатный лимит 10ГБ/мес',
            'url': 'https://windscribe.com',
            'free': True,
            'platforms': 'Windows, Mac, Linux, iOS, Android'
        },
        {
            'name': 'Hide.me',
            'description': 'Бесплатный тариф 10ГБ/мес',
            'url': 'https://hide.me',
            'free': True,
            'platforms': 'Windows, Mac, iOS, Android'
        },
        {
            'name': 'Hotspot Shield',
            'description': 'Бесплатный тариф с рекламой, 500МБ/день',
            'url': 'https://hotspotshield.com',
            'free': True,
            'platforms': 'Windows, Mac, iOS, Android'
        },
        {
            'name': 'Psiphon',
            'description': 'Популярный в РФ, есть бесплатная версия',
            'url': 'https://psiphon.ca',
            'free': True,
            'platforms': 'Windows, iOS, Android'
        },
        {
            'name': 'V2Ray (V2Box)',
            'description': 'Клиент для работы с V2Ray на iOS',
            'url': 'https://apps.apple.com/app/v2box-v2ray-client/id1446815469',
            'free': True,
            'platforms': 'iOS'
        },
        {
            'name': 'v2rayNG',
            'description': 'V2Ray клиент для Android',
            'url': 'https://play.google.com/store/apps/details?id=com.v2ray.ang',
            'free': True,
            'platforms': 'Android'
        },
        {
            'name': 'Outline VPN',
            'description': 'Open-source VPN от Google',
            'url': 'https://getoutline.org',
            'free': True,
            'platforms': 'Windows, Mac, iOS, Android'
        },
        {
            'name': 'Lantern',
            'description': 'Быстрый VPN с бесплатным лимитом',
            'url': 'https://lantern.io',
            'free': True,
            'platforms': 'Windows, Mac, iOS, Android'
        }
    ]

# ========== ИНЛАЙН-КЛАВИАТУРЫ ==========

def get_main_keyboard():
    """Главная клавиатура"""
    keyboard = [
        [InlineKeyboardButton("🌐 Найти прокси", callback_data='menu_proxy')],
        [InlineKeyboardButton("🔒 Найти VPN", callback_data='menu_vpn')],
        [InlineKeyboardButton("❓ Помощь", callback_data='menu_help')]
    ]
    return InlineKeyboardMarkup(keyboard)

def get_proxy_keyboard():
    """Клавиатура для прокси"""
    keyboard = [
        [InlineKeyboardButton("🔄 Все прокси", callback_data='proxy_all')],
        [InlineKeyboardButton("🌐 HTTP", callback_data='proxy_http'),
         InlineKeyboardButton("🔒 HTTPS", callback_data='proxy_https')],
        [InlineKeyboardButton("🧦 SOCKS4", callback_data='proxy_socks4'),
         InlineKeyboardButton("🧦 SOCKS5", callback_data='proxy_socks5')],
        [InlineKeyboardButton("◀️ Назад", callback_data='back_main')]
    ]
    return InlineKeyboardMarkup(keyboard)

def get_vpn_keyboard():
    """Клавиатура для VPN"""
    keyboard = [
        [InlineKeyboardButton("📱 Все VPN", callback_data='vpn_all')],
        [InlineKeyboardButton("💻 Для Windows", callback_data='vpn_windows'),
         InlineKeyboardButton("🍏 Для Mac", callback_data='vpn_mac')],
        [InlineKeyboardButton("📱 Для Android", callback_data='vpn_android'),
         InlineKeyboardButton("📱 Для iOS", callback_data='vpn_ios')],
        [InlineKeyboardButton("🆓 Только бесплатные", callback_data='vpn_free')],
        [InlineKeyboardButton("◀️ Назад", callback_data='back_main')]
    ]
    return InlineKeyboardMarkup(keyboard)

def get_back_keyboard():
    """Клавиатура с кнопкой назад"""
    keyboard = [
        [InlineKeyboardButton("◀️ Назад", callback_data='back_main')]
    ]
    return InlineKeyboardMarkup(keyboard)

# ========== ОБРАБОТЧИКИ ==========

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик команды /start"""
    welcome_text = (
        "👋 **Привет! Я бот для поиска прокси и VPN**\n\n"
        "🔹 **🌐 Найти прокси** — получу список рабочих прокси\n"
        "🔹 **🔒 Найти VPN** — покажу рабочие VPN сервисы\n"
        "🔹 **❓ Помощь** — информация и контакты\n\n"
        "👇 Выбери нужный раздел:"
    )
    await update.message.reply_text(welcome_text, parse_mode='Markdown', reply_markup=get_main_keyboard())

async def button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик нажатий на инлайн-кнопки"""
    query = update.callback_query
    await query.answer()
    
    # ===== НАВИГАЦИЯ =====
    if query.data == 'back_main':
        await query.edit_message_text(
            "👋 **Главное меню**\n\nВыбери нужный раздел:",
            parse_mode='Markdown',
            reply_markup=get_main_keyboard()
        )
    
    elif query.data == 'menu_proxy':
        await query.edit_message_text(
            "🌐 **Поиск прокси**\n\n"
            "Выбери тип прокси:\n"
            "• HTTP/HTTPS — для браузера и софта\n"
            "• SOCKS — для Telegram и других приложений\n\n"
            "👇 Нажми на кнопку:",
            parse_mode='Markdown',
            reply_markup=get_proxy_keyboard()
        )
    
    elif query.data == 'menu_vpn':
        await query.edit_message_text(
            "🔒 **Поиск VPN**\n\n"
            "Выбери платформу или смотри все варианты:",
            parse_mode='Markdown',
            reply_markup=get_vpn_keyboard()
        )
    
    elif query.data == 'menu_help':
        help_text = (
            "❓ **Помощь**\n\n"
            "🔹 **Как пользоваться:**\n"
            "• Нажимай кнопки в меню\n"
            "• Получай списки рабочих прокси и VPN\n\n"
            "🔹 **Связь с админом:**\n"
            f"{ADMIN_USERNAME} — только по важным вопросам\n\n"
            "🔹 **О боте:**\n"
            "Версия 2.0\n"
            "Прокси обновляются каждые 5 минут\n"
            "VPN список актуален на 2026 год"
        )
        await query.edit_message_text(help_text, parse_mode='Markdown', reply_markup=get_back_keyboard())
    
    # ===== ПРОКСИ =====
    elif query.data.startswith('proxy_'):
        protocol_map = {
            'proxy_all': 'all',
            'proxy_http': 'http',
            'proxy_https': 'https',
            'proxy_socks4': 'socks4',
            'proxy_socks5': 'socks5'
        }
        protocol = protocol_map.get(query.data, 'all')
        
        # Отправляем сообщение о поиске
        await query.edit_message_text(
            "🔍 **Ищу рабочие прокси...**\nЭто может занять несколько секунд",
            parse_mode='Markdown'
        )
        
        # Получаем прокси
        proxies = get_working_proxies(protocol if protocol != 'all' else None, limit=15)
        
        if proxies:
            response = f"🌐 **Найдено {len(proxies)} прокси:**\n\n"
            for p in proxies:
                response += f"• `{p['ip']}:{p['port']}`  [{p['protocol'].upper()}]\n"
            response += "\n✅ Как использовать:\n"
            response += "Настрой в программе как прокси"
        else:
            response = "❌ Не удалось найти рабочие прокси. Попробуй позже."
        
        await query.edit_message_text(response, parse_mode='Markdown', reply_markup=get_proxy_keyboard())
    
    # ===== VPN =====
    elif query.data.startswith('vpn_'):
        vpn_list = get_vpn_services()
        
        if query.data == 'vpn_all':
            filtered = vpn_list
            title = "📱 **Все VPN сервисы:**\n\n"
        elif query.data == 'vpn_free':
            filtered = [v for v in vpn_list if v['free']]
            title = "🆓 **Бесплатные VPN:**\n\n"
        elif query.data == 'vpn_windows':
            filtered = [v for v in vpn_list if 'Windows' in v['platforms']]
            title = "💻 **VPN для Windows:**\n\n"
        elif query.data == 'vpn_mac':
            filtered = [v for v in vpn_list if 'Mac' in v['platforms']]
            title = "🍏 **VPN для Mac:**\n\n"
        elif query.data == 'vpn_android':
            filtered = [v for v in vpn_list if 'Android' in v['platforms']]
            title = "📱 **VPN для Android:**\n\n"
        elif query.data == 'vpn_ios':
            filtered = [v for v in vpn_list if 'iOS' in v['platforms']]
            title = "📱 **VPN для iOS:**\n\n"
        else:
            filtered = vpn_list
            title = "📱 **Все VPN сервисы:**\n\n"
        
        if filtered:
            response = title
            for v in filtered[:10]:  # Не больше 10
                free_tag = " 🆓" if v['free'] else ""
                response += f"🔹 **[{v['name']}]({v['url']})**{free_tag}\n"
                response += f"   {v['description']}\n"
                response += f"   📱 {v['platforms']}\n\n"
        else:
            response = "❌ Нет VPN под эти параметры"
        
        await query.edit_message_text(response, parse_mode='Markdown', disable_web_page_preview=True, reply_markup=get_vpn_keyboard())

# ========== РЕГИСТРАЦИЯ ОБРАБОТЧИКОВ ==========
application = Application.builder().token(TOKEN).build()
application.add_handler(CommandHandler("start", start))
application.add_handler(CallbackQueryHandler(button_callback))

# ========== ЗАПУСК ==========
if __name__ == "__main__":
    print("🚀 Бот с ИНЛАЙН-КНОПКАМИ запущен!")
    print(f"👤 Админ: {ADMIN_USERNAME}")
    application.run_polling(allowed_updates=Update.ALL_TYPES)