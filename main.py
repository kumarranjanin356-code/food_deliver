"""Console demo of the Food Delivery System."""
from app import FoodDeliveryApp
from models import OrderStatus
from payment import UPIPayment

app = FoodDeliveryApp.get_instance()

dhaba = app.add_restaurant("Punjabi Dhaba", "North Indian")
paneer = dhaba.add_item("Paneer Tikka", 220)
naan = dhaba.add_item("Butter Naan", 40)
ravi = app.register_customer("Ravi", "9999999999", "NIT Campus")
app.register_agent("Sunil", "8888888888")

print("Search 'paneer':", [r.name for r in app.search("paneer")])
app.add_to_cart(ravi.id, dhaba.restaurant_id, paneer.item_id, 2)
app.add_to_cart(ravi.id, dhaba.restaurant_id, naan.item_id, 4)

order = app.checkout(ravi.id, UPIPayment("ravi@upi"))
print(f"{order.order_id}: subtotal Rs {order.subtotal}, delivery Rs {order.delivery_fee}, total Rs {order.total}")

for status in (OrderStatus.ACCEPTED, OrderStatus.PREPARING,
               OrderStatus.OUT_FOR_DELIVERY, OrderStatus.DELIVERED):
    app.update_status(order.order_id, status)

print("\nRavi's notifications:")
for n in ravi.notifications:
    print(" -", n)
