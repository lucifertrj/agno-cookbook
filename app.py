"""
- User's budget (desired_spend)
- Preferred form factor (e.g., edible, flower)
- Current promotions
- Real-time inventory
"""

from agno.agent import Agent
from agno.models.google import Gemini
from dotenv import load_dotenv
import os
load_dotenv()

os.environ["GOOGLE_API_KEY"] = os.getenv("GOOGLE_API_KEY")

def get_discounts(category: str = None):
    """Get active promotions and discounts"""
    return {
        "stackable": [
            {"type": "percentage", "value": 20, "name": "Weekend Special"},
            {"type": "percentage", "value": 10, "name": "Member Discount"}
        ],
        "non_stackable": [
            {"type": "fixed", "value": 10, "name": "$10 Off"},
            {"type": "percentage", "value": 25, "name": "Flash Sale"}
        ]
    }

def resolve_category(category_name: str):
    """Resolve category name to ID"""
    categories = {
        "edible": "6e73028e-8a2b-4f3c-9e1a-2d8c3b4a5f6g",
        "flower": "7f84139f-9b3c-5g4d-0f2b-3e9d4c5b6g7h",
        "vape": "8g95240g-0c4d-6h5e-1g3c-4f0e5d6c7h8i"
    }
    return {"category_id": categories.get(category_name.lower(), "unknown"), "category_name": category_name}

def query_inventory(category_id: str, budget: float):
    """Query available products in category"""
    edible_products = [
        {"id": "1", "name": "CBD Gummies 100mg (20ct)", "price": 40.00, "thc": 0, "cbd": 100},
        {"id": "2", "name": "Chocolate Bites 50mg (10ct)", "price": 30.00, "thc": 50, "cbd": 0},
        {"id": "3", "name": "Vegan Caramels 10mg (15ct)", "price": 18.00, "thc": 10, "cbd": 0},
        {"id": "4", "name": "Fruit Chews 10mg (10ct)", "price": 15.00, "thc": 10, "cbd": 0},
        {"id": "5", "name": "Mint Drops 5mg (20ct)", "price": 18.00, "thc": 5, "cbd": 0},
        {"id": "6", "name": "Luxury Truffles 100mg", "price": 60.00, "thc": 100, "cbd": 0},
        {"id": "7", "name": "Fast-Acting Nano Shots", "price": 51.00, "thc": 25, "cbd": 25},
        {"id": "8", "name": "Sleep Gummies 25mg", "price": 35.00, "thc": 5, "cbd": 20},
        {"id": "9", "name": "Energy Bites 15mg", "price": 22.00, "thc": 15, "cbd": 0},
        {"id": "10", "name": "Relief Capsules 30mg", "price": 45.00, "thc": 10, "cbd": 20}
    ]
    return [p for p in edible_products if p["price"] <= budget * 1.5]

def calculate_bundles(agent: Agent, products: list[dict], discounts: dict, budget: float):
    """Calculate and generate optimized bundles
    
    Args:
        agent: The agent instance
        products: List of product dictionaries with id, name, price, thc, and cbd fields
        discounts: Dictionary of available discounts
        budget: Maximum budget for the bundle
        
    Returns:
        List of bundle options
    """
    stackable_discount = sum(d["value"] for d in discounts["stackable"] if d["type"] == "percentage") / 100
    best_non_stackable = max(discounts["non_stackable"], key=lambda x: x["value"] if x["type"] == "percentage" else x["value"]/budget*100)
    
    def apply_discount(price, use_stackable=True):
        if use_stackable:
            return price * (1 - stackable_discount)
        else:
            if best_non_stackable["type"] == "percentage":
                return price * (1 - best_non_stackable["value"]/100)
            else:
                return max(0, price - best_non_stackable["value"])
    
    bundles = []
    
    sorted_by_discount = sorted(products, key=lambda p: p["price"] - apply_discount(p["price"]), reverse=True)
    bundle1 = []
    total1 = 0
    for product in sorted_by_discount:
        discounted = apply_discount(product["price"])
        if total1 + discounted <= budget:
            bundle1.append({**product, "discounted_price": discounted})
            total1 += discounted
    
    sorted_by_price = sorted(products, key=lambda p: apply_discount(p["price"]))
    bundle2 = []
    total2 = 0
    for product in sorted_by_price:
        discounted = apply_discount(product["price"])
        if total2 + discounted <= budget:
            bundle2.append({**product, "discounted_price": discounted})
            total2 += discounted
    
    sorted_by_premium = sorted(products, key=lambda p: p["price"], reverse=True)
    bundle3 = []
    total3 = 0
    for product in sorted_by_premium[:3]:
        discounted = apply_discount(product["price"], use_stackable=False)
        if total3 + discounted <= budget:
            bundle3.append({**product, "discounted_price": discounted})
            total3 += discounted
    
    return [
        {"type": "Maximum Savings", "items": bundle1, "total": total1, "emoji": "💰"},
        {"type": "Most Items", "items": bundle2, "total": total2, "emoji": "📦"},
        {"type": "Premium Selection", "items": bundle3, "total": total3, "emoji": "💎"}
    ]

agent = Agent(
    model = Gemini(id="gemini-2.0-flash"),
    tools=[get_discounts, resolve_category, query_inventory, calculate_bundles],
    session_state={"budget": 0, "category": "", "products": [], "discounts": {}},
    instructions="""You are a cannabis bundle recommendation assistant. Follow these steps:
    1. Get active discounts (use category-specific discounts when available)
    2. Resolve the category to get ID (support for edibles, flower, concentrates, vapes)
    3. Query inventory for products within budget
    4. Calculate optimized bundles using the best discount combinations
    5. Display exactly 3 recommendations in the specified format with emojis:
       - 💰 Maximum Savings Bundle (best discounts)
       - 📦 Maximum Quantity Bundle (most items)
       - 💎 Premium Selection (highest quality items)
    
    For each bundle, show:
    - Bundle name with emoji
    - Total price after discounts
    - Savings amount and percentage
    - List of products with original and discounted prices
    - Any applicable discount codes
    
    Be conversational and helpful when explaining the benefits of each bundle.""",
    add_state_in_messages=True,
    markdown=True,
    show_tool_calls=True
)

agent.print_response("I have $100 for edibles", stream=True)
