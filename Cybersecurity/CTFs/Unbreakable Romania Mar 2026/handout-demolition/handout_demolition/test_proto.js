const raw = '{"__proto__": {"engine": "go"}}';
const parsed = JSON.parse(raw);
console.log("Keys:", Object.keys(parsed));
console.log("Entries:", Object.entries(parsed));
console.log("__proto__ property:", parsed.__proto__);

const flat = {};
function collectLeafPaths(node, prefix, out) {
  if (Array.isArray(node)) {
    out[prefix] = node.slice();
    return;
  }
  if (!node || typeof node !== "object") {
    out[prefix] = node;
    return;
  }
  for (const [key, value] of Object.entries(node)) {
    const path = prefix ? `${prefix}.${key}` : key;
    collectLeafPaths(value, path, out);
  }
}

collectLeafPaths(parsed, "", flat);
console.log("Flat:", flat);
