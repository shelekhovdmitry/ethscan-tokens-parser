import json
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin

URL = "https://pedsovet.org/"

def parse_articles():
    try:
        print("Загружаем страницу pedsovet.org...")
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        
        resp = requests.get(URL, timeout=10, headers=headers)
        resp.raise_for_status()
        soup = BeautifulSoup(resp.text, 'html.parser')
        
        result = []
        
        # Основные селекторы для карточек статей на pedsovet.org
        card_selectors = [
            ".material-item",
            ".news-item", 
            ".item-news",
            "article.material",
            "div.material",
            ".content-item"
        ]
        
        cards = []
        for selector in card_selectors:
            found = soup.select(selector)
            if found:
                cards.extend(found)
        
        # Альтернативный поиск по ссылкам на статьи
        if not cards:
            article_links = soup.find_all('a', href=lambda x: x and '/article/' in x)
            for link in article_links:
                card = link.find_parent(['div', 'article', 'li'])
                if card and card not in cards:
                    cards.append(card)
        
        print(f"Найдено карточек для анализа: {len(cards)}")
        
        for card in cards:
            try:
                # Поиск заголовка
                title = None
                title_selectors = [
                    '.material-title',
                    '.news-title',
                    '.item-title',
                    'h2', 'h3', 'h4',
                    '.title',
                    '[class*="title"]'
                ]
                
                for selector in title_selectors:
                    title_elem = card.select_one(selector)
                    if title_elem and title_elem.get_text(strip=True):
                        title = title_elem.get_text(strip=True)
                        break
                
                # Если не нашли по селекторам, ищем текст в ссылке
                if not title:
                    link_elem = card.find('a', href=True)
                    if link_elem:
                        title = link_elem.get_text(strip=True)
                
                if not title or len(title) < 5:
                    continue
                
                # Поиск ссылки
                link_elem = card.find('a', href=True)
                if not link_elem:
                    continue
                    
                link = link_elem['href']
                if not link or '/article/' not in link:
                    continue
                
                # Обрабатываем относительные ссылки
                if link.startswith('/'):
                    link = urljoin(URL, link)
                
                article_data = {
                    "title": title,
                    "link": link
                }
                
                # Проверяем на дубликаты
                if not any(a['link'] == link for a in result):
                    result.append(article_data)
                    
            except Exception:
                continue
        
        return result
        
    except requests.RequestException as e:
        print(f"Ошибка при загрузке страницы: {e}")
        return []
    except Exception as e:
        print(f"Общая ошибка: {e}")
        return []

def save_to_json(data, filename="articles.json"):
    #Сохраняет данные в JSON файл
    try:
        with open(filename, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        print(f"Данные сохранены в файл: {filename}")
        return True
    except Exception as e:
        print(f"Ошибка при сохранении файла: {e}")
        return False

def print_results(articles):


    print("Найденные статьи:")
    print("="*80)
    
    for i, article in enumerate(articles, 1):
        print(f"{i:2d}. {article['title']}")
        print(f"     Ссылка: {article['link']}")
        print()

if __name__ == "__main__":

    print("ПАРСИНГ СТАТЕЙ С PEDSOVET.ORG")

    
    articles = parse_articles()
    
    if articles:
        print(f"Найдено статей: {len(articles)}")
        if save_to_json(articles):
            print_results(articles)
    else:
        print("Статьи не найдены")
