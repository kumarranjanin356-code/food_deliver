from abc import ABC, abstractmethod
from enum import Enum
from typing import Dict, List, Optional

from exceptions import *
from payment import Payment

DELIVERY_FEE = 30
FREE_DELIVERY_ABOVE = 500


class OrderStatus(Enum):
    PLACED = "Placed"
    ACCEPTED = "Accepted"
    PREPARING = "Preparing"
    OUT_FOR_DELIVERY = "Out for delivery"
    DELIVERED = "Delivered"
    CANCELLED = "Cancelled"


TRANSITIONS = {
    OrderStatus.PLACED: {OrderStatus.ACCEPTED, OrderStatus.CANCELLED},
    OrderStatus.ACCEPTED: {OrderStatus.PREPARING, OrderStatus.CANCELLED},
    OrderStatus.PREPARING: {OrderStatus.OUT_FOR_DELIVERY},
    OrderStatus.OUT_FOR_DELIVERY: {OrderStatus.DELIVERED},
    OrderStatus.DELIVERED: set(),
    OrderStatus.CANCELLED: set(),
}


# ------------------------------------------------------------ users
class User(ABC):
    def __init__(self, user_id: str, name: str, phone: str):
        self._id, self._name, self._phone = user_id, name, phone

    @property
    def id(self): return self._id
    @property
    def name(self): return self._name

    @property
    @abstractmethod
    def role(self) -> str: ...


class Customer(User):
    """Also the Observer: gets notified when an order's status changes."""
    def __init__(self, user_id, name, phone, address):
        super().__init__(user_id, name, phone)
        self.address = address
        self.cart = Cart()
        self.orders: List["Order"] = []
        self.notifications: List[str] = []

    @property
    def role(self): return "Customer"

    def update(self, message: str):
        self.notifications.append(message)


class DeliveryAgent(User):
    def __init__(self, user_id, name, phone):
        super().__init__(user_id, name, phone)
        self.available = True

    @property
    def role(self): return "Delivery Agent"


# ------------------------------------------------------------ restaurant
class MenuItem:
    def __init__(self, item_id: str, name: str, price: int):
        self.item_id, self.name, self.price = item_id, name, price
        self.available = True


class Restaurant:
    def __init__(self, restaurant_id: str, name: str, cuisine: str):
        self.restaurant_id, self.name, self.cuisine = restaurant_id, name, cuisine
        self.menu: Dict[str, MenuItem] = {}

    def add_item(self, name: str, price: int) -> MenuItem:
        item = MenuItem(f"{self.restaurant_id}-I{len(self.menu) + 1}", name, price)
        self.menu[item.item_id] = item
        return item


# ------------------------------------------------------------ cart
class Cart:
    def __init__(self):
        self.restaurant: Optional[Restaurant] = None
        self.items: Dict[str, int] = {}        # item_id -> quantity

    def add(self, restaurant: Restaurant, item: MenuItem, qty: int = 1):
        if not item.available:
            raise ItemUnavailable(f"{item.name} is not available")
        if self.items and self.restaurant is not restaurant:
            raise DifferentRestaurantError("Cart already has items from another restaurant")
        self.restaurant = restaurant
        self.items[item.item_id] = self.items.get(item.item_id, 0) + qty

    def remove(self, item_id: str):
        self.items.pop(item_id, None)
        if not self.items:
            self.restaurant = None

    def subtotal(self) -> int:
        return sum(self.restaurant.menu[i].price * q for i, q in self.items.items())

    def clear(self):
        self.restaurant, self.items = None, {}


# ------------------------------------------------------------ order
class OrderLine:
    """Snapshot of name and price so later menu changes don't alter old orders."""
    def __init__(self, name, price, qty):
        self.name, self.price, self.qty = name, price, qty

    @property
    def total(self): return self.price * self.qty


class Order:
    """Subject in the Observer pattern; status changes follow TRANSITIONS."""
    def __init__(self, order_id, customer: Customer, restaurant: Restaurant,
                 lines: List[OrderLine], payment: Payment):
        self.order_id = order_id
        self.customer = customer
        self.restaurant = restaurant
        self.lines = lines
        self.payment = payment
        self.subtotal = sum(l.total for l in lines)
        self.delivery_fee = 0 if self.subtotal >= FREE_DELIVERY_ABOVE else DELIVERY_FEE
        self.total = self.subtotal + self.delivery_fee
        self.status = OrderStatus.PLACED
        self.agent: Optional[DeliveryAgent] = None
        self._observers = [customer]
        self._notify("Order placed")

    def _notify(self, text):
        for o in self._observers:
            o.update(f"Order {self.order_id}: {text}")

    def change_status(self, new: OrderStatus):
        if new not in TRANSITIONS[self.status]:
            raise InvalidStatusChange(f"Cannot go from {self.status.value} to {new.value}")
        self.status = new
        if new == OrderStatus.CANCELLED:
            self.payment.refund()
        if new == OrderStatus.DELIVERED and self.payment.method == "COD":
            self.payment.mark_paid()
        self._notify(new.value)
