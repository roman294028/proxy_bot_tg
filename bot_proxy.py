import os
import logging
import requests
import time
import random
import re
import json
from datetime import datetime
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes, CallbackQueryHandler
from urllib.parse import quote, urlparse

# Настройка логирования
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Токен бота
TOKEN = '8674299514:AAFtGkSZPO__V1yGktKmh0wz-ZM-WbNxPAE'

# Твой Telegram username
ADMIN_USERNAME = "@hoshino_aaai"

# ========== КЭШ ДЛЯ ОПТИМИЗАЦИИ ==========
cache = {
    'proxies': {'data': [], 'last_update': 0},
    'vpn': {'data': [], 'last_update': 0},
    'dpi': {'data': [], 'last_update': 0},
    'browsers': {'data': [], 'last_update': 0},
    'dns': {'data': [], 'last_update': 0},
    'news': {'data': [], 'last_update': 0}
}
CACHE_TTL = 300  # 5 минут

# ========== ФУНКЦИИ ДЛЯ ПОИСКА В РЕАЛЬНОМ ВРЕМЕНИ ==========

def search_realtime(query_type, limit=10):
    """
    УНИВЕРСАЛЬНАЯ ФУНКЦИЯ ПОИСКА В РЕАЛЬНОМ ВРЕМЕНИ
    Ищет по всем доступным источникам актуальную информацию
    """
    current_time = time.time()
    
    # Проверяем кэш
    if query_type in cache and current_time - cache[query_type]['last_update'] < CACHE_TTL:
        if cache[query_type]['data']:
            return cache[query_type]['data'][:limit]
    
    results = []
    
    # ===== ИСТОЧНИК 1: GitHub репозитории =====
    try:
        github_sources = {
            'proxies': [
                'https://raw.githubusercontent.com/jetkai/proxy-list/main/online-proxies/txt/proxies.txt',
                'https://raw.githubusercontent.com/ShiftyTR/Proxy-List/master/http.txt',
                'https://raw.githubusercontent.com/ShiftyTR/Proxy-List/master/socks4.txt',
                'https://raw.githubusercontent.com/ShiftyTR/Proxy-List/master/socks5.txt'
            ],
            'vpn': [
                'https://raw.githubusercontent.com/awesome-vpn/awesome-vpn/master/README.md',
                'https://raw.githubusercontent.com/youxam/youxam-v2ray/main/README.md'
            ],
            'dpi': [
                'https://raw.githubusercontent.com/bol-van/zapret/master/README.md',
                'https://raw.githubusercontent.com/dovecoteescapee/ByeDPIAndroid/master/README.md'
            ]
        }
        
        if query_type in github_sources:
            for url in github_sources[query_type][:2]:  # Берём первые 2 источника
                try:
                    response = requests.get(url, timeout=8)
                    if response.status_code == 200:
                        content = response.text
                        lines = content.split('\n')[:30]
                        
                        if query_type == 'proxies':
                            for line in lines:
                                if ':' in line and len(line.split(':')) == 2:
                                    ip, port = line.strip().split(':')
                                    if ip.count('.') == 3 and port.isdigit():
                                        results.append({
                                            'type': 'proxy',
                                            'name': f"Прокси {ip}:{port}",
                                            'content': f"`{ip}:{port}`",
                                            'source': url.split('/')[-1],
                                            'timestamp': datetime.now().strftime('%H:%M')
                                        })
                        
                        elif query_type == 'vpn':
                            for line in lines:
                                if 'vless://' in line or 'vmess://' in line or 'trojan://' in line:
                                    # Извлекаем ссылки на конфиги
                                    configs = re.findall(r'(vless|vmess|trojan|ss)://[^\s)]+', line)
                                    for config in configs[:3]:
                                        results.append({
                                            'type': 'vpn_config',
                                            'name': f"🔐 {config[:30]}...",
                                            'content': config,
                                            'source': 'GitHub',
                                            'timestamp': datetime.now().strftime('%H:%M')
                                        })
                except Exception as e:
                    logger.error(f"GitHub source error {url}: {e}")
    except Exception as e:
        logger.error(f"GitHub search error: {e}")
    
    # ===== ИСТОЧНИК 2: API бесплатных прокси =====
    if query_type == 'proxies':
        proxy_apis = [
            ('http', 'https://api.proxyscrape.com/v2/?request=getproxies&protocol=http&timeout=5000&country=all'),
            ('socks4', 'https://api.proxyscrape.com/v2/?request=getproxies&protocol=socks4&timeout=5000&country=all'),
            ('socks5', 'https://api.proxyscrape.com/v2/?request=getproxies&protocol=socks5&timeout=5000&country=all')
        ]
        
        for proto, url in proxy_apis:
            try:
                response = requests.get(url, timeout=10)
                if response.status_code == 200:
                    proxies = response.text.strip().split('\r\n')[:10]
                    for proxy in proxies:
                        if ':' in proxy:
                            results.append({
                                'type': 'proxy',
                                'name': f"{proto.upper()} прокси",
                                'content': f"`{proxy}`",
                                'protocol': proto,
                                'source': 'proxyscrape',
                                'timestamp': datetime.now().strftime('%H:%M')
                            })
            except Exception as e:
                logger.error(f"ProxyScrape error {proto}: {e}")
    
    # ===== ИСТОЧНИК 3: Поиск актуальных новостей и статей =====
    if query_type == 'news':
        # Используем GitHub для поиска свежих обсуждений
        try:
            search_queries = ['youtube+block+bypass', 'vpn+free+2026', 'dpi+bypass+android']
            for q in search_queries[:2]:
                url = f"https://api.github.com/search/repositories?q={q}&sort=updated"
                response = requests.get(url, timeout=8)
                if response.status_code == 200:
                    data = response.json()
                    for item in data.get('items', [])[:5]:
                        results.append({
                            'type': 'news',
                            'name': f"📰 {item['name']}",
                            'content': item['description'] or 'Актуальный репозиторий',
                            'url': item['html_url'],
                            'updated': item['updated_at'][:10],
                            'timestamp': datetime.now().strftime('%H:%M')
                        })
        except Exception as e:
            logger.error(f"News search error: {e}")
    
    # ===== ИСТОЧНИК 4: MTProto прокси для Telegram =====
    if query_type == 'proxies':
        try:
            mtproto_sources = [
                'https://raw.githubusercontent.com/soot-af/MTProto-proxy/main/proxy.txt',
                'https://raw.githubusercontent.com/miruxs/MTProtoProxyCollector/main/proxies.txt'
            ]
            for url in mtproto_sources:
                response = requests.get(url, timeout=8)
                if response.status_code == 200:
                    lines = response.text.strip().split('\n')[:5]
                    for line in lines:
                        if 't.me/proxy' in line:
                            results.append({
                                'type': 'mtproto',
                                'name': '📱 Telegram MTProto',
                                'content': line,
                                'source': 'telegram',
                                'timestamp': datetime.now().strftime('%H:%M')
                            })
        except Exception as e:
            logger.error(f"MTProto error: {e}")
    
    # ===== ИСТОЧНИК 5: Актуальные DPI-обходчики =====
    if query_type == 'dpi':
        dpi_items = [
            {
                'name': 'Zapret (Windows/Linux)',
                'content': 'Обход DPI на ПК. Работает через nfqws/winpcap.',
                'url': 'https://github.com/bol-van/zapret',
                'updated': '2026'
            },
            {
                'name': 'ByeDPI Android',
                'content': 'Обход DPI на Android без root',
                'url': 'https://github.com/dovecoteescapee/ByeDPIAndroid',
                'updated': '2026'
            },
            {
                'name': 'GoodByeDPI (Windows)',
                'content': 'Простой обходчик для Windows',
                'url': 'https://github.com/ValdikSS/GoodbyeDPI',
                'updated': '2026'
            },
            {
                'name': 'PowerTunnel (Java)',
                'content': 'Кроссплатформенный обходчик',
                'url': 'https://github.com/krlvm/PowerTunnel',
                'updated': '2026'
            }
        ]
        
        # Проверяем, какие из них ещё актуальны (пытаемся достучаться до GitHub)
        for item in dpi_items:
            try:
                # Проверяем, жив ли репозиторий
                api_url = f"https://api.github.com/repos/{'/'.join(item['url'].split('/')[-2:])}"
                r = requests.get(api_url, timeout=3)
                if r.status_code == 200:
                    data = r.json()
                    item['updated'] = data.get('updated_at', '2026')[:10]
                    results.append({
                        'type': 'dpi',
                        'name': f"🛡️ {item['name']}",
                        'content': item['content'],
                        'url': item['url'],
                        'updated': item['updated'],
                        'timestamp': datetime.now().strftime('%H:%M')
                    })
            except:
                # Если не достучались, добавляем как есть
                results.append({
                    'type': 'dpi',
                    'name': f"🛡️ {item['name']}",
                    'content': item['content'],
                    'url': item['url'],
                    'updated': item['updated'],
                    'timestamp': datetime.now().strftime('%H:%M')
                })
    
    # Сохраняем в кэш
    if query_type in cache:
        cache[query_type]['data'] = results
        cache[query_type]['last_update'] = current_time
    
    return results[:limit]

