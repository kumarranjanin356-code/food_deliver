# Food Delivery System (OOAD)

Run: `python3 main.py` (demo) and `python3 -m unittest -v` (15 tests). Python 3.9+, no dependencies.

## 1. Requirements
- Customer: search restaurants or dishes, fill a cart, pay, track order, cancel
- Restaurant: manage menu, accept order, prepare food
- Delivery agent: picks up and delivers order
- Rules: one restaurant per cart; delivery fee Rs 30, free for orders of Rs 500 or more;
  cancel only before preparing starts (prepaid orders are refunded); COD is paid on delivery

## 2. Use case diagram
```mermaid
flowchart LR
  C((Customer)) --> U1[Search Restaurant / Dish]
  C --> U2[Add to Cart]
  C --> U3[Place Order]
  C --> U4[Cancel Order]
  C --> U5[Track Order]
  U3 -. include .-> U6[Make Payment]
  R((Restaurant)) --> U7[Accept Order]
  R --> U8[Mark Preparing]
  D((Delivery Agent)) --> U9[Pick Up Order]
  D --> U10[Mark Delivered]
  S((System)) --> U11[Notify Customer]
```

## 3. Class diagram
```mermaid
classDiagram
  class User { <<abstract>> -id -name -phone +role() }
  class Customer { address cart +update(msg) }
  class DeliveryAgent { available }
  class Restaurant { name cuisine +addItem() }
  class MenuItem { name price available }
  class Cart { items +add() +remove() +subtotal() +clear() }
  class Order { status subtotal deliveryFee total +changeStatus() }
  class OrderLine { name price qty }
  class Payment { amount method status +refund() }
  class PaymentStrategy { <<abstract>> +pay() }
  class FoodDeliveryApp { <<singleton>> +search() +addToCart() +checkout() +updateStatus() +cancelOrder() }
  User <|-- Customer
  User <|-- DeliveryAgent
  PaymentStrategy <|-- UPIPayment
  PaymentStrategy <|-- CardPayment
  PaymentStrategy <|-- CashOnDelivery
  Restaurant "1" *-- "*" MenuItem : composition
  Order "1" *-- "1..*" OrderLine : composition
  Customer "1" *-- "1" Cart
  Customer "1" --> "*" Order
  Cart --> Restaurant
  Order --> Restaurant
  Order --> DeliveryAgent
  Order --> Payment
  Order ..> Customer : notifies (Observer)
  FoodDeliveryApp o-- Restaurant
  FoodDeliveryApp o-- Customer
```

## 4. Sequence diagram: Place Order
```mermaid
sequenceDiagram
  actor C as Customer
  participant A as FoodDeliveryApp
  participant P as PaymentStrategy
  participant O as Order
  C->>A: checkout(customerId, UPIPayment)
  A->>A: check cart not empty, compute total
  A->>P: pay(total)
  P-->>A: success
  A->>O: create Order (PLACED)
  O-->>C: notify "Order placed"
  A->>A: clear cart
  A-->>C: Order
```

## 5. State diagram: Order lifecycle
```mermaid
stateDiagram-v2
  [*] --> Placed
  Placed --> Accepted
  Placed --> Cancelled
  Accepted --> Preparing
  Accepted --> Cancelled
  Preparing --> OutForDelivery : agent assigned
  OutForDelivery --> Delivered
  Delivered --> [*]
  Cancelled --> [*]
```

## 6. OOP concepts and patterns
| Concept | Where |
|---|---|
| Abstraction | `User`, `PaymentStrategy` are abstract |
| Inheritance | `Customer`, `DeliveryAgent` extend `User` |
| Encapsulation | private `_id`, `_upi_id`, `_card_no` |
| Polymorphism | `pay()` behaves differently for UPI, Card and COD |
| Composition | `Restaurant` owns `MenuItem`s, `Order` owns `OrderLine`s |
| Singleton | `FoodDeliveryApp.get_instance()` |
| Strategy | `UPIPayment`, `CardPayment`, `CashOnDelivery` |
| Observer | `Order` notifies the `Customer` on every status change |

## 7. Files
`models.py` domain classes and order state rules, `payment.py` Strategy, `app.py` Singleton facade,
`exceptions.py`, `main.py` demo, `test_food.py` test cases.

## 8. Extension ideas
Coupon codes (another Strategy), ratings and reviews, restaurant-side accept or reject, SQLite storage, Flask UI.
