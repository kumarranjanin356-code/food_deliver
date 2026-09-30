import unittest

from app import FoodDeliveryApp
from exceptions import *
from models import OrderStatus
from payment import CardPayment, CashOnDelivery, UPIPayment


class FoodTests(unittest.TestCase):
    def setUp(self):
        FoodDeliveryApp.reset()
        self.app = FoodDeliveryApp.get_instance()
        self.r1 = self.app.add_restaurant("Punjabi Dhaba", "North Indian")
        self.paneer = self.r1.add_item("Paneer Tikka", 220)
        self.naan = self.r1.add_item("Butter Naan", 40)
        self.r2 = self.app.add_restaurant("Pizza Point", "Italian")
        self.pizza = self.r2.add_item("Margherita", 300)
        self.cust = self.app.register_customer("Ravi", "9999999999", "NIT Campus")
        self.agent = self.app.register_agent("Sunil", "8888888888")

    def cart(self, item, qty=1, rest=None):
        rest = rest or self.r1
        self.app.add_to_cart(self.cust.id, rest.restaurant_id, item.item_id, qty)

    def test_singleton(self):
        self.assertIs(FoodDeliveryApp.get_instance(), self.app)

    def test_search_by_dish_and_cuisine(self):
        self.assertEqual(self.app.search("paneer"), [self.r1])
        self.assertEqual(self.app.search("italian"), [self.r2])

    def test_cart_single_restaurant_rule(self):
        self.cart(self.paneer)
        with self.assertRaises(DifferentRestaurantError):
            self.cart(self.pizza, rest=self.r2)

    def test_unavailable_item(self):
        self.naan.available = False
        with self.assertRaises(ItemUnavailable):
            self.cart(self.naan)

    def test_delivery_fee_below_and_above_threshold(self):
        self.cart(self.paneer)                                  # 220 -> fee 30
        o1 = self.app.checkout(self.cust.id, UPIPayment("ravi@upi"))
        self.assertEqual(o1.total, 250)
        self.cart(self.paneer, 3)                               # 660 -> free
        o2 = self.app.checkout(self.cust.id, UPIPayment("ravi@upi"))
        self.assertEqual(o2.total, 660)

    def test_checkout_clears_cart(self):
        self.cart(self.paneer)
        self.app.checkout(self.cust.id, CashOnDelivery())
        self.assertEqual(self.cust.cart.items, {})

    def test_empty_cart(self):
        with self.assertRaises(EmptyCartError):
            self.app.checkout(self.cust.id, CashOnDelivery())

    def test_payment_failure_keeps_cart(self):
        self.cart(self.paneer)
        with self.assertRaises(PaymentFailed):
            self.app.checkout(self.cust.id, UPIPayment("bad-id"))
        self.assertTrue(self.cust.cart.items)
        with self.assertRaises(PaymentFailed):
            self.app.checkout(self.cust.id, CardPayment("1234"))

    def test_full_lifecycle_and_notifications(self):
        self.cart(self.paneer)
        o = self.app.checkout(self.cust.id, UPIPayment("ravi@upi"))
        for s in (OrderStatus.ACCEPTED, OrderStatus.PREPARING,
                  OrderStatus.OUT_FOR_DELIVERY, OrderStatus.DELIVERED):
            self.app.update_status(o.order_id, s)
        self.assertEqual(o.status, OrderStatus.DELIVERED)
        self.assertTrue(self.agent.available)
        self.assertGreaterEqual(len(self.cust.notifications), 5)

    def test_invalid_transition(self):
        self.cart(self.paneer)
        o = self.app.checkout(self.cust.id, UPIPayment("ravi@upi"))
        with self.assertRaises(InvalidStatusChange):
            self.app.update_status(o.order_id, OrderStatus.DELIVERED)

    def test_cancel_before_preparing_refunds(self):
        self.cart(self.paneer)
        o = self.app.checkout(self.cust.id, UPIPayment("ravi@upi"))
        self.app.cancel_order(o.order_id)
        self.assertEqual(o.payment.status, "REFUNDED")

    def test_cannot_cancel_once_preparing(self):
        self.cart(self.paneer)
        o = self.app.checkout(self.cust.id, UPIPayment("ravi@upi"))
        self.app.update_status(o.order_id, OrderStatus.ACCEPTED)
        self.app.update_status(o.order_id, OrderStatus.PREPARING)
        with self.assertRaises(InvalidStatusChange):
            self.app.cancel_order(o.order_id)

    def test_cod_paid_on_delivery(self):
        self.cart(self.paneer)
        o = self.app.checkout(self.cust.id, CashOnDelivery())
        self.assertEqual(o.payment.status, "PENDING")
        for s in (OrderStatus.ACCEPTED, OrderStatus.PREPARING,
                  OrderStatus.OUT_FOR_DELIVERY, OrderStatus.DELIVERED):
            self.app.update_status(o.order_id, s)
        self.assertEqual(o.payment.status, "PAID")

    def test_no_agent_available(self):
        self.agent.available = False
        self.cart(self.paneer)
        o = self.app.checkout(self.cust.id, CashOnDelivery())
        self.app.update_status(o.order_id, OrderStatus.ACCEPTED)
        self.app.update_status(o.order_id, OrderStatus.PREPARING)
        with self.assertRaises(NoAgentAvailable):
            self.app.update_status(o.order_id, OrderStatus.OUT_FOR_DELIVERY)
        self.assertEqual(o.status, OrderStatus.PREPARING)

    def test_order_keeps_price_snapshot(self):
        self.cart(self.paneer)
        o = self.app.checkout(self.cust.id, CashOnDelivery())
        self.paneer.price = 999
        self.assertEqual(o.subtotal, 220)


if __name__ == "__main__":
    unittest.main()
