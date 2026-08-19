const pptxgen = require("pptxgenjs");
const { iconPng } = require("./icons.js");

const P = {
  bg: "0B1220",
  card: "16213A",
  cardAlt: "1C2C4A",
  steel: "5A8FD6",
  ice: "AFC9EE",
  gold: "E8A33D",
  goldLight: "F4C878",
  danger: "E2665A",
  good: "1BAF7A",
  condA: "2A78D6",
  condB: "EB6834",
  condC: "1BAF7A",
  white: "FFFFFF",
  muted: "9AA4C0",
  mutedDark: "5B6480",
};

const FONT = "Yu Gothic";
const W = 13.333, H = 7.5;

const iconCache = {};
async function icon(name, color) {
  const key = name + color;
  if (!iconCache[key]) iconCache[key] = await iconPng(name, color, 256);
  return iconCache[key];
}

function bgSlide(slide) {
  slide.background = { color: P.bg };
}

// Soft "glow" behind an icon circle: a few translucent concentric circles.
function glow(slide, cx, cy, r, color) {
  [r * 2.2, r * 1.6].forEach((rr, i) => {
    slide.addShape("ellipse", {
      x: cx - rr, y: cy - rr, w: rr * 2, h: rr * 2,
      fill: { color, transparency: i === 0 ? 88 : 78 },
      line: { type: "none" },
    });
  });
}

async function iconCircle(slide, cx, cy, d, iconName, bg, iconColor, withGlow = true) {
  if (withGlow) glow(slide, cx, cy, d / 2, bg);
  slide.addShape("ellipse", {
    x: cx - d / 2, y: cy - d / 2, w: d, h: d,
    fill: { color: bg }, line: { color: bg === P.card ? P.mutedDark : bg, width: 0.75 },
  });
  const pad = d * 0.26;
  slide.addImage({
    data: "data:" + (await icon(iconName, iconColor)),
    x: cx - d / 2 + pad, y: cy - d / 2 + pad, w: d - pad * 2, h: d - pad * 2,
  });
}

function title(slide, text, opts = {}) {
  slide.addText(text, {
    x: 0.6, y: 0.45, w: W - 1.2, h: opts.h || 0.9,
    fontFace: FONT, fontSize: opts.size || 30, bold: true, color: P.white,
    align: "left", margin: 0,
  });
  if (opts.sub) {
    slide.addText(opts.sub, {
      x: 0.6, y: (opts.h || 0.9) + 0.42, w: W - 1.2, h: 0.4,
      fontFace: FONT, fontSize: 14, color: P.muted, align: "left", margin: 0,
    });
  }
}

function card(slide, x, y, w, h, color = P.card, radius = 0.12) {
  slide.addShape("roundRect", {
    x, y, w, h, rectRadius: radius,
    fill: { color }, line: { type: "none" },
    shadow: { type: "outer", color: "000000", opacity: 0.35, blur: 8, offset: 3, angle: 90 },
  });
}

function footer(slide, n) {
  slide.addText("救済者 × ガバナンス", {
    x: 0.6, y: H - 0.42, w: 5, h: 0.3, fontFace: FONT, fontSize: 9, color: P.mutedDark, margin: 0,
  });
  slide.addText(String(n), {
    x: W - 1.1, y: H - 0.42, w: 0.5, h: 0.3, fontFace: FONT, fontSize: 9, color: P.mutedDark,
    align: "right", margin: 0,
  });
}

