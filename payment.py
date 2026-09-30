"""Strategy pattern: interchangeable payment methods."""
from abc import ABC, abstractmethod


class PaymentStrategy(ABC):
    name = ""
    pay_upfront = True

    @abstractmethod
    def pay(self, amount: int) -> bool: ...


class UPIPayment(PaymentStrategy):
    name = "UPI"

    def __init__(self, upi_id: str):
        self._upi_id = upi_id

    def pay(self, amount):
        return "@" in self._upi_id and amount > 0


class CardPayment(PaymentStrategy):
    name = "Card"

    def __init__(self, card_no: str):
        self._card_no = card_no.replace(" ", "")

    def pay(self, amount):
        return self._card_no.isdigit() and len(self._card_no) == 16 and amount > 0


class CashOnDelivery(PaymentStrategy):
    name = "COD"
    pay_upfront = False

    def pay(self, amount):
        return True          # cash is collected at the door


class Payment:
    """Result of paying for an order."""
    def __init__(self, amount: int, strategy: PaymentStrategy):
        self.amount = amount
        self.method = strategy.name
        self.status = "PENDING"

    def mark_paid(self): self.status = "PAID"
    def mark_failed(self): self.status = "FAILED"
    def refund(self):
        if self.status == "PAID":
            self.status = "REFUNDED"
