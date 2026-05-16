import { SQL } from 'bun';

const db = new SQL('sqlite://:memory:');

await db`CREATE TABLE cart_items (
  username TEXT,
  book_id TEXT,
  is_sample INT
)`;

const tests = [
  0.1,
  1.1,
  "0.1",
  "1.1",
  true,
  "true",
  "1",
  "0",
  1n,
  1e-10
];

console.log("Testing inputs...");

for (const val of tests) {
  const ischarged = !+val;
  console.log(`Input: ${val} (type: ${typeof val}), +val: ${+val}, is_charged: ${ischarged}`);
  
  await db`DELETE FROM cart_items`;
  try {
     const entry = { username: 'test', book_id: 'b1', is_sample: val };
    // Bun's db helper might need array for bulk insert usually, but let's try single object or array
    await db`INSERT INTO cart_items ${db([entry])}`;
    
    const res = await db`SELECT is_sample FROM cart_items`;
    const stored = res[0].is_sample;
    
    console.log(`  -> Stored: ${stored} (type: ${typeof stored})`);
    console.log(`  -> Stored Truthy?: ${!!stored}`);
    console.log(`  -> Stored Ternary logic: ${stored ? 'SAMPLE' : 'REAL'}`);
    
  } catch (e) {
    console.log(`  -> Error: ${e.message}`);
  }
  console.log('---');
}
