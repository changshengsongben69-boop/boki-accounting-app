// 独立検算スクリプト。index.html の問題データを一切参照せず、
// 設問の前提条件だけから正解値を再計算する。
// 実行: node verify_calc.js
// index.html から answer を抽出して突合するのは compare 部分のみ。

const R = n => Math.round(n); // 円未満四捨五入

const expected = {};

// ---------- A 減価償却 ----------
// A-C1 取得原価3,000,000 / 残存0 / 耐用8年 / 定額法 / 年間償却費
expected['a-c01'] = (3000000 - 0) / 8;
// A-C2 取得原価2,400,000 / 残存0 / 耐用10年 / 定額法 / 11月1日取得・決算3月31日(5か月)
expected['a-c02'] = (2400000 / 10) * (5 / 12);
// A-C3 取得原価1,000,000 / 定率法 償却率0.250 / 1年目
expected['a-c03'] = 1000000 * 0.25;
// A-C4 同上 2年目
expected['a-c04'] = (1000000 - 1000000 * 0.25) * 0.25;
// A-C5 取得原価4,000,000 / 耐用8年 / 200%定率法 / 1年目
{
  const rate = (1 / 8) * 2.0;
  expected['a-c05'] = 4000000 * rate;
}
// A-C6 取得原価5,000,000 / 残存500,000 / 総見積走行距離300,000km / 当期42,000km / 生産高比例法
expected['a-c06'] = R((5000000 - 500000) * (42000 / 300000));
// A-C7 取得原価3,000,000 / 残存0 / 耐用8年 / 定額法 / 3年経過後の期末帳簿価額
expected['a-c07'] = 3000000 - (3000000 / 8) * 3;
// A-C8 取得原価800,000 / 期首減価償却累計額480,000 / 期首に250,000で売却 / 売却損の絶対値
expected['a-c08'] = Math.abs((800000 - 480000) - 250000);
// A-C9 取得原価600,000 / 累計額480,000 / 処分価値30,000で除却 / 除却損
expected['a-c09'] = (600000 - 480000) - 30000;
// A-C10 取得原価1,200,000 / 残存0 / 耐用6年 / 定額法 / 期首累計額600,000
//       期首4/1、9/30に450,000で売却(6か月) / 売却損の絶対値
{
  const yearly = 1200000 / 6;
  const thisYear = yearly * (6 / 12);
  const bv = 1200000 - 600000 - thisYear;
  expected['a-c10'] = Math.abs(bv - 450000);
}

// ---------- B 棚卸資産 ----------
// 資料: 期首 100個@200 / 5日仕入 300個@220 / 10日売上 250個
//       20日仕入 200個@250 / 25日売上 150個
// B-C1 先入先出法による月末商品棚卸高
{
  // 払出合計400個 = 期首100 + 5日300。残200個は20日仕入分。
  const lots = [[100, 200], [300, 220], [200, 250]];
  let out = 400;
  const rest = [];
  for (const [q, p] of lots) {
    const take = Math.min(q, out);
    out -= take;
    if (q - take > 0) rest.push([q - take, p]);
  }
  expected['b-c01'] = rest.reduce((s, [q, p]) => s + q * p, 0);
}
// B-C2 移動平均法による月末商品棚卸高
{
  let qty = 100, amt = 100 * 200;
  // 5日仕入
  qty += 300; amt += 300 * 220;
  // 10日売上250個
  let avg = amt / qty; amt -= 250 * avg; qty -= 250;
  // 20日仕入
  qty += 200; amt += 200 * 250;
  // 25日売上150個
  avg = amt / qty; amt -= 150 * avg; qty -= 150;
  expected['b-c02'] = R(amt);
}
// B-C3 帳簿棚卸数量200個 / 実地棚卸数量190個 / 原価@250 / 棚卸減耗損
expected['b-c03'] = (200 - 190) * 250;
// B-C4 実地190個 / 原価@250 / 正味売却価額@230 / 商品評価損
expected['b-c04'] = (250 - 230) * 190;

// ---------- C 引当金 ----------
// C-C1 売掛金期末4,000,000 / 貸倒実績率2% / 貸倒引当金残高30,000 / 差額補充法の繰入額
expected['c-c01'] = 4000000 * 0.02 - 30000;

// ---------- F 配賦計算 (2026年度過去問の数値) ----------
const X = { dm: 2000000, dl: 600000, de: 300000, mh: 5000, qty: 1000, price: 800 };
const Y = { dm: 1000000, dl: 1800000, de: 450000, mh: 7500, qty: 1000, price: 3200 };
const OH = 6000000;
const alloc = (bx, by) => [R(OH * bx / (bx + by)), R(OH * by / (bx + by))];