# ========== ПОИСК ПО ЗАПРОСУ ПОЛЬЗОВАТЕЛЯ ==========

def search_by_query(user_query):
    """
    Ищет информацию по любому запросу пользователя
    """
    query = user_query.lower().strip()
    results = []
    
    # Определяем тип запроса
    if any(word in query for word in ['прокси', 'proxy', 'socks', 'http']):
        results = search_realtime('proxies', 15)
    elif any(word in query for word in ['впн', 'vpn', 'vless', 'vmess', 'trojan']):
        results = search_realtime('vpn', 15)
    elif any(word in query for word in ['dpi', 'запрет', 'обход', 'bypass']):
        results = search_realtime('dpi', 15)
    elif any(word in query for word in ['новости', 'актуально', 'свежие']):
        results = search_realtime('news', 10)
    elif any(word in query for word in ['ютуб', 'youtube', 'video']):
        # Смешанный поиск для YouTube
        results.extend(search_realtime('vpn', 5))
        results.extend(search_realtime('dpi', 5))
    else:
        # Общий поиск по всем категориям
        results.extend(search_realtime('proxies', 3))
        results.extend(search_realtime('vpn', 3))
        results.extend(search_realtime('dpi', 3))
        results.extend(search_realtime('news', 3))
    
    return results

