class FoodDeliveryError(Exception): pass
class NotFoundError(FoodDeliveryError): pass
class DifferentRestaurantError(FoodDeliveryError): pass
class ItemUnavailable(FoodDeliveryError): pass
class EmptyCartError(FoodDeliveryError): pass
class PaymentFailed(FoodDeliveryError): pass
class InvalidStatusChange(FoodDeliveryError): pass
class NoAgentAvailable(FoodDeliveryError): pass
