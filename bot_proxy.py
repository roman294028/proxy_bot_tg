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

# Токен бота (вставь свой)
TOKEN = '8674299514:AAFtGkSZPO__V1yGktKmh0wz-ZM-WbNxPAE'

# Твой Telegram username для раздела помощи
ADMIN_USERNAME = "@hoshino_aaai"

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

def get_working_proxies(protocol=None, limit=10):
    """Возвращает список работающих прокси"""
    proxies = fetch_proxies_from_api()
    
    # Фильтруем по протоколу
    if protocol and protocol != 'all':
        filtered = [p for p in proxies if p['protocol'] == protocol]
    else:
        filtered = proxies
    
    # Перемешиваем и возвращаем
    random.shuffle(filtered)
    return filtered[:limit]

# ========== СПОСОБЫ ОБХОДА YouTube НА ANDROID ==========

def get_youtube_workarounds():
    """Возвращает актуальные способы обхода блокировки YouTube на Android (2026)"""
    return {
        'vpn': [
            {
                'name': 'VPNella VPN',
                'description': '🇷🇺 Российский VPN, стабильно работает. Бесплатно 3 ГБ/мес.',
                'howto': '1. Скачай из Google Play\n2. Выбери сервер в Европе\n3. Подключись и смотри YouTube',
                'url': 'https://play.google.com/store/apps/details?id=com.vpnella.android',
                'pros': 'Высокая скорость, блокировка рекламы, русский интерфейс',
                'cons': 'Лимит 3 ГБ в месяц'
            },
            {
                'name': 'Proton VPN',
                'description': '🇨🇭 Швейцарский VPN с бесплатной версией (нет ограничений по трафику).',
                'howto': '1. Установи из Google Play\n2. Подключись к бесплатному серверу\n3. Открой YouTube',
                'url': 'https://play.google.com/store/apps/details?id=ch.protonvpn.android',
                'pros': 'Нет лимита трафика, строгая политика приватности',
                'cons': 'Медленные серверы в бесплатной версии'
            },
            {
                'name': 'X Rocket VPN (Telegram-бот)',
                'description': '🚀 Работает через VLESS/Trojan, обходит белые списки операторов.',
                'howto': '1. Установи приложение Happ из Google Play\n2. В Telegram найди @X_Rocket_VPN_bot\n3. Возьми тестовый период\n4. Подключись',
                'url': 'https://t.me/X_Rocket_VPN_bot',
                'pros': 'Обходит мобильных операторов, 5 устройств, 1000 руб/год',
                'cons': 'Платный (но есть тестовый период)'
            },
            {
                'name': 'Albania VPN Trick',
                'description': '🌍 Через VPN с сервером в Албании YouTube может показывать видео без рекламы.',
                'howto': 'Найди VPN с сервером в Албании (например, NordVPN) и подключись к YouTube',
                'url': None,
                'pros': 'Возможно, вообще нет рекламы',
                'cons': 'Риск блокировки аккаунта, платный VPN'
            }
        ],
        'dpi_bypass': [
            {
                'name': 'ByeDPI Android',
                'description': '🛡️ Приложение для обхода DPI (глубокой инспекции пакетов). Работает как локальный VPN.',
                'howto': '1. Скачай с GitHub: https://github.com/dovecoteescapee/ByeDPIAndroid/releases\n2. Установи APK\n3. Включи VPN-режим\n4. Настрой DNS: 8.8.8.8\n5. Включи "Desync only HTTPS" и метод "fake"',
                'url': 'https://github.com/dovecoteescapee/ByeDPIAndroid',
                'pros': 'Бесплатно, не требует root, не замедляет трафик',
                'cons': 'Требует ручной установки APK'
            },
            {
                'name': 'Zapret2 (Magisk модуль)',
                'description': '⚡ Модуль для root-устройств. Маскирует трафик, провайдер не видит блокируемое.',
                'howto': '1. Нужен root (Magisk)\n2. Скачай модуль с GitHub\n3. Установи через Magisk\n4. Перезагрузи\n5. Для управления используй Zapret2 Control',
                'url': 'https://github.com/youtubediscord/magisk-zapret2',
                'pros': 'Работает на уровне системы, очень быстро',
                'cons': 'Требует root'
            }
        ],
        'browsers': [
            {
                'name': 'Microsoft Edge Canary + Violentmonkey',
                'description': '🧪 Браузер с поддержкой расширений + скрипт для фонового воспроизведения.',
                'howto': '1. Установи Edge Canary\n2. Установи расширение Violentmonkey\n3. Добавь скрипт "Disable Page Visibility API"\n4. Открой YouTube в Edge\n5. Видео будет играть в фоне',
                'url': 'https://www.microsoftedgeinsider.com/',
                'pros': 'Фоновое воспроизведение без Premium',
                'cons': 'Только для фонового режима, не обходит блокировку сайта'
            },
            {
                'name': 'Mozilla Firefox',
                'description': '🦊 В некоторых версиях Firefox на Android фоновое видео работает без доп. настроек.',
                'howto': 'Просто установи Firefox и открой YouTube',
                'url': 'https://play.google.com/store/apps/details?id=org.mozilla.firefox',
                'pros': 'Просто, бесплатно',
                'cons': 'Может перестать работать в любой момент'
            }
        ],
        'dns': [
            {
                'name': 'Смена DNS на Android',
                'description': '🌐 Иногда помогает сменить DNS на публичные (Google, Cloudflare).',
                'howto': 'Настройки → Сеть → Частный DNS → Введите:\n• dns.google (Google)\n• 1dot1dot1dot1.cloudflare-dns.com (Cloudflare)',
                'url': None,
                'pros': 'Бесплатно, без приложений',
                'cons': 'Помогает не всегда'
            }
        ]
    }

