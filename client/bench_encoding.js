// Експеримент 1: розмір і час кодування JSON та Protobuf (Node.js) на 10 000 замовлень.
const fs = require('fs');
const path = require('path');
const pb = require('./gen/v1/shop_pb.js');

const RUNS = 5;
const data = JSON.parse(fs.readFileSync(path.join(__dirname, '..', 'data', 'orders.json'), 'utf8'));
const dicts = data.map(({ promo_code, ...rest }) => rest);

function toPb(d) {
  const o = new pb.Order();
  o.setId(d.id);
  o.setCustomerId(d.customer_id);
  o.setCreatedAtMs(d.created_at_ms);
  o.setStatus(pb.OrderStatus[d.status]);
  const a = new pb.Address();
  a.setCountry(d.shipping_address.country);
  a.setCity(d.shipping_address.city);
  a.setStreet(d.shipping_address.street);
  a.setPostalCode(d.shipping_address.postal_code);
  o.setShippingAddress(a);
  for (const it of d.items) {
    const item = new pb.OrderItem();
    item.setProductId(it.product_id);
    item.setQuantity(it.quantity);
    item.setUnitPriceCents(it.unit_price_cents);
    o.addItems(item);
  }
  if (d.comment !== undefined) o.setComment(d.comment);
  return o;
}

const msgs = dicts.map(toPb);
const jsonEnc = () => dicts.map((d) => Buffer.from(JSON.stringify(d)));
const pbEnc = () => msgs.map((m) => m.serializeBinary());
const jsonBytes = jsonEnc();
const pbBytes = pbEnc();
const jsonDec = () => jsonBytes.map((b) => JSON.parse(b.toString()));
const pbDec = () => pbBytes.map((b) => pb.Order.deserializeBinary(b));

const median = (xs) => [...xs].sort((a, b) => a - b)[Math.floor(xs.length / 2)];
const out = {};
for (const [name, fn] of [['json_encode', jsonEnc], ['json_decode', jsonDec], ['pb_encode', pbEnc], ['pb_decode', pbDec]]) {
  fn();
  const times = [];
  for (let i = 0; i < RUNS; i++) {
    const t0 = process.hrtime.bigint();
    fn();
    times.push(Number(process.hrtime.bigint() - t0) / 1e6);
  }
  out[name] = +median(times).toFixed(2);
  console.log(`${name.padEnd(12)} runs(ms)=${times.map((t) => t.toFixed(1)).join(',')} median=${out[name]}`);
}
const js = jsonBytes.reduce((s, b) => s + b.length, 0);
const pbs = pbBytes.reduce((s, b) => s + b.length, 0);
console.log(`size json=${js} protobuf=${pbs} ratio=${(js / pbs).toFixed(2)}`);
console.log(JSON.stringify({ json_bytes: js, pb_bytes: pbs, ...out }));
