// Експеримент 2: Node.js з v1 декодує повідомлення v2 і кодує знову. node reencode.js <in.bin> <out.bin>
const fs = require('fs');
const pb = require('./gen/v1/shop_pb.js');

const raw = fs.readFileSync(process.argv[2]);
const o = pb.Order.deserializeBinary(raw);
o.setStatus(pb.OrderStatus.CONFIRMED);
const out = Buffer.from(o.serializeBinary());
fs.writeFileSync(process.argv[3], out);
console.log(`node v1: прочитано ${raw.length} B, hasComment=${o.hasComment()}, записано ${out.length} B`);