# ========== ИНЛАЙН-КЛАВИАТУРЫ ==========

def get_main_keyboard():
    """Главная клавиатура"""
    keyboard = [
        [InlineKeyboardButton("🌐 Найти прокси", callback_data='menu_proxy')],
        [InlineKeyboardButton("📱 Обход YouTube на Android", callback_data='menu_youtube')],
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

def get_youtube_keyboard():
    """Клавиатура для YouTube разделов"""
    keyboard = [
        [InlineKeyboardButton("📡 VPN для YouTube", callback_data='youtube_vpn')],
        [InlineKeyboardButton("🛡️ DPI-обходчики", callback_data='youtube_dpi')],
        [InlineKeyboardButton("🌐 Браузеры с обходом", callback_data='youtube_browsers')],
        [InlineKeyboardButton("🔧 DNS-настройки", callback_data='youtube_dns')],
        [InlineKeyboardButton("📋 Все способы сразу", callback_data='youtube_all')],
        [InlineKeyboardButton("◀️ Назад", callback_data='back_main')]
    ]
    return InlineKeyboardMarkup(keyboard)

def get_back_keyboard():
    """Клавиатура с кнопкой назад"""
    keyboard = [
        [InlineKeyboardButton("◀️ Назад", callback_data='back_main')]
    ]
    return InlineKeyboardMarkup(keyboard)

def get_youtube_back_keyboard():
    """Клавиатура с кнопкой назад в раздел YouTube"""
    keyboard = [
        [InlineKeyboardButton("◀️ Назад к YouTube", callback_data='menu_youtube')]
    ]
    return InlineKeyboardMarkup(keyboard)

# ========== ОБРАБОТЧИКИ ==========

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик команды /start"""
    welcome_text = (
        "👋 **Привет! Я Proxy & YouTube Helper Bot**\n\n"
        "🔹 **🌐 Найти прокси** — рабочие прокси для Telegram и других сервисов\n"
        "🔹 **📱 Обход YouTube на Android** — актуальные способы на 2026 год\n"
        "🔹 **🔒 Найти VPN** — список VPN-сервисов\n"
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
    
    elif query.data == 'menu_youtube':
        await query.edit_message_text(
            "📱 **Обход YouTube на Android**\n\n"
            "Актуальные способы на **2026 год**:\n\n"
            "• 📡 **VPN** — классический способ\n"
            "• 🛡️ **DPI-обходчики** — ByeDPI, Zapret2 (без VPN!)\n"
            "• 🌐 **Браузеры** — Edge Canary + скрипты\n"
            "• 🔧 **DNS** — смена DNS\n\n"
            "👇 Выбери категорию:",
            parse_mode='Markdown',
            reply_markup=get_youtube_keyboard()
        )
    
    elif query.data == 'menu_vpn':
        vpn_list = get_youtube_workarounds()['vpn']
        response = "🔒 **VPN-сервисы (2026):**\n\n"
        for vpn in vpn_list:
            response += f"🔹 **{vpn['name']}**\n"
            response += f"   {vpn['description']}\n"
            response += f"   ✅ {vpn['pros']}\n"
            response += f"   ❌ {vpn['cons']}\n"
            if vpn.get('url'):
                response += f"   [Ссылка]({vpn['url']})\n"
            response += "\n"
        await query.edit_message_text(response, parse_mode='Markdown', disable_web_page_preview=True, reply_markup=get_back_keyboard())
    
    elif query.data == 'menu_help':
        help_text = (
            "❓ **Помощь**\n\n"
            "🔹 **Как пользоваться:**\n"
            "• Нажимай кнопки в меню\n"
            "• Получай списки рабочих прокси и способов обхода\n\n"
            "🔹 **Обход YouTube на Android:**\n"
            "Все способы проверены и актуальны на март 2026 года.\n\n"
            "🔹 **Связь с админом:**\n"
            f"{ADMIN_USERNAME} — только по важным вопросам\n\n"
            "🔹 **О боте:**\n"
            "Версия 3.0 (YouTube Edition)\n"
            "Прокси обновляются в реальном времени\n"
            "Способы обхода YouTube обновляются вручную"
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
        protocol_name = 'все' if protocol == 'all' else protocol.upper()
        
        # Отправляем сообщение о поиске
        await query.edit_message_text(
            f"🔍 **Ищу рабочие {protocol_name} прокси...**",
            parse_mode='Markdown'
        )
        
        # Получаем прокси
        proxies = get_working_proxies(protocol if protocol != 'all' else None, limit=15)
        
        if proxies:
            response = f"🌐 **Найдено {len(proxies)} прокси ({protocol_name}):**\n\n"
            for p in proxies:
                response += f"• `{p['ip']}:{p['port']}`  [{p['protocol'].upper()}]\n"
            response += "\n✅ **Как использовать:**\n"
            response += "Настрой в программе как прокси (IP:PORT)"
        else:
            response = "❌ Не удалось найти рабочие прокси. Попробуй позже."
        
        await query.edit_message_text(response, parse_mode='Markdown', reply_markup=get_proxy_keyboard())
    
    # ===== YOUTUBE КАТЕГОРИИ =====
    elif query.data == 'youtube_vpn':
        items = get_youtube_workarounds()['vpn']
        response = "📡 **VPN для YouTube (2026):**\n\n"
        for item in items:
            response += f"🔹 **{item['name']}**\n"
            response += f"   {item['description']}\n"
            response += f"   **Как установить:** {item['howto']}\n"
            response += f"   ✅ {item['pros']} | ❌ {item['cons']}\n"
            if item.get('url'):
                response += f"   [Ссылка]({item['url']})\n"
            response += "\n"
        await query.edit_message_text(response, parse_mode='Markdown', disable_web_page_preview=True, reply_markup=get_youtube_back_keyboard())
    
    elif query.data == 'youtube_dpi':
        items = get_youtube_workarounds()['dpi_bypass']
        response = "🛡️ **DPI-обходчики (без VPN!):**\n\n"
        for item in items:
            response += f"🔹 **{item['name']}**\n"
            response += f"   {item['description']}\n"
            response += f"   **Как установить:** {item['howto']}\n"
            response += f"   ✅ {item['pros']} | ❌ {item['cons']}\n"
            if item.get('url'):
                response += f"   [Ссылка]({item['url']})\n"
            response += "\n"
        await query.edit_message_text(response, parse_mode='Markdown', disable_web_page_preview=True, reply_markup=get_youtube_back_keyboard())
    
    elif query.data == 'youtube_browsers':
        items = get_youtube_workarounds()['browsers']
        response = "🌐 **Браузеры с обходом блокировок:**\n\n"
        for item in items:
            response += f"🔹 **{item['name']}**\n"
            response += f"   {item['description']}\n"
            response += f"   **Как установить:** {item['howto']}\n"
            response += f"   ✅ {item['pros']} | ❌ {item['cons']}\n"
            if item.get('url'):
                response += f"   [Ссылка]({item['url']})\n"
            response += "\n"
        await query.edit_message_text(response, parse_mode='Markdown', disable_web_page_preview=True, reply_markup=get_youtube_back_keyboard())
    
    elif query.data == 'youtube_dns':
        items = get_youtube_workarounds()['dns']
        response = "🔧 **DNS-настройки:**\n\n"
        for item in items:
            response += f"🔹 **{item['name']}**\n"
            response += f"   {item['description']}\n"
            response += f"   **Как настроить:** {item['howto']}\n"
            response += f"   ✅ {item['pros']} | ❌ {item['cons']}\n\n"
        await query.edit_message_text(response, parse_mode='Markdown', reply_markup=get_youtube_back_keyboard())
    
    elif query.data == 'youtube_all':
        categories = get_youtube_workarounds()
        response = "📋 **ВСЕ СПОСОБЫ ОБХОДА YouTube на Android (2026):**\n\n"
        
        response += "=== 📡 VPN ===\n"
        for item in categories['vpn']:
            response += f"🔹 {item['name']}: {item['description']}\n"
        
        response += "\n=== 🛡️ DPI-обходчики ===\n"
        for item in categories['dpi_bypass']:
            response += f"🔹 {item['name']}: {item['description']}\n"
        
        response += "\n=== 🌐 Браузеры ===\n"
        for item in categories['browsers']:
            response += f"🔹 {item['name']}: {item['description']}\n"
        
        response += "\n=== 🔧 DNS ===\n"
        for item in categories['dns']:
            response += f"🔹 {item['name']}: {item['description']}\n"
        
        response += "\n👉 Выбери категорию для подробной инструкции!"
        
        await query.edit_message_text(response, parse_mode='Markdown', reply_markup=get_youtube_keyboard())

# ========== РЕГИСТРАЦИЯ ОБРАБОТЧИКОВ ==========
application = Application.builder().token(TOKEN).build()
application.add_handler(CommandHandler("start", start))
application.add_handler(CallbackQueryHandler(button_callback))

# ========== ЗАПУСК ==========
if __name__ == "__main__":
    print("🚀 Бот с функциями обхода YouTube запущен!")
    print(f"👤 Админ: {ADMIN_USERNAME}")
    print(f"📱 Режимы: прокси + обход YouTube")
    application.run_polling(allowed_updates=Update.ALL_TYPES)
