"""FoodDeliveryApp: Singleton facade that coordinates everything."""
from typing import Dict, List, Optional

from exceptions import *
from models import (Cart, Customer, DeliveryAgent, DELIVERY_FEE, FREE_DELIVERY_ABOVE,
                    Order, OrderLine, OrderStatus, Restaurant)
from payment import Payment, PaymentStrategy


class FoodDeliveryApp:
    _instance: Optional["FoodDeliveryApp"] = None

    @classmethod
    def get_instance(cls):
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    @classmethod
    def reset(cls):
        cls._instance = None

    def __init__(self):
        self.customers: Dict[str, Customer] = {}
        self.agents: Dict[str, DeliveryAgent] = {}
        self.restaurants: Dict[str, Restaurant] = {}
        self.orders: Dict[str, Order] = {}

    # ---- setup
    def register_customer(self, name, phone, address) -> Customer:
        c = Customer(f"C{len(self.customers) + 1:03d}", name, phone, address)
        self.customers[c.id] = c
        return c

    def register_agent(self, name, phone) -> DeliveryAgent:
        a = DeliveryAgent(f"A{len(self.agents) + 1:03d}", name, phone)
        self.agents[a.id] = a
        return a

    def add_restaurant(self, name, cuisine) -> Restaurant:
        r = Restaurant(f"R{len(self.restaurants) + 1:03d}", name, cuisine)
        self.restaurants[r.restaurant_id] = r
        return r

    # ---- lookups
    def _get(self, table, key, what):
        if key not in table:
            raise NotFoundError(f"{what} {key} not found")
        return table[key]

    def search(self, query: str) -> List[Restaurant]:
        q = query.lower()
        return [r for r in self.restaurants.values()
                if q in r.name.lower() or q in r.cuisine.lower()
                or any(q in i.name.lower() for i in r.menu.values())]

    # ---- customer actions
    def add_to_cart(self, customer_id, restaurant_id, item_id, qty=1):
        cust = self._get(self.customers, customer_id, "Customer")
        rest = self._get(self.restaurants, restaurant_id, "Restaurant")
        item = self._get(rest.menu, item_id, "Item")
        cust.cart.add(rest, item, qty)

    def checkout(self, customer_id, strategy: PaymentStrategy) -> Order:
        cust = self._get(self.customers, customer_id, "Customer")
        cart = cust.cart
        if not cart.items:
            raise EmptyCartError("Your cart is empty")

        lines = [OrderLine(cart.restaurant.menu[i].name, cart.restaurant.menu[i].price, q)
                 for i, q in cart.items.items()]
        order_id = f"O{len(self.orders) + 1:04d}"
        subtotal = sum(l.total for l in lines)
        total = subtotal + (0 if subtotal >= FREE_DELIVERY_ABOVE else DELIVERY_FEE)

        payment = Payment(total, strategy)
        if not strategy.pay(total):
            payment.mark_failed()
            raise PaymentFailed(f"{strategy.name} payment failed; cart kept")
        if strategy.pay_upfront:
            payment.mark_paid()

        order = Order(order_id, cust, cart.restaurant, lines, payment)
        self.orders[order_id] = order
        cust.orders.append(order)
        cart.clear()
        return order

    def cancel_order(self, order_id):
        self._get(self.orders, order_id, "Order").change_status(OrderStatus.CANCELLED)

    # ---- restaurant / delivery actions
    def update_status(self, order_id, new_status: OrderStatus):
        order = self._get(self.orders, order_id, "Order")
        if new_status == OrderStatus.OUT_FOR_DELIVERY:
            agent = next((a for a in self.agents.values() if a.available), None)
            if agent is None:
                raise NoAgentAvailable("No delivery agent is free right now")
            order.change_status(new_status)
            agent.available = False
            order.agent = agent
            order.customer.update(f"Order {order.order_id}: {agent.name} is bringing your food")
            return order
        order.change_status(new_status)
        if new_status == OrderStatus.DELIVERED and order.agent:
            order.agent.available = True
        return order
