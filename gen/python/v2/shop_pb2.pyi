from google.protobuf.internal import containers as _containers
from google.protobuf.internal import enum_type_wrapper as _enum_type_wrapper
from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from collections.abc import Iterable as _Iterable, Mapping as _Mapping
from typing import ClassVar as _ClassVar, Optional as _Optional, Union as _Union

DESCRIPTOR: _descriptor.FileDescriptor

class OrderStatus(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
    __slots__ = ()
    STATUS_UNSPECIFIED: _ClassVar[OrderStatus]
    PENDING: _ClassVar[OrderStatus]
    CONFIRMED: _ClassVar[OrderStatus]
    REJECTED: _ClassVar[OrderStatus]
STATUS_UNSPECIFIED: OrderStatus
PENDING: OrderStatus
CONFIRMED: OrderStatus
REJECTED: OrderStatus

class Address(_message.Message):
    __slots__ = ("country", "city", "street", "postal_code")
    COUNTRY_FIELD_NUMBER: _ClassVar[int]
    CITY_FIELD_NUMBER: _ClassVar[int]
    STREET_FIELD_NUMBER: _ClassVar[int]
    POSTAL_CODE_FIELD_NUMBER: _ClassVar[int]
    country: str
    city: str
    street: str
    postal_code: str
    def __init__(self, country: _Optional[str] = ..., city: _Optional[str] = ..., street: _Optional[str] = ..., postal_code: _Optional[str] = ...) -> None: ...

class OrderItem(_message.Message):
    __slots__ = ("product_id", "quantity", "unit_price_cents")
    PRODUCT_ID_FIELD_NUMBER: _ClassVar[int]
    QUANTITY_FIELD_NUMBER: _ClassVar[int]
    UNIT_PRICE_CENTS_FIELD_NUMBER: _ClassVar[int]
    product_id: str
    quantity: int
    unit_price_cents: int
    def __init__(self, product_id: _Optional[str] = ..., quantity: _Optional[int] = ..., unit_price_cents: _Optional[int] = ...) -> None: ...

class Order(_message.Message):
    __slots__ = ("id", "customer_id", "created_at_ms", "status", "shipping_address", "items", "promo_code")
    ID_FIELD_NUMBER: _ClassVar[int]
    CUSTOMER_ID_FIELD_NUMBER: _ClassVar[int]
    CREATED_AT_MS_FIELD_NUMBER: _ClassVar[int]
    STATUS_FIELD_NUMBER: _ClassVar[int]
    SHIPPING_ADDRESS_FIELD_NUMBER: _ClassVar[int]
    ITEMS_FIELD_NUMBER: _ClassVar[int]
    PROMO_CODE_FIELD_NUMBER: _ClassVar[int]
    id: str
    customer_id: str
    created_at_ms: int
    status: OrderStatus
    shipping_address: Address
    items: _containers.RepeatedCompositeFieldContainer[OrderItem]
    promo_code: str
    def __init__(self, id: _Optional[str] = ..., customer_id: _Optional[str] = ..., created_at_ms: _Optional[int] = ..., status: _Optional[_Union[OrderStatus, str]] = ..., shipping_address: _Optional[_Union[Address, _Mapping]] = ..., items: _Optional[_Iterable[_Union[OrderItem, _Mapping]]] = ..., promo_code: _Optional[str] = ...) -> None: ...

class CreateOrderRequest(_message.Message):
    __slots__ = ("request_id", "order")
    REQUEST_ID_FIELD_NUMBER: _ClassVar[int]
    ORDER_FIELD_NUMBER: _ClassVar[int]
    request_id: str
    order: Order
    def __init__(self, request_id: _Optional[str] = ..., order: _Optional[_Union[Order, _Mapping]] = ...) -> None: ...

class GetOrderRequest(_message.Message):
    __slots__ = ("id",)
    ID_FIELD_NUMBER: _ClassVar[int]
    id: str
    def __init__(self, id: _Optional[str] = ...) -> None: ...

class ListOrdersRequest(_message.Message):
    __slots__ = ("customer_id",)
    CUSTOMER_ID_FIELD_NUMBER: _ClassVar[int]
    customer_id: str
    def __init__(self, customer_id: _Optional[str] = ...) -> None: ...

class ListOrdersResponse(_message.Message):
    __slots__ = ("orders",)
    ORDERS_FIELD_NUMBER: _ClassVar[int]
    orders: _containers.RepeatedCompositeFieldContainer[Order]
    def __init__(self, orders: _Optional[_Iterable[_Union[Order, _Mapping]]] = ...) -> None: ...

class OrderCreated(_message.Message):
    __slots__ = ("order",)
    ORDER_FIELD_NUMBER: _ClassVar[int]
    order: Order
    def __init__(self, order: _Optional[_Union[Order, _Mapping]] = ...) -> None: ...

class ReservationResult(_message.Message):
    __slots__ = ("order_id", "status", "reason", "processed_at_ms", "order")
    ORDER_ID_FIELD_NUMBER: _ClassVar[int]
    STATUS_FIELD_NUMBER: _ClassVar[int]
    REASON_FIELD_NUMBER: _ClassVar[int]
    PROCESSED_AT_MS_FIELD_NUMBER: _ClassVar[int]
    ORDER_FIELD_NUMBER: _ClassVar[int]
    order_id: str
    status: OrderStatus
    reason: str
    processed_at_ms: int
    order: Order
    def __init__(self, order_id: _Optional[str] = ..., status: _Optional[_Union[OrderStatus, str]] = ..., reason: _Optional[str] = ..., processed_at_ms: _Optional[int] = ..., order: _Optional[_Union[Order, _Mapping]] = ...) -> None: ...