# ========== ИНЛАЙН-КЛАВИАТУРЫ ==========

def get_main_keyboard():
    """Главная клавиатура"""
    keyboard = [
        [InlineKeyboardButton("🌐 Найти прокси", callback_data='search_proxies')],
        [InlineKeyboardButton("🔒 Найти VPN/конфиги", callback_data='search_vpn')],
        [InlineKeyboardButton("🛡️ DPI-обходчики", callback_data='search_dpi')],
        [InlineKeyboardButton("📰 Актуальные новости", callback_data='search_news')],
        [InlineKeyboardButton("🔍 СВОЙ ЗАПРОС", callback_data='custom_search')],
        [InlineKeyboardButton("❓ Помощь", callback_data='menu_help')]
    ]
    return InlineKeyboardMarkup(keyboard)

def get_back_keyboard():
    """Клавиатура с кнопкой назад"""
    keyboard = [
        [InlineKeyboardButton("◀️ Назад в меню", callback_data='back_main')]
    ]
    return InlineKeyboardMarkup(keyboard)

# ========== ОБРАБОТЧИКИ ==========

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик команды /start"""
    welcome_text = (
        "👋 **Привет! Я живой поисковик по прокси и обходам**\n\n"
        "🔹 **🌐 Найти прокси** — рабочие прокси прямо сейчас\n"
        "🔹 **🔒 Найти VPN/конфиги** — актуальные конфиги VLESS/VMESS/Trojan\n"
        "🔹 **🛡️ DPI-обходчики** — программы для обхода блокировок\n"
        "🔹 **📰 Актуальные новости** — свежие репозитории и обсуждения\n"
        "🔹 **🔍 СВОЙ ЗАПРОС** — напиши что хочешь найти\n\n"
        "⚡ **Вся информация — в реальном времени с GitHub и API**\n"
        "⏱️ Обновление каждые 5 минут\n\n"
        "👇 Выбери категорию:"
    )
    await update.message.reply_text(welcome_text, parse_mode='Markdown', reply_markup=get_main_keyboard())

async def button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик нажатий на инлайн-кнопки"""
    query = update.callback_query
    await query.answer()
    
    if query.data == 'back_main':
        await query.edit_message_text(
            "👋 **Главное меню**\n\nВыбери категорию поиска:",
            parse_mode='Markdown',
            reply_markup=get_main_keyboard()
        )
        return
    
    elif query.data == 'menu_help':
        help_text = (
            "❓ **Помощь**\n\n"
            "🔹 **Как это работает:**\n"
            "Бот ищет информацию в реальном времени на:\n"
            "• GitHub репозиториях\n"
            "• API бесплатных прокси\n"
            "• Сборщиках MTProto\n"
            "• Актуальных обсуждениях\n\n"
            "🔹 **Обновление:**\n"
            "Каждые 5 минут кэш обновляется\n"
            "При каждом запросе — проверка свежести\n\n"
            "🔹 **Связь с админом:**\n"
            f"{ADMIN_USERNAME} — только по важным вопросам\n\n"
            "🔹 **Версия:** 4.0 (Живой поиск)"
        )
        await query.edit_message_text(help_text, parse_mode='Markdown', reply_markup=get_back_keyboard())
        return
    
    elif query.data == 'custom_search':
        await query.edit_message_text(
            "🔍 **Напиши свой запрос**\n\n"
            "Примеры:\n"
            "• `прокси socks5`\n"
            "• `vless конфиги 2026`\n"
            "• `обход ютуба на андроид`\n"
            "• `dpi обход windows`\n"
            "• `свежие новости по блокировкам`\n\n"
            "Я найду всё в реальном времени!",
            parse_mode='Markdown',
            reply_markup=get_back_keyboard()
        )
        # Сохраняем состояние, что ждём запрос
        context.user_data['awaiting_query'] = True
        return
    
    # Обработка поисковых категорий
    search_type = query.data.replace('search_', '')
    
    # Отправляем сообщение о поиске
    await query.edit_message_text(
        f"🔍 **Ищу актуальную информацию...**\nТип: {search_type}\n⏱️ Реальное время",
        parse_mode='Markdown'
    )
    
    # Выполняем поиск
    if search_type == 'proxies':
        results = search_realtime('proxies', 20)
    elif search_type == 'vpn':
        results = search_realtime('vpn', 20)
    elif search_type == 'dpi':
        results = search_realtime('dpi', 15)
    elif search_type == 'news':
        results = search_realtime('news', 15)
    else:
        results = []
    
    # Формируем ответ
    if results:
        response = f"📋 **Найдено {len(results)} результатов:**\n\n"
        for i, item in enumerate(results[:15], 1):
            if item['type'] == 'proxy':
                response += f"{i}. 🌐 {item['content']}\n"
            elif item['type'] == 'mtproto':
                response += f"{i}. 📱 {item['content']}\n"
            elif item['type'] == 'vpn_config':
                response += f"{i}. 🔐 {item['name']}\n   `{item['content'][:50]}...`\n"
            elif item['type'] == 'dpi':
                response += f"{i}. 🛡️ **{item['name']}**\n   {item['content']}\n"
                if 'url' in item:
                    response += f"   [Ссылка]({item['url']})\n"
            elif item['type'] == 'news':
                response += f"{i}. 📰 **{item['name']}**\n   {item['content']}\n"
                if 'url' in item:
                    response += f"   [Ссылка]({item['url']})\n"
            response += f"   🕒 {item['timestamp']}\n\n"
        
        response += "⚡ Информация обновлена в реальном времени"
    else:
        response = "❌ Не удалось найти информацию. Попробуй другой запрос."
    
    await query.edit_message_text(response, parse_mode='Markdown', disable_web_page_preview=True, reply_markup=get_back_keyboard())

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик текстовых сообщений (пользовательский запрос)"""
    
    # Проверяем, ждём ли мы запрос
    if context.user_data.get('awaiting_query'):
        context.user_data['awaiting_query'] = False
        user_query = update.message.text
        
        # Отправляем статус печати
        await update.message.chat.send_action(action="typing")
        
        # Отправляем сообщение о поиске
        status_msg = await update.message.reply_text(
            f"🔍 **Ищу по запросу:** '{user_query}'\n⏱️ Реальное время...",
            parse_mode='Markdown'
        )
        
        # Выполняем поиск
        results = search_by_query(user_query)
        
        # Формируем ответ
        if results:
            response = f"📋 **Найдено {len(results)} результатов по запросу** '{user_query}':\n\n"
            for i, item in enumerate(results[:15], 1):
                if item['type'] == 'proxy':
                    response += f"{i}. 🌐 {item['content']}\n"
                elif item['type'] == 'mtproto':
                    response += f"{i}. 📱 {item['content']}\n"
                elif item['type'] == 'vpn_config':
                    response += f"{i}. 🔐 {item['name']}\n   `{item['content'][:50]}...`\n"
                elif item['type'] == 'dpi':
                    response += f"{i}. 🛡️ **{item['name']}**\n   {item['content']}\n"
                elif item['type'] == 'news':
                    response += f"{i}. 📰 **{item['name']}**\n   {item['content']}\n"
                response += f"   🕒 {item['timestamp']}\n\n"
            
            response += "⚡ Информация в реальном времени с GitHub/API"
        else:
            response = f"❌ По запросу '{user_query}' ничего не найдено.\n\nПопробуй другие слова или выбери категорию в меню."
        
        await status_msg.edit_text(response, parse_mode='Markdown', disable_web_page_preview=True, reply_markup=get_back_keyboard())
    else:
        # Если не ждали запрос, предлагаем меню
        await update.message.reply_text(
            "👋 Используй меню для поиска или напиши /start",
            reply_markup=get_main_keyboard()
        )

# ========== РЕГИСТРАЦИЯ ОБРАБОТЧИКОВ ==========
application = Application.builder().token(TOKEN).build()
application.add_handler(CommandHandler("start", start))
application.add_handler(CallbackQueryHandler(button_callback))
application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

# ========== ЗАПУСК ==========
if __name__ == "__main__":
    print("🚀 Бот с ЖИВЫМ ПОИСКОМ запущен!")
    print(f"👤 Админ: {ADMIN_USERNAME}")
    print(f"⚡ Режим: реальное время, кэш 5 минут")
    print(f"📊 Источники: GitHub API, ProxyScrape, MTProto сборщики")
    application.run_polling(allowed_updates=Update.ALL_TYPES)
