// Клієнт сервісу замовлень (Node.js, gRPC).
// Використання: node client.js --schema v1 <команда> [параметри]
//   create-all [--n 10000] [--out file]     послідовно створює замовлення з data/orders.json, міряє час
//   create-one [--index 0]                  створює одне замовлення і читає його назад (для експерименту 2)
//   get <id> | list <customer_id>
//   retry [--n 20] [--deadline 1000] [--attempts 3] [--backoff 0]   створення з таймаутом і повтором (експеримент 3)
//   wait-status [--ids file] [--timeout 120]          чекає, поки замовлення отримають фінальний стан
const fs = require('fs');
const path = require('path');
const crypto = require('crypto');
const grpc = require('@grpc/grpc-js');

function parseArgs(argv) {
  const opts = { _: [] };
  for (let i = 0; i < argv.length; i++) {
    if (argv[i].startsWith('--')) opts[argv[i].slice(2)] = argv[++i];
    else opts._.push(argv[i]);
  }
  return opts;
}

const opts = parseArgs(process.argv.slice(2));
const version = opts.schema || 'v1';
const pb = require(`./gen/${version}/shop_pb.js`);
const services = require(`./gen/${version}/shop_grpc_pb.js`);
const client = new services.OrderServiceClient(opts.addr || '127.0.0.1:50051', grpc.credentials.createInsecure());

function loadOrders() {
  return JSON.parse(fs.readFileSync(path.join(__dirname, '..', 'data', 'orders.json'), 'utf8'));
}

function orderFromDict(d) {
  const o = new pb.Order();
  o.setCustomerId(d.customer_id);
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
  // у згенерованому коді методів для полів, яких немає в цій версії схеми, просто не існує
  if (d.comment !== undefined && o.setComment) o.setComment(d.comment);
  if (d.promo_code !== undefined && o.setPromoCode) o.setPromoCode(d.promo_code);
  return o;
}

function describe(o) {
  const parts = [`id=${o.getId()}`, `status=${o.getStatus()}`, `items=${o.getItemsList().length}`];
  if (o.getItemsList().length) parts.push(`item0.qty=${o.getItemsList()[0].getQuantity()}`);
  if (o.hasComment) parts.push(o.hasComment() ? `comment='${o.getComment()}'` : 'comment=<не задано>');
  if (o.getPromoCode) parts.push(`promo_code='${o.getPromoCode()}'`);
  return parts.join(' ');
}

function call(method, req, deadlineMs) {
  return new Promise((resolve, reject) => {
    const options = deadlineMs ? { deadline: Date.now() + deadlineMs } : {};
    client[method](req, new grpc.Metadata(), options, (err, res) => (err ? reject(err) : resolve(res)));
  });
}

function makeCreateRequest(d, requestId) {
  const req = new pb.CreateOrderRequest();
  req.setRequestId(requestId || crypto.randomUUID());
  req.setOrder(orderFromDict(d));
  return req;
}

function percentile(sorted, p) {
  return sorted[Math.min(sorted.length - 1, Math.ceil((p / 100) * sorted.length) - 1)];
}

async function createAll() {
  const orders = loadOrders().slice(0, Number(opts.n || 10000));
  const lat = [];
  const ids = [];
  for (const d of orders) {
    const req = makeCreateRequest(d);
    const t0 = process.hrtime.bigint();
    const res = await call('createOrder', req);
    lat.push(Number(process.hrtime.bigint() - t0) / 1e6);
    ids.push(res.getId());
  }
  if (opts.ids) fs.writeFileSync(opts.ids, ids.join('\n') + '\n');
  const sorted = [...lat].sort((a, b) => a - b);
  const total = lat.reduce((a, b) => a + b, 0);
  const result = {
    n: lat.length,
    p50: percentile(sorted, 50), p95: percentile(sorted, 95), p99: percentile(sorted, 99),
    max: sorted[sorted.length - 1], total_ms: total,
  };
  console.log(JSON.stringify(result));
}

async function createOne() {
  const d = loadOrders()[Number(opts.index || 0)];
  const created = await call('createOrder', makeCreateRequest(d));
  console.log(`CreateOrder відповідь: ${describe(created)}`);
  const req = new pb.GetOrderRequest();
  req.setId(created.getId());
  const got = await call('getOrder', req);
  console.log(`GetOrder відповідь:    ${describe(got)}`);
}

async function retry() {
  // кожне логічне замовлення має один request_id на всі спроби
  const orders = loadOrders().slice(0, Number(opts.n || 20));
  const deadline = Number(opts.deadline || 1000);
  const attempts = Number(opts.attempts || 3);
  const backoff = Number(opts.backoff || 0);
  const stats = { logical: orders.length, ok: 0, failed: 0, attempts: 0, errors: {} };
  for (const d of orders) {
    const requestId = crypto.randomUUID();
    let done = false;
    for (let a = 0; a < attempts && !done; a++) {
      if (a > 0 && backoff) await new Promise((r) => setTimeout(r, backoff));
      stats.attempts++;
      // таймаут подвоюється з кожною спробою
      const dl = deadline * 2 ** a;
      try {
        await call('createOrder', makeCreateRequest(d, requestId), dl);
        done = true;
      } catch (e) {
        const key = grpc.status[e.code];
        stats.errors[key] = (stats.errors[key] || 0) + 1;
        stats.example = stats.example || {};
        stats.example[key] = stats.example[key] || e.details.split(',')[0];
      }
    }
    if (done) stats.ok++; else stats.failed++;
  }
  console.log(JSON.stringify(stats, null, 1));
}

async function waitStatus() {
  const ids = fs.readFileSync(opts.ids, 'utf8').trim().split('\n');
  const until = Date.now() + 1000 * Number(opts.timeout || 120);
  for (;;) {
    const counts = {};
    for (const id of ids) {
      const req = new pb.GetOrderRequest();
      req.setId(id);
      const o = await call('getOrder', req);
      const name = Object.keys(pb.OrderStatus).find((k) => pb.OrderStatus[k] === o.getStatus());
      counts[name] = (counts[name] || 0) + 1;
    }
    if (!counts.PENDING || Date.now() > until) {
      console.log(JSON.stringify(counts));
      return;
    }
    await new Promise((r) => setTimeout(r, 1000));
  }
}

async function main() {
  const cmd = opts._[0];
  if (cmd === 'create-all') return createAll();
  if (cmd === 'create-one') return createOne();
  if (cmd === 'retry') return retry();
  if (cmd === 'wait-status') return waitStatus();
  if (cmd === 'get') {
    const req = new pb.GetOrderRequest();
    req.setId(opts._[1]);
    return console.log(describe(await call('getOrder', req)));
  }
  if (cmd === 'list') {
    const req = new pb.ListOrdersRequest();
    req.setCustomerId(opts._[1]);
    const res = await call('listCustomerOrders', req);
    for (const o of res.getOrdersList()) console.log(describe(o));
    return;
  }
  throw new Error(`невідома команда ${cmd}`);
}

main().then(() => client.close()).catch((e) => {
  console.error(`помилка: code=${e.code} (${grpc.status[e.code]}) ${e.details || e.message}`);
  client.close();
  process.exit(1);
});