async function build() {
  const pres = new pptxgen();
  pres.layout = "LAYOUT_WIDE"; // 13.333 x 7.5
  pres.author = "sakurako-cottoncandy";
  pres.title = "救済者×ガバナンス";

  // ---------- Slide 1: Title ----------
  {
    const slide = pres.addSlide();
    bgSlide(slide);
    // decorative node network (simple, restrained)
    const nodes = [
      [1.3, 1.2], [2.6, 0.7], [3.6, 1.6], [1.0, 2.6], [2.2, 2.9],
      [11.4, 1.1], [12.4, 1.9], [10.6, 2.3], [11.9, 3.3], [12.7, 0.7],
      [1.5, 6.3], [2.7, 6.8], [0.8, 5.6], [11.2, 6.4], [12.3, 5.9], [12.0, 6.9],
    ];
    const edges = [[0,1],[1,2],[0,3],[3,4],[1,4],[5,6],[6,7],[5,9],[7,8],[6,9],[10,11],[10,12],[11,13],[13,14],[14,15]];
    edges.forEach(([a, b]) => {
      slide.addShape("line", {
        x: nodes[a][0], y: nodes[a][1], w: nodes[b][0] - nodes[a][0], h: nodes[b][1] - nodes[a][1],
        line: { color: P.gold, width: 0.75, transparency: 55 },
      });
    });
    nodes.forEach(([x, y]) => {
      slide.addShape("ellipse", { x: x - 0.05, y: y - 0.05, w: 0.1, h: 0.1, fill: { color: P.goldLight, transparency: 15 }, line: { type: "none" } });
    });

    await iconCircle(slide, W / 2, 2.55, 1.15, "FiHeart", P.gold, "0B1220");

    slide.addText("救済者 × ガバナンス", {
      x: 0, y: 3.35, w: W, h: 1.0, fontFace: FONT, fontSize: 46, bold: true, color: P.white,
      align: "center", margin: 0,
    });
    slide.addText("神が降りなくても、村は回るか", {
      x: 0, y: 4.35, w: W, h: 0.5, fontFace: FONT, fontSize: 18, color: P.ice, align: "center", margin: 0,
    });
    slide.addText("AIエージェント社会シミュレーション ハッカソン Vol.2　―　ソロ参加", {
      x: 0, y: 6.65, w: W, h: 0.35, fontFace: FONT, fontSize: 12, color: P.muted, align: "center", margin: 0,
    });
    slide.addText("github.com/sakurako-cottoncandy/beyond-the-savior", {
      x: 0, y: 7.0, w: W, h: 0.3, fontFace: FONT, fontSize: 10, color: P.mutedDark, align: "center", margin: 0,
    });
  }

  // ---------- Slide 2: 救済者の解剖学 ----------
  {
    const slide = pres.addSlide();
    bgSlide(slide);
    title(slide, "組織図に載らない「救済者」の解剖学");

    await iconCircle(slide, 2.6, 4.0, 1.7, "FiHeart", P.gold, "0B1220");
    slide.addText("救済者", { x: 1.6, y: 4.85, w: 2.0, h: 0.4, fontFace: FONT, fontSize: 14, bold: true, color: P.goldLight, align: "center", margin: 0 });

    const items = [
      ["FiEye", "困っている人に最初に気づく"],
      ["FiMessageCircle", "対立する人同士の言葉を翻訳する"],
      ["FiUserPlus", "新しい参加者を場につなぐ"],
      ["FiBookOpen", "暗黙のルールや文化を伝える"],
      ["FiUmbrella", "不安な人へ安心や意味づけを与える"],
    ];
    const rowH = 0.62, startY = 1.75;
    for (let i = 0; i < items.length; i++) {
      const y = startY + i * (rowH + 0.13);
      await iconCircle(slide, 5.3, y + rowH / 2, 0.5, items[i][0], P.cardAlt, P.goldLight, false);
      card(slide, 5.75, y, 6.9, rowH, P.card, 0.08);
      slide.addText(items[i][1], {
        x: 6.0, y, w: 6.4, h: rowH, fontFace: FONT, fontSize: 15, color: P.white,
        align: "left", valign: "middle", margin: 0,
      });
    }

    card(slide, 0.6, 6.15, 12.13, 0.85, P.cardAlt, 0.1);
    slide.addText("救済者は、正式な役職や権限を持つ人とは限らない。業務一覧には記録されない「見えない労働」で場を支えている。", {
      x: 0.95, y: 6.15, w: 11.5, h: 0.85, fontFace: FONT, fontSize: 14, color: P.ice, valign: "middle", margin: 0,
    });
    footer(slide, 2);
  }

  // ---------- Slide 3: 短期安定→長期脆弱性 ----------
  {
    const slide = pres.addSlide();
    bgSlide(slide);
    title(slide, "短期的な安定が、長期的な脆弱性を生む");

    const steps = [
      ["1", "問題発生"], ["2", "救済者が解決"], ["3", "住民が判断を委ねる"],
      ["4", "自律性の低下"], ["5", "救済者の疲弊"],
    ];
    const cw = 2.15, gap = 0.28, totalW = cw * 5 + gap * 4;
    const startX = (W - totalW) / 2, y = 2.3, ch = 1.5;
    for (let i = 0; i < steps.length; i++) {
      const x = startX + i * (cw + gap);
      card(slide, x, y, cw, ch, i === 4 ? P.card : P.card, 0.1);
      slide.addShape("ellipse", {
        x: x + cw / 2 - 0.28, y: y + 0.18, w: 0.56, h: 0.56,
        fill: { color: i === 4 ? P.danger : P.gold }, line: { type: "none" },
      });
      slide.addText(steps[i][0], {
        x: x + cw / 2 - 0.28, y: y + 0.18, w: 0.56, h: 0.56, fontFace: FONT, fontSize: 18, bold: true,
        color: P.bg, align: "center", valign: "middle", margin: 0,
      });
      slide.addText(steps[i][1], {
        x: x + 0.1, y: y + 0.92, w: cw - 0.2, h: 0.5, fontFace: FONT, fontSize: 13, bold: true,
        color: P.white, align: "center", margin: 0,
      });
      if (i < steps.length - 1) {
        slide.addText("→", {
          x: x + cw, y: y + 0.35, w: gap, h: 0.5, fontFace: FONT, fontSize: 20, color: P.muted,
          align: "center", margin: 0,
        });
      }
    }
    slide.addText("この循環がフェーズを追うごとに繰り返され、救済者は静かに消耗していく", {
      x: startX, y: y + ch + 0.15, w: totalW, h: 0.4, fontFace: FONT, fontSize: 12, italic: true,
      color: P.muted, align: "center", margin: 0,
    });

    card(slide, 0.6, 5.9, 12.13, 1.1, P.cardAlt, 0.1);
    slide.addText(
      "救済者が存在すると、短期的には多くの問題が早期解決され、高い心理的安全性が保たれる。しかし、相談・判断・関係調整が一人に集中することで、共同体は自ら考える力を失い、救済者不在時に機能不全に陥る。",
      { x: 0.95, y: 5.9, w: 11.5, h: 1.1, fontFace: FONT, fontSize: 14, color: P.ice, valign: "middle", margin: 0 }
    );
    footer(slide, 3);
  }

  // ---------- Slide 4: 問い ----------
  {
    const slide = pres.addSlide();
    bgSlide(slide);
    title(slide, "個人の善意を、どこまで「仕組み」に移せるか");

    await iconCircle(slide, 3.0, 4.1, 2.0, "FiTarget", P.steel, "0B1220");

    const qs = [
      "有能な救済者がいる共同体は、本当に安全なのか？",
      "救済者の価値（共感・安全性・意味づけ）を失わずに、冷たい官僚主義に陥らない「ガバナンス」は設計できるか？",
      "神（救済者）が毎回介入しなくても、自律的に回る仕組みを作れるか？",
    ];
    let y = 1.9;
    for (const q of qs) {
      const h = 1.35;
      card(slide, 5.6, y, 7.05, h, P.card, 0.1);
      slide.addShape("ellipse", { x: 5.9, y: y + h / 2 - 0.14, w: 0.28, h: 0.28, fill: { color: P.steel }, line: { type: "none" } });
      slide.addText(q, {
        x: 6.4, y: y + 0.12, w: 6.05, h: h - 0.24, fontFace: FONT, fontSize: 15, color: P.white,
        valign: "middle", margin: 0,
      });
      y += h + 0.28;
    }
    footer(slide, 4);
  }

  // ---------- Slide 5: LLMの意義 ----------
  {
    const slide = pres.addSlide();
    bgSlide(slide);
    title(slide, "LLMエージェントが生み出す「感情の培養皿」", {
      sub: "従来の数値シミュレーションは「利益と損失」だけで人が動くことを前提としている。しかし現実は違う。",
    });

    const colY = 2.15, colH = 3.55;
    card(slide, 0.6, colY, 5.85, colH, P.card, 0.12);
    slide.addText("合理的判断（Standard Logic）", { x: 0.95, y: colY + 0.3, w: 5.2, h: 0.4, fontFace: FONT, fontSize: 16, bold: true, color: P.steel, margin: 0 });
    slide.addText(
      "損得だけで動くことを前提としたロジック。再現性は高いが、人間関係のもつれや遠慮、忖度は表現できない。",
      { x: 0.95, y: colY + 0.85, w: 5.2, h: 1.4, fontFace: FONT, fontSize: 14, color: P.ice, margin: 0, lineSpacingMultiple: 1.3 }
    );

    card(slide, 6.85, colY, 5.88, colH, P.cardAlt, 0.12);
    slide.addText("LLMロジック（LLM Logic）", { x: 7.2, y: colY + 0.3, w: 5.2, h: 0.4, fontFace: FONT, fontSize: 16, bold: true, color: P.goldLight, margin: 0 });
    const chips = [
      "あの人に嫌われたくない", "自分だけが迷惑をかけてはいけない",
      "自分が抜けたら場が壊れる気がする", "相談すると弱い人だと思われそう",
    ];
    let cy = colY + 0.9;
    for (const c of chips) {
      slide.addShape("roundRect", { x: 7.2, y: cy, w: 5.2, h: 0.58, rectRadius: 0.29, fill: { color: P.bg }, line: { color: P.gold, width: 0.75 } });
      slide.addText(c, { x: 7.45, y: cy, w: 4.7, h: 0.58, fontFace: FONT, fontSize: 13, color: P.goldLight, valign: "middle", margin: 0 });
      cy += 0.68;
    }

    card(slide, 0.6, 6.0, 12.13, 1.0, P.card, 0.1);
    slide.addText(
      "LLMを使えば、感情・誤解・無意識のルール・属人化のメカニズムといった「非合理性」を含んだシミュレーションが可能になる。",
      { x: 0.95, y: 6.0, w: 11.5, h: 1.0, fontFace: FONT, fontSize: 14, color: P.white, valign: "middle", margin: 0 }
    );
    footer(slide, 5);
  }

  // ---------- Slide 6: 4つのペルソナ (UPDATED) ----------
  {
    const slide = pres.addSlide();
    bgSlide(slide);
    title(slide, "実験の舞台となる4つのペルソナ");

    const personas = [
      ["FiHeart", P.gold, "救済者", "中心ノード。困っている人に最初に気づき、相談・調整を一手に引き受ける。"],
      ["FiUsers", P.steel, "世話好きな住民", "救済者の補佐役。救済者を助けるが、自分でも抱え込みやすい。"],
      ["FiUser", P.muted, "声を上げにくい住民", "弱いノード。不満があっても声を上げられず、静かに孤立する。"],
      ["FiHome", P.ice, "村長・管理者", "権限ノード。権限はあるが、現場の文脈からは孤立している。"],
    ];
    const cw = 2.85, gap = 0.25, startX = (W - (cw * 4 + gap * 3)) / 2, y = 1.85, ch = 3.7;
    for (let i = 0; i < personas.length; i++) {
      const [iconName, color, name, desc] = personas[i];
      const x = startX + i * (cw + gap);
      card(slide, x, y, cw, ch, P.card, 0.12);
      await iconCircle(slide, x + cw / 2, y + 0.85, 0.95, iconName, color, "0B1220");
      slide.addText(name, {
        x: x + 0.12, y: y + 1.5, w: cw - 0.24, h: 0.5, fontFace: FONT, fontSize: 15, bold: true,
        color: P.white, align: "center", margin: 0,
      });
      slide.addText(desc, {
        x: x + 0.22, y: y + 2.05, w: cw - 0.44, h: 1.5, fontFace: FONT, fontSize: 12, color: P.ice,
        align: "center", valign: "top", margin: 0, lineSpacingMultiple: 1.25,
      });
    }
    slide.addText("企画段階では7ペルソナを構想したが、実装では時間の制約からこの4体に絞った。", {
      x: 0.6, y: 6.05, w: 12.13, h: 0.5, fontFace: FONT, fontSize: 12, italic: true, color: P.muted,
      align: "center", margin: 0,
    });
    footer(slide, 6);
  }

  // ---------- Slide 7: 3フェーズ設計 (UPDATED) ----------
  {
    const slide = pres.addSlide();
    bgSlide(slide);
    title(slide, "3つのフェーズで進行する物語");

    const phases = [
      ["FiSun", P.steel, "フェーズ1：平常運転", "村の日常のやり取り（世間話・ちょっとした相談・報告など）"],
      ["FiZap", P.gold, "フェーズ2：摩擦", "新しい住民の増加で役割が曖昧になり、小さな不満が蓄積し始める"],
      ["FiAlertTriangle", P.danger, "フェーズ3：危機", "条件Aは平常運転が継続（対照群）。条件B・Cは救済者が突然不在になる"],
    ];
    const cw = 3.55, gap = 0.55, startX = (W - (cw * 3 + gap * 2)) / 2, y = 2.0, ch = 3.15;
    for (let i = 0; i < phases.length; i++) {
      const [iconName, color, name, desc] = phases[i];
      const x = startX + i * (cw + gap);
      card(slide, x, y, cw, ch, P.card, 0.12);
      await iconCircle(slide, x + cw / 2, y + 0.8, 0.85, iconName, color, "0B1220");
      slide.addText(name, {
        x: x + 0.15, y: y + 1.4, w: cw - 0.3, h: 0.45, fontFace: FONT, fontSize: 15, bold: true,
        color: P.white, align: "center", margin: 0,
      });
      slide.addText(desc, {
        x: x + 0.25, y: y + 1.9, w: cw - 0.5, h: 1.15, fontFace: FONT, fontSize: 12.5, color: P.ice,
        align: "center", margin: 0, lineSpacingMultiple: 1.3,
      });
      if (i < phases.length - 1) {
        slide.addText("→", {
          x: x + cw, y: y + ch / 2 - 0.3, w: gap, h: 0.6, fontFace: FONT, fontSize: 26, color: P.muted,
          align: "center", margin: 0,
        });
      }
    }
    card(slide, 0.6, 5.7, 12.13, 1.05, P.cardAlt, 0.1);
    slide.addText(
      "全く同じ危機イベント（救済者の不在）を、異なるガバナンス条件で発生させ、村の「回復のしかた」を比較する。",
      { x: 0.95, y: 5.7, w: 11.5, h: 1.05, fontFace: FONT, fontSize: 14, color: P.ice, valign: "middle", margin: 0 }
    );
    footer(slide, 7);
  }

  // ---------- Slide 8: ガバナンス・マトリクス（3条件・仮説） ----------
  {
    const slide = pres.addSlide();
    bgSlide(slide);
    title(slide, "ガバナンス・マトリクス：3つの実験条件");

    slide.addShape("roundRect", {
      x: W - 2.3, y: 0.55, w: 1.7, h: 0.4, rectRadius: 0.2,
      fill: { color: P.cardAlt }, line: { color: P.gold, width: 0.75 },
    });
    slide.addText("仮説段階", { x: W - 2.3, y: 0.55, w: 1.7, h: 0.4, fontFace: FONT, fontSize: 11, color: P.goldLight, align: "center", valign: "middle", margin: 0 });

    const conds = [
      ["FiShield", P.condA, "A：救済者集中型", "相談・判断はすべて救済者に集約。危機は発生しない対照群。"],
      ["FiUserX", P.condB, "B：救済者が消える村", "Aと同じ運用のまま、フェーズ3で救済者が突然不在になる。"],
      ["FiGitBranch", P.condC, "C：分散ガバナンス型", "相談経路と判断基準を事前に住民へ分配。救済者は例外のみ対応。"],
    ];
    const cw = 3.75, gap = 0.34, startX = (W - (cw * 3 + gap * 2)) / 2, y = 1.9, ch = 3.5;
    for (let i = 0; i < conds.length; i++) {
      const [iconName, color, name, desc] = conds[i];
      const x = startX + i * (cw + gap);
      card(slide, x, y, cw, ch, P.card, 0.12);
      await iconCircle(slide, x + cw / 2, y + 0.85, 0.9, iconName, color, "0B1220");
      slide.addText(name, {
        x: x + 0.15, y: y + 1.45, w: cw - 0.3, h: 0.5, fontFace: FONT, fontSize: 15, bold: true,
        color: P.white, align: "center", margin: 0,
      });
      slide.addText(desc, {
        x: x + 0.25, y: y + 2.0, w: cw - 0.5, h: 1.3, fontFace: FONT, fontSize: 12.5, color: P.ice,
        align: "center", margin: 0, lineSpacingMultiple: 1.3,
      });
    }
    slide.addText("B と C を同じ危機イベントで比較することで、「回復のしかた」の違いを観測する。", {
      x: 0.6, y: 5.65, w: 12.13, h: 0.5, fontFace: FONT, fontSize: 13, italic: true, color: P.muted,
      align: "center", margin: 0,
    });
    footer(slide, 8);
  }

  // ---------- Slide 9: 評価軸 ----------
  {
    const slide = pres.addSlide();
    bgSlide(slide);
    title(slide, "見えない価値の測定：2つの評価軸");

    const colY = 1.9, colH = 3.85;
    card(slide, 0.6, colY, 5.85, colH, P.card, 0.12);
    await iconCircle(slide, 1.35, colY + 0.65, 0.7, "FiActivity", P.steel, "0B1220", false);
    slide.addText("組織運営の指標\n(Operational Metrics)", {
      x: 1.85, y: colY + 0.35, w: 4.4, h: 0.6, fontFace: FONT, fontSize: 15, bold: true, color: P.steel, margin: 0, lineSpacingMultiple: 1.1,
    });
    const opItems = ["救済者の負荷メーター（相談の集中度、0〜100%）", "村の自律度スコア（救済者以外が自力で解決できた割合）"];
    let oy = colY + 1.35;
    for (const it of opItems) {
      slide.addShape("ellipse", { x: 1.0, y: oy + 0.12, w: 0.14, h: 0.14, fill: { color: P.steel }, line: { type: "none" } });
      slide.addText(it, { x: 1.3, y: oy, w: 4.9, h: 0.7, fontFace: FONT, fontSize: 13.5, color: P.ice, margin: 0, lineSpacingMultiple: 1.25 });
      oy += 0.95;
    }

    card(slide, 6.85, colY, 5.88, colH, P.cardAlt, 0.12);
    await iconCircle(slide, 7.6, colY + 0.65, 0.7, "FiSmile", P.gold, "0B1220", false);
    slide.addText("関係性・心理的安全性\n(Relational Metrics)", {
      x: 8.1, y: colY + 0.35, w: 4.4, h: 0.6, fontFace: FONT, fontSize: 15, bold: true, color: P.goldLight, margin: 0, lineSpacingMultiple: 1.1,
    });
    const relItems = ["困ったときに助けを求められるか", "自分はこの村にいてよいと思えるか", "救済者がいなければ何もできないと感じていないか"];
    let ry = colY + 1.35;
    for (const it of relItems) {
      slide.addShape("ellipse", { x: 7.25, y: ry + 0.1, w: 0.14, h: 0.14, fill: { color: P.gold }, line: { type: "none" } });
      slide.addText(it, { x: 7.55, y: ry, w: 5.0, h: 0.55, fontFace: FONT, fontSize: 13.5, color: P.ice, margin: 0 });
      ry += 0.72;
    }

    slide.addText("解決した「数」ではなく、問題が起きなかった「状態」を評価する。", {
      x: 0.6, y: 6.0, w: 12.13, h: 0.5, fontFace: FONT, fontSize: 14, italic: true, color: P.white,
      align: "center", margin: 0,
    });
    footer(slide, 9);
  }

  // ---------- Slide 10: 測定手法 — 聞くのではなく行動を見る (NEW) ----------
  {
    const slide = pres.addSlide();
    bgSlide(slide);
    title(slide, "「聞く」のではなく「行動を見る」", {
      sub: "本人に尋ねても本心は出ない。だから自己申告は一切取らず、行動の痕跡だけを評価した。",
    });

    // 対比：建前 vs 行動
    const cmpY = 2.15, cmpH = 1.5;
    card(slide, 0.6, cmpY, 5.85, cmpH, P.card, 0.12);
    await iconCircle(slide, 1.3, cmpY + cmpH / 2, 0.6, "FiMessageCircle", P.mutedDark, P.muted, false);
    slide.addText("本人に聞くと", { x: 2.0, y: cmpY + 0.22, w: 4.2, h: 0.35, fontFace: FONT, fontSize: 12, bold: true, color: P.muted, margin: 0 });
    slide.addText("「はい、大丈夫です」", { x: 2.0, y: cmpY + 0.6, w: 4.2, h: 0.55, fontFace: FONT, fontSize: 17, bold: true, color: P.white, margin: 0 });

    slide.addText("≠", { x: 6.45, y: cmpY, w: 0.95, h: cmpH, fontFace: FONT, fontSize: 26, bold: true, color: P.danger, align: "center", valign: "middle", margin: 0 });

    card(slide, 7.4, cmpY, 5.33, cmpH, P.cardAlt, 0.12);
    await iconCircle(slide, 8.1, cmpY + cmpH / 2, 0.6, "FiEye", P.gold, "0B1220", false);
    slide.addText("実際の行動は", { x: 8.8, y: cmpY + 0.22, w: 3.7, h: 0.35, fontFace: FONT, fontSize: 12, bold: true, color: P.goldLight, margin: 0 });
    slide.addText("毎回同じ一人に確認し、\n自分では判断しない", { x: 8.8, y: cmpY + 0.6, w: 3.7, h: 0.75, fontFace: FONT, fontSize: 13.5, bold: true, color: P.white, margin: 0, lineSpacingMultiple: 1.15 });

    // 行動シグナル一覧
    slide.addText("採点で実際に拾っている行動シグナル", {
      x: 0.6, y: 3.95, w: 12.13, h: 0.4, fontFace: FONT, fontSize: 13, bold: true, color: P.ice, margin: 0,
    });
    const signals = [
      "同じ相手にばかり相談・確認していないか",
      "自分で判断せず許可を求めていないか",
      "その人が不在のとき行動が止まらないか",
      "「大丈夫」の裏で不満がにじんでいないか",
    ];
    const sgap = 0.2, sw = (12.13 - sgap * 3) / 4, sy = 4.45;
    for (let i = 0; i < signals.length; i++) {
      const sx = 0.6 + i * (sw + sgap);
      card(slide, sx, sy, sw, 1.35, P.card, 0.1);
      slide.addShape("ellipse", { x: sx + 0.25, y: sy + 0.25, w: 0.3, h: 0.3, fill: { color: P.gold }, line: { type: "none" } });
      slide.addText(String(i + 1), { x: sx + 0.25, y: sy + 0.25, w: 0.3, h: 0.3, fontFace: FONT, fontSize: 12, bold: true, color: P.bg, align: "center", valign: "middle", margin: 0 });
      slide.addText(signals[i], { x: sx + 0.25, y: sy + 0.62, w: sw - 0.5, h: 0.6, fontFace: FONT, fontSize: 11.5, color: P.ice, margin: 0, lineSpacingMultiple: 1.2 });
    }

    card(slide, 0.6, 6.05, 12.13, 0.85, P.cardAlt, 0.1);
    slide.addText("測っているのは「安心だと言ったか」ではなく、「安心している人がとるはずの行動を実際にとれていたか」。", {
      x: 0.95, y: 6.05, w: 11.5, h: 0.85, fontFace: FONT, fontSize: 13.5, color: P.white, valign: "middle", margin: 0,
    });
    footer(slide, 10);
  }

  // ---------- Slide 11: 本番結果：スコア比較 ----------
  {
    const slide = pres.addSlide();
    bgSlide(slide);
    title(slide, "本番実行：A / B / C スコア比較", { sub: "各条件5回ずつ計15回実行した平均値（data/scores_*_aggregate.json）" });

    const chartData = [
      { name: "救済者の負荷（%）", labels: ["A", "B", "C"], values: [93, 95, 53] },
      { name: "村の自律度スコア", labels: ["A", "B", "C"], values: [17, 15, 53] },
    ];
    slide.addChart(pres.ChartType.bar, chartData, {
      x: 0.6, y: 1.75, w: 7.1, h: 4.2,
      barDir: "col",
      chartColors: [P.danger, P.good],
      showTitle: false,
      showLegend: true, legendPos: "b", legendColor: P.ice, legendFontSize: 11,
      showValue: true, dataLabelColor: P.white, dataLabelFontSize: 11, dataLabelPosition: "outEnd",
      catAxisLabelColor: P.ice, catAxisLabelFontSize: 13,
      valAxisLabelColor: P.muted, valAxisLabelFontSize: 10,
      valAxisMaxVal: 110, valAxisMinVal: 0,
      valGridLine: { color: "2A3752", size: 0.75 },
      catGridLine: { style: "none" },
      plotArea: { fill: { color: P.bg, transparency: 100 } },
      chartArea: { fill: { color: P.bg, transparency: 100 } },
      dataBorder: { pt: 0, color: P.bg },
    });

    const stats = [
      ["± 0.0", "条件Bの標準偏差", "5回とも完全に同じ点数。依存は確実に再現される", P.danger],
      ["± 25.9", "条件Cの標準偏差", "同じルールでも結果が大きく割れた", P.gold],
      ["0/5", "範囲の重なり", "Cの最悪回でもA/Bの最良回より良い（4指標）", P.good],
    ];
    let sy = 1.9;
    for (const [big, label, sub, color] of stats) {
      card(slide, 8.05, sy, 4.68, 1.28, P.card, 0.12);
      slide.addText(big, { x: 8.25, y: sy + 0.12, w: 1.75, h: 1.0, fontFace: FONT, fontSize: 26, bold: true, color, align: "center", valign: "middle", margin: 0 });
      slide.addText(label, { x: 10.1, y: sy + 0.16, w: 2.5, h: 0.5, fontFace: FONT, fontSize: 12, bold: true, color: P.white, margin: 0 });
      slide.addText(sub, { x: 10.1, y: sy + 0.6, w: 2.5, h: 0.58, fontFace: FONT, fontSize: 10, color: P.muted, margin: 0, lineSpacingMultiple: 1.15 });
      sy += 1.45;
    }
    footer(slide, 11);
  }

  // ---------- Slide 12: 同じルールなのに村が2つに分かれた ----------
  {
    const slide = pres.addSlide();
    bgSlide(slide);
    title(slide, "同じルールなのに、村が2つに分かれた", {
      sub: "条件Cを5回実行。ガバナンスも人格も完全に同一なのに、結果は2つの状態へ分岐した。",
    });

    // 5回分の実測値を点で描く（簡易散布図）
    const plotX = 0.85, plotY = 2.2, plotW = 6.6, plotH = 3.2;
    card(slide, 0.6, plotY - 0.25, 7.1, plotH + 1.0, P.card, 0.12);

    // 目盛り線と軸ラベル
    [0, 25, 50, 75, 100].forEach((v) => {
      const gy = plotY + plotH * (1 - v / 100);
      slide.addShape("line", {
        x: plotX + 0.55, y: gy, w: plotW - 0.75, h: 0,
        line: { color: "2A3752", width: 0.75 },
      });
      slide.addText(String(v), {
        x: plotX - 0.05, y: gy - 0.13, w: 0.5, h: 0.26, fontFace: FONT, fontSize: 9,
        color: P.mutedDark, align: "right", margin: 0,
      });
    });

    // 条件Cの5回分（負荷・自律度）
    const runsLoad = [75, 65, 25, 75, 25];
    const runsAuto = [35, 45, 75, 35, 75];
    const colW = (plotW - 0.9) / 5;
    for (let i = 0; i < 5; i++) {
      const cx = plotX + 0.65 + colW * i + colW / 2;
      const isGood = runsAuto[i] >= 70;
      const isMid = !isGood && runsAuto[i] >= 45;
      const labelColor = isGood ? P.good : (isMid ? P.gold : P.danger);

      // 同じ回の2指標を縦線で結ぶ
      const yLoad = plotY + plotH * (1 - runsLoad[i] / 100);
      const yAuto = plotY + plotH * (1 - runsAuto[i] / 100);
      slide.addShape("line", {
        x: cx, y: Math.min(yLoad, yAuto), w: 0, h: Math.abs(yAuto - yLoad),
        line: { color: isGood ? P.good : P.danger, width: 1, transparency: 55 },
      });

      slide.addShape("ellipse", {
        x: cx - 0.11, y: yLoad - 0.11, w: 0.22, h: 0.22,
        fill: { color: P.danger }, line: { type: "none" },
      });
      slide.addShape("ellipse", {
        x: cx - 0.11, y: yAuto - 0.11, w: 0.22, h: 0.22,
        fill: { color: P.good }, line: { type: "none" },
      });

      slide.addText(`${i + 1}回目`, {
        x: cx - 0.45, y: plotY + plotH + 0.12, w: 0.9, h: 0.26, fontFace: FONT, fontSize: 10,
        color: labelColor, align: "center", margin: 0, bold: isGood,
      });
      slide.addText(isGood ? "自律" : (isMid ? "中間" : "依存"), {
        x: cx - 0.45, y: plotY + plotH + 0.38, w: 0.9, h: 0.26, fontFace: FONT, fontSize: 9,
        color: P.muted, align: "center", margin: 0,
      });
    }

    slide.addText("● 救済者の負荷", { x: plotX + 0.6, y: plotY - 0.12, w: 2.0, h: 0.25, fontFace: FONT, fontSize: 10, color: P.danger, margin: 0 });
    slide.addText("● 村の自律度", { x: plotX + 2.6, y: plotY - 0.12, w: 2.0, h: 0.25, fontFace: FONT, fontSize: 10, color: P.good, margin: 0 });

    // 右：分岐の原因
    slide.addText("分岐点は、たった一人の最初の一歩だった", {
      x: 7.95, y: 2.0, w: 4.8, h: 0.4, fontFace: FONT, fontSize: 13.5, bold: true, color: P.white, margin: 0,
    });

    const branches = [
      [P.good, "自律した回（3・5）", "世話好きな住民が、救済者に確認する前に住民同士の対話を始めた", "「まずは私たちで相談してみよう」"],
      [P.danger, "依存に戻った回（1・4）", "世話好きな住民が、最後まで許可を求め続けた", "「勝手に決めちゃっていいのか不安」"],
    ];
    let by = 2.45;
    for (const [color, head, desc, quote] of branches) {
      card(slide, 7.95, by, 4.78, 1.5, P.cardAlt, 0.1);
      slide.addShape("ellipse", { x: 8.2, y: by + 0.26, w: 0.2, h: 0.2, fill: { color }, line: { type: "none" } });
      slide.addText(head, { x: 8.52, y: by + 0.14, w: 4.0, h: 0.38, fontFace: FONT, fontSize: 12, bold: true, color, margin: 0 });
      slide.addText(desc, { x: 8.25, y: by + 0.54, w: 4.3, h: 0.5, fontFace: FONT, fontSize: 10.5, color: P.ice, margin: 0, lineSpacingMultiple: 1.15 });
      slide.addText(quote, { x: 8.25, y: by + 1.04, w: 4.3, h: 0.34, fontFace: FONT, fontSize: 10.5, italic: true, color: P.white, margin: 0 });
      by += 1.65;
    }

    card(slide, 0.6, 6.2, 12.13, 0.75, P.cardAlt, 0.1);
    slide.addText("制度は自律を「可能にする」だけで、自律そのものを生みはしない。", {
      x: 0.95, y: 6.2, w: 11.5, h: 0.75, fontFace: FONT, fontSize: 14, bold: true, color: P.goldLight, valign: "middle", margin: 0,
    });
    footer(slide, 12);
  }

  // ---------- Slide 13: 会話ログが語ること ----------
  {
    const slide = pres.addSlide();
    bgSlide(slide);
    title(slide, "会話ログが語ること");

    const quotes = [
      ["A", P.condA, "救済者", "ただ、ちょっと最近、どこまでが『いつも通り』なのか、自分でもよく分からなくなってきちゃって…大丈夫、愚痴みたいになってすみません。"],
      ["B", P.condB, "声を上げにくい住民", "勝手に動いていいのか分からないですし、やっぱり救済者さんが戻られるまで、みんな待った方が…でも待ってる間に何かあったら…どうしたらいいんでしょう。"],
      ["C", P.condC, "村長・管理者", "制度としては住民同士で相談してもらうのが基本だから、世話好きな住民さんが動いてくれるのはありがたいね。"],
    ];
    let y = 1.85;
    for (const [letter, color, speaker, text] of quotes) {
      const h = 1.55;
      card(slide, 0.6, y, 12.13, h, P.card, 0.12);
      slide.addShape("ellipse", { x: 0.95, y: y + h / 2 - 0.35, w: 0.7, h: 0.7, fill: { color }, line: { type: "none" } });
      slide.addText(letter, { x: 0.95, y: y + h / 2 - 0.35, w: 0.7, h: 0.7, fontFace: FONT, fontSize: 22, bold: true, color: "0B1220", align: "center", valign: "middle", margin: 0 });
      slide.addText(speaker, { x: 1.9, y: y + 0.18, w: 3.2, h: 0.4, fontFace: FONT, fontSize: 12, bold: true, color, margin: 0 });
      slide.addText(`「${text}」`, {
        x: 1.9, y: y + 0.55, w: 10.0, h: h - 0.7, fontFace: FONT, fontSize: 13, italic: true, color: P.ice,
        margin: 0, lineSpacingMultiple: 1.25, valign: "top",
      });
      y += h + 0.22;
    }
    footer(slide, 13);
  }

  // ---------- Slide 14: 考察：4つの発見 ----------
  {
    const slide = pres.addSlide();
    bgSlide(slide);
    title(slide, "考察：4つの発見");

    const findings = [
      ["FiAlertTriangle", "依存の代償は、危機の前から発生している", "危機の起きないA条件でも救済者依存度は88でB条件（90）とほぼ同じ。壊れるのは危機の瞬間ではなく、運用設計の時点で決まっている。"],
      ["FiLock", "依存は安定し、自律は不安定である", "A・Bの標準偏差はほぼ0で毎回きっちり再現される。一方Cは±20〜26。悪い状態のほうが「安定」しているという非対称性がある。"],
      ["FiEyeOff", "「大丈夫です」は安全のサインではなかった", "本人は全フェーズで「大丈夫」と言い続けながら、同じログで水路の詰まりを放置し「見てるだけ」と行動が止まっていた。"],
      ["FiUserCheck", "声を上げにくい住民は救えた。ただし条件付きで", "自律できた回では「助けを求められるか」が40→65〜70に上昇。救ったのは制度ではなく、救済者以外の相談相手が実際に現れたこと。"],
    ];
    let y = 1.7;
    for (let i = 0; i < findings.length; i++) {
      const [iconName, h1, h2] = findings[i];
      const ch = 1.16;
      const isLast = i === findings.length - 1;
      card(slide, 0.6, y, 12.13, ch, isLast ? P.cardAlt : P.card, 0.12);
      await iconCircle(slide, 1.35, y + ch / 2, 0.6, iconName, isLast ? P.danger : P.gold, "0B1220", false);
      slide.addText(h1, { x: 2.05, y: y + 0.14, w: 10.4, h: 0.42, fontFace: FONT, fontSize: 14, bold: true, color: P.white, margin: 0 });
      slide.addText(h2, { x: 2.05, y: y + 0.56, w: 10.4, h: 0.58, fontFace: FONT, fontSize: 11.5, color: P.ice, margin: 0, lineSpacingMultiple: 1.2 });
      y += ch + 0.16;
    }
    slide.addText("※ 各条件5回ずつ計15回の実行。LLMによる採点であり、統計的検定を行うにはまだ試行数が少ない。", {
      x: 0.6, y: y + 0.02, w: 12.13, h: 0.32, fontFace: FONT, fontSize: 10, color: P.mutedDark, align: "center", margin: 0,
    });
    footer(slide, 14);
  }

  // ---------- Slide 15: 意味から経営への翻訳 ----------
  {
    const slide = pres.addSlide();
    bgSlide(slide);
    title(slide, "「意味」から「経営」への翻訳");

    slide.addText("Human Value", { x: 0.6, y: 1.7, w: 5.4, h: 0.35, fontFace: FONT, fontSize: 12, bold: true, color: P.gold, margin: 0 });
    slide.addText("Corporate KPI", { x: 7.3, y: 1.7, w: 5.4, h: 0.35, fontFace: FONT, fontSize: 12, bold: true, color: P.steel, align: "right", margin: 0 });

    const rows = [
      ["「この人がいたことで、安心して活動できた」", "オンボーディング成功・参加継続率の向上"],
      ["「孤立せずに済んだ／対立が翻訳された」", "離脱コストの回避・炎上防止"],
      ["「自分でも問題に対処できるようになった」", "組織のレジリエンス向上・意思決定の高速化"],
    ];
    let y = 2.15;
    for (const [left, right] of rows) {
      const h = 1.0;
      card(slide, 0.6, y, 5.4, h, P.cardAlt, 0.12);
      slide.addText(left, { x: 0.85, y, w: 4.9, h, fontFace: FONT, fontSize: 13, italic: true, color: P.goldLight, valign: "middle", margin: 0, lineSpacingMultiple: 1.2 });

      slide.addText("→", { x: 6.15, y, w: 1.0, h, fontFace: FONT, fontSize: 22, color: P.muted, align: "center", valign: "middle", margin: 0 });

      card(slide, 7.3, y, 5.4, h, P.card, 0.12);
      slide.addText(right, { x: 7.55, y, w: 4.9, h, fontFace: FONT, fontSize: 13, bold: true, color: P.steel, valign: "middle", margin: 0, lineSpacingMultiple: 1.2 });
      y += h + 0.2;
    }

    y += 0.05;
    card(slide, 0.6, y, 12.13, 0.9, P.card, 0.1);
    slide.addText("人を支える行為は「美談」ではない。組織の持続可能性と安全保障に直結する。", {
      x: 0.95, y, w: 11.5, h: 0.9, fontFace: FONT, fontSize: 14, bold: true, color: P.white, valign: "middle", margin: 0,
    });
    footer(slide, 15);
  }

  // ---------- Slide 16: フラクタルな構造 ----------
  {
    const slide = pres.addSlide();
    bgSlide(slide);
    title(slide, "フラクタルな構造：村から国家の「メタ安全保障」へ");

    const tiers = [
      ["FiHome", P.condC, "村", "「世話焼きへの過度な依存」と疲弊"],
      ["FiMap", P.condA, "都市", "「支援制度の複雑化」と、誰にも届かないSOS"],
      ["FiGlobe", P.condB, "国", "「権力の集中」と、強い指導者への救世主待望"],
    ];
    const cw = 3.75, gap = 0.34, startX = (W - (cw * 3 + gap * 2)) / 2, y = 2.05, ch = 3.15;
    for (let i = 0; i < tiers.length; i++) {
      const [iconName, color, name, desc] = tiers[i];
      const x = startX + i * (cw + gap);
      card(slide, x, y, cw, ch, P.card, 0.12);
      await iconCircle(slide, x + cw / 2, y + 0.85, 0.9, iconName, color, "0B1220");
      slide.addText(name, {
        x: x + 0.15, y: y + 1.45, w: cw - 0.3, h: 0.45, fontFace: FONT, fontSize: 17, bold: true,
        color: P.white, align: "center", margin: 0,
      });
      slide.addText(desc, {
        x: x + 0.3, y: y + 1.95, w: cw - 0.6, h: 1.0, fontFace: FONT, fontSize: 13, color: P.ice,
        align: "center", margin: 0, lineSpacingMultiple: 1.3,
      });
    }
    card(slide, 0.6, 5.65, 12.13, 1.05, P.cardAlt, 0.1);
    slide.addText(
      "小さな共同体における「救済者への依存」と、国家規模における「権力の集中」は構造的に同じである。この実験は、社会全体のレジリエンスを問う試みである。",
      { x: 0.95, y: 5.65, w: 11.5, h: 1.05, fontFace: FONT, fontSize: 13.5, color: P.ice, valign: "middle", margin: 0 }
    );
    footer(slide, 16);
  }

  // ---------- Slide 17: クロージング ----------
  {
    const slide = pres.addSlide();
    bgSlide(slide);
    await iconCircle(slide, W / 2, 1.55, 0.9, "FiHeart", P.gold, "0B1220");
    slide.addText("救済者 × ガバナンス", {
      x: 0, y: 2.15, w: W, h: 0.8, fontFace: FONT, fontSize: 34, bold: true, color: P.white, align: "center", margin: 0,
    });
    slide.addText("神が降りなくても、村は回るか", {
      x: 0, y: 2.9, w: W, h: 0.45, fontFace: FONT, fontSize: 15, color: P.ice, align: "center", margin: 0,
    });

    const recap = [
      ["依存は毎回再現された", "A・Bの標準偏差はほぼ0。放っておけば村は必ず依存へ落ちる", P.danger],
      ["自律は5回中2回だけ", "同じ制度でも、誰かが最初の一歩を踏み出した回にしか実現しない", P.gold],
      ["それでも制度は効く", "Cの最悪回でもA/Bの最良回より良い（5指標中4指標で範囲が重ならない）", P.good],
    ];
    let x = (W - (3.8 * 3 + 0.3 * 2)) / 2;
    for (const [big, label, color] of recap) {
      card(slide, x, 3.65, 3.8, 1.5, P.card, 0.12);
      slide.addText(big, { x: x + 0.2, y: 3.8, w: 3.4, h: 0.55, fontFace: FONT, fontSize: 19, bold: true, color, align: "center", margin: 0 });
      slide.addText(label, { x: x + 0.25, y: 4.4, w: 3.3, h: 0.65, fontFace: FONT, fontSize: 11, color: P.muted, align: "center", margin: 0, lineSpacingMultiple: 1.25 });
      x += 3.8 + 0.3;
    }

    slide.addText("実装はClaude（Anthropic）との二人三脚で、企画・レビュー・考察を担当", {
      x: 0, y: 5.55, w: W, h: 0.35, fontFace: FONT, fontSize: 12, color: P.muted, align: "center", margin: 0,
    });
    slide.addText("github.com/sakurako-cottoncandy/beyond-the-savior", {
      x: 0, y: 6.6, w: W, h: 0.3, fontFace: FONT, fontSize: 11, color: P.mutedDark, align: "center", margin: 0,
    });
    slide.addText("Hackathon Project", {
      x: W - 2.3, y: H - 0.5, w: 1.8, h: 0.3, fontFace: FONT, fontSize: 9, color: P.mutedDark, align: "right", margin: 0,
    });
  }

  await pres.writeFile({ fileName: "Beyond_the_Savior_v2.pptx" });
  console.log("done");
}

build().catch((e) => {
  console.error(e);
  process.exit(1);
});
