// REVIEW.md を index.html の問題データから生成する。手で編集しないこと。
const fs = require('fs');
const html = fs.readFileSync(__dirname + '/index.html', 'utf8');
const js = html.match(/<script>([\s\S]*)<\/script>/)[1];
const cut = js.indexOf('/* ---------- セクション定義');
const mod = js.slice(0, cut) + '\nmodule.exports={DATA,TABLES};';
fs.writeFileSync('/tmp/_rev_data.js', mod);
const { DATA } = require('/tmp/_rev_data.js');

const SEC = { A:'減価償却', B:'棚卸資産', C:'引当金・経過勘定', D:'有価証券・一般原則',
              E:'原価計算の基礎概念', F:'費目別・配賦計算', G:'予定配賦・差異分析' };

let o = [];
o.push('# 会計内容レビュー票');
o.push('');
o.push('`index.html` の記述問題33問について、採点要素を出典条番号とともに一覧にしたもの。');
o.push('**このファイルは `node gen_review.js` で自動生成する。手で編集しない。**');
o.push('');
o.push('## なぜこの票が要るのか');
o.push('');
o.push('制作時のセッションは外向き通信が遮断されており、企業会計原則・同注解、企業会計基準第9号・');
o.push('第10号、連続意見書、原価計算基準のいずれの公式ページにも到達できなかった。');
o.push('そのため**採点要素は条文を参照せずに書かれている。会計の正確性は未検証である。**');
o.push('');
o.push('会計法規集を手元に置き、各問の出典条番号を引いて、下記の要素を1件ずつ確認すること。');
o.push('とくに次の4点は誤りが混入しやすい。');
o.push('');
o.push('- 棚卸資産の評価方法（後入先出法は現行では選択不可）→ B-2, B-3');
o.push('- 減価償却の各方法の適用対象資産 → A-2, A-3');
o.push('- 引当金の計上要件 → C-1, C-3');
o.push('- 予定配賦率の計算基礎となる操業度の定義 → G-1');
o.push('');
o.push('確認できた問題は、行頭の `[ ]` を `[x]` にする。');
o.push('');
o.push('## 優先確認リスト（作成者の確信度が低い順）');
o.push('');
o.push('33問すべてが未検証だが、危険度は一様ではない。**次の7件を先に潰すこと。**');
o.push('残りは、標準的な教科書の記述と条文の内容がほぼ一致している箇所である。');
o.push('');
o.push('| 優先 | 該当 | 疑う理由 |');
o.push('|---|---|---|');
o.push('| 1 | G-1「期待実際操業度または正常操業度」 | 原価計算基準 三三 のどの項番に操業度の定義があるかを特定できていない。そのため出典の細目を空けてある。文言と項番の両方を確認すること |');
o.push('| 2 | B-1 加点「仕入割引は営業外収益」 | 収益認識会計基準（企業会計基準第29号）の適用で、日商簿記では売上割引・仕入割引の扱いが変わっている。企業会計原則ベースの入試で従来どおりの解答でよいか判断が要る |');
o.push('| 3 | C-2「評価性引当金／負債性引当金」 | この2分類は注解18の条文そのものの区分ではなく、通説的な整理である可能性が高い。条文の文言と突き合わせること |');
o.push('| 4 | D-3「網羅性・立証性・秩序性」 | 注解1の文言ではなく、通説的な整理。入試の採点で使える表現かを確認 |');
o.push('| 5 | B-4「棚卸減耗損は原価性の有無で表示区分が変わる」 | 連続意見書第四・注解にまたがる整理。出典の帰属が正しいか確認 |');
o.push('| 6 | A-8 加点「備忘価額1円」 | 法人税法由来の実務慣行。会計上の残存価額と混同しないよう注意欄を付けてあるが、記述として適切かは要判断 |');
o.push('| 7 | E-5 加点「費目別計算は第一次の計算段階」 | 当初は「財務会計機構と有機的に結びつく」（これは基準二の内容）を基準九に帰属させる誤りがあり、修正済み。修正後の文言が基準九と合っているか確認 |');
o.push('');

for (const s of Object.keys(SEC)) {
  const list = DATA.filter(q => q.section === s && q.type === 'write');
  if (!list.length) continue;
  o.push(`## ${s} ${SEC[s]}（記述${list.length}問）`);
  o.push('');
  list.forEach((q, i) => {
    o.push(`### ${s}-${i + 1}　${q.q.replace(/\n/g, ' ')}`);
    o.push('');
    o.push(`- 出典: **${q.source.doc}　${q.source.article}**（${q.source.issuer}）`);
    o.push(`- リンク: ${q.source.url ? q.source.url : '**なし（未解決。会計法規集で確認）**'}`);
    o.push('');
    q.elements.forEach(e => {
      o.push(`- [ ] ${e.core ? '**必須**' : '加点'}　${e.text}`);
    });
    if (q.caution) { o.push(''); o.push(`> 注意欄の記載: ${q.caution}`); }
    o.push('');
  });
}

o.push('## 計算問題（28問）');
o.push('');
o.push('正解値は `verify_calc.js`（問題データを参照しない独立実装）で28件すべて突合済み。');
o.push('算術は検証されているが、**設問の会計的な前提（適用してよい処理かどうか）は未検証**である。');
o.push('');
DATA.filter(q => q.type === 'calc').forEach(q => {
  o.push(`- [ ] \`${q.id}\`　正解 ${q.answer.toLocaleString('en-US')}　（出典: ${q.source.doc} ${q.source.article}）`);
});
o.push('');
o.push('## 出典URLの状態');
o.push('');
const withU = DATA.filter(q => q.source.url).length;
o.push(`| 区分 | 問数 | 状態 |`);
o.push(`|---|---|---|`);
o.push(`| 原価計算基準 | ${withU} | SPEC §2-1 記載のURL・アンカーを採用。**本セッションでは到達確認できていない** |`);
o.push(`| その他（注解・基準第9号・第10号・連続意見書） | ${DATA.length - withU} | URL未解決。SPEC §2-2 の指示により条番号のみ表示 |`);
o.push('');
o.push('公開ページを特定できた場合は `index.html` の `nolink(...)` を');
o.push('`{doc,article,issuer,url}` の形に置き換える。**アクセスして中身を確認してから登録すること。**');
o.push('');

fs.writeFileSync(__dirname + '/REVIEW.md', o.join('\n'));
console.log('REVIEW.md generated:', o.length, 'lines');
