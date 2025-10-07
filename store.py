PRODUCTS = {
    "psn10": {
        "sku": "psn10",
        "name": "PSN Gift Card $10",
        "price_usd": 10.0,
        "image": "https://i.imgur.com/7bKQZ7p.jpg",
        "category": "🎮 گیفت کارت بازی"
    },
    "steam20": {
        "sku": "steam20",
        "name": "Steam Wallet $20",
        "price_usd": 20.0,
        "image": "https://i.imgur.com/0Y8z8.jpg",
        "category": "🎮 گیفت کارت بازی"
    },
    "pm50": {
        "sku": "pm50",
        "name": "Perfect Money $50",
        "price_usd": 50.0,
        "image": "https://i.imgur.com/3ZQ3.jpg",
        "category": "💳 ووچر"
    }
}

def categories_list():
    cats = {}
    for p in PRODUCTS.values():
        cats.setdefault(p['category'], []).append(p)
    return cats