// F-C1 機械加工時間を配賦基準としたときの配賦率(円/時間)
expected['f-c01'] = OH / (X.mh + Y.mh);
// F-C2 直接材料費基準・製品Xへの配賦額
expected['f-c02'] = alloc(X.dm, Y.dm)[0];
// F-C3 直接労務費基準・製品X
expected['f-c03'] = alloc(X.dl, Y.dl)[0];
// F-C4 直接費基準(材料+労務+経費)・製品X
expected['f-c04'] = alloc(X.dm + X.dl + X.de, Y.dm + Y.dl + Y.de)[0];
// F-C5 素価基準(材料+労務)・製品X
expected['f-c05'] = alloc(X.dm + X.dl, Y.dm + Y.dl)[0];
// F-C6 製造数量基準・製品X
expected['f-c06'] = alloc(X.qty, Y.qty)[0];
// F-C7 機械加工時間基準・製品X
expected['f-c07'] = alloc(X.mh, Y.mh)[0];
// F-C8 販売価格基準・製品X
expected['f-c08'] = alloc(X.price * X.qty, Y.price * Y.qty)[0];

// ---------- G 差異分析 ----------
// 標準: 材料 @400×3kg / 労務 @1,000×2h / 間接費 @1,500×2h (変動600・固定900)
// 基準操業度2,000h / 固定製造間接費予算1,800,000
// 当月実際生産量900個(仕掛品なし)
// 実際: 材料2,800kg@410 / 労務1,850h@1,020 / 間接費実際2,760,000・実際時間1,850h
{
  const stdQty = 900 * 3, stdHr = 900 * 2;
  // G-C1 材料価格差異(絶対値)
  expected['g-c01'] = Math.abs((400 - 410) * 2800);
  // G-C2 材料数量差異(絶対値)
  expected['g-c02'] = Math.abs((stdQty - 2800) * 400);
  // G-C3 賃率差異(絶対値)
  expected['g-c03'] = Math.abs((1000 - 1020) * 1850);
  // G-C4 作業時間差異(絶対値)
  expected['g-c04'] = Math.abs((stdHr - 1850) * 1000);
  // G-C5 製造間接費 予算差異(絶対値) 変動予算
  const allowance = 600 * 1850 + 1800000;
  expected['g-c05'] = Math.abs(allowance - 2760000);

  // 内部整合チェック: 3分法の合計 = 総差異
  const budgetVar = allowance - 2760000;            // +150,000 有利
  const capacityVar = (1850 - 2000) * 900;          // -135,000 不利
  const efficiencyVar = (stdHr - 1850) * 1500;      // -75,000 不利
  const total = stdHr * 1500 - 2760000;
  if (budgetVar + capacityVar + efficiencyVar !== total) {
    console.error('FATAL: 製造間接費差異の3分法が総差異と一致しない');
    process.exit(1);
  }
  // 内部整合チェック: 配賦額合計 = 実際発生額 (F各基準)
  for (const [bx, by] of [[X.dm, Y.dm], [X.dl, Y.dl],
                          [X.dm + X.dl + X.de, Y.dm + Y.dl + Y.de],
                          [X.dm + X.dl, Y.dm + Y.dl], [X.qty, Y.qty],
                          [X.mh, Y.mh], [X.price * X.qty, Y.price * Y.qty]]) {
    const [a, b] = alloc(bx, by);
    if (a + b !== OH) { console.error('FATAL: 配賦額合計 != 6,000,000', bx, by, a + b); process.exit(1); }
  }
}

// ---------- 突合 ----------
const fs = require('fs');
const path = require('path');
const htmlPath = path.join(__dirname, 'index.html');

if (!fs.existsSync(htmlPath)) {
  console.log('index.html が未作成。expected のみ出力する。');
  for (const k of Object.keys(expected).sort()) console.log(k, expected[k]);
  process.exit(0);
}

const html = fs.readFileSync(htmlPath, 'utf8');
// id と answer を素朴に抽出する(問題データの構造には依存するが、値の計算には依存しない)
const found = {};
const re = /id:\s*"([a-g]-c\d+)"[\s\S]*?answer:\s*(-?[\d.]+)/g;
let m;
while ((m = re.exec(html)) !== null) found[m[1]] = Number(m[2]);

let ng = 0, n = 0;
const keys = new Set([...Object.keys(expected), ...Object.keys(found)]);
for (const k of [...keys].sort()) {
  n++;
  const e = expected[k], f = found[k];
  const ok = e !== undefined && f !== undefined && Math.abs(e - f) < 1e-9;
  if (!ok) ng++;
  console.log(`${ok ? 'OK  ' : 'NG  '} ${k}  expected=${e}  inFile=${f}`);
}
console.log(`--- ${n} 件中 ${n - ng} 件一致 / ${ng} 件不一致 ---`);
process.exit(ng === 0 ? 0 : 1);
