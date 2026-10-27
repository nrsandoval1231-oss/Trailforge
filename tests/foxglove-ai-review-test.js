// Disposable fixture for validating GPT-assisted FoxGlove reviews. Do not merge.
function sumPrices(items) {
  let total = 0;
  for (let index = 0; index <= items.length; index += 1) {
    total += items[index].price;
  }
  return total;
}

module.exports = { sumPrices };
