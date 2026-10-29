// GENERATED CODE -- DO NOT EDIT!

// Original file comments:
// Схема v2: додано promo_code, видалено comment
'use strict';
var grpc = require('@grpc/grpc-js');
var shop_pb = require('./shop_pb.js');

function serialize_shop_CreateOrderRequest(arg) {
  if (!(arg instanceof shop_pb.CreateOrderRequest)) {
    throw new Error('Expected argument of type shop.CreateOrderRequest');
  }
  return Buffer.from(arg.serializeBinary());
}

function deserialize_shop_CreateOrderRequest(buffer_arg) {
  return shop_pb.CreateOrderRequest.deserializeBinary(new Uint8Array(buffer_arg));
}

function serialize_shop_GetOrderRequest(arg) {
  if (!(arg instanceof shop_pb.GetOrderRequest)) {
    throw new Error('Expected argument of type shop.GetOrderRequest');
  }
  return Buffer.from(arg.serializeBinary());
}

function deserialize_shop_GetOrderRequest(buffer_arg) {
  return shop_pb.GetOrderRequest.deserializeBinary(new Uint8Array(buffer_arg));
}

function serialize_shop_ListOrdersRequest(arg) {
  if (!(arg instanceof shop_pb.ListOrdersRequest)) {
    throw new Error('Expected argument of type shop.ListOrdersRequest');
  }
  return Buffer.from(arg.serializeBinary());
}

function deserialize_shop_ListOrdersRequest(buffer_arg) {
  return shop_pb.ListOrdersRequest.deserializeBinary(new Uint8Array(buffer_arg));
}

function serialize_shop_ListOrdersResponse(arg) {
  if (!(arg instanceof shop_pb.ListOrdersResponse)) {
    throw new Error('Expected argument of type shop.ListOrdersResponse');
  }
  return Buffer.from(arg.serializeBinary());
}

function deserialize_shop_ListOrdersResponse(buffer_arg) {
  return shop_pb.ListOrdersResponse.deserializeBinary(new Uint8Array(buffer_arg));
}

function serialize_shop_Order(arg) {
  if (!(arg instanceof shop_pb.Order)) {
    throw new Error('Expected argument of type shop.Order');
  }
  return Buffer.from(arg.serializeBinary());
}

function deserialize_shop_Order(buffer_arg) {
  return shop_pb.Order.deserializeBinary(new Uint8Array(buffer_arg));
}


var OrderServiceService = exports.OrderServiceService = {
  createOrder: {
    path: '/shop.OrderService/CreateOrder',
    requestStream: false,
    responseStream: false,
    requestType: shop_pb.CreateOrderRequest,
    responseType: shop_pb.Order,
    requestSerialize: serialize_shop_CreateOrderRequest,
    requestDeserialize: deserialize_shop_CreateOrderRequest,
    responseSerialize: serialize_shop_Order,
    responseDeserialize: deserialize_shop_Order,
  },
  getOrder: {
    path: '/shop.OrderService/GetOrder',
    requestStream: false,
    responseStream: false,
    requestType: shop_pb.GetOrderRequest,
    responseType: shop_pb.Order,
    requestSerialize: serialize_shop_GetOrderRequest,
    requestDeserialize: deserialize_shop_GetOrderRequest,
    responseSerialize: serialize_shop_Order,
    responseDeserialize: deserialize_shop_Order,
  },
  listCustomerOrders: {
    path: '/shop.OrderService/ListCustomerOrders',
    requestStream: false,
    responseStream: false,
    requestType: shop_pb.ListOrdersRequest,
    responseType: shop_pb.ListOrdersResponse,
    requestSerialize: serialize_shop_ListOrdersRequest,
    requestDeserialize: deserialize_shop_ListOrdersRequest,
    responseSerialize: serialize_shop_ListOrdersResponse,
    responseDeserialize: deserialize_shop_ListOrdersResponse,
  },
};

exports.OrderServiceClient = grpc.makeGenericClientConstructor(OrderServiceService, 'OrderService');
