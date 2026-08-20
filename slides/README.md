# プレゼン資料の再生成

`docs/Beyond_the_Savior.pptx` を生成するスクリプトです。
スライドの文言やスコアの数値を直したいときは `build.js` を編集して再生成します。

## 必要なもの

- Node.js
- 依存パッケージ（このフォルダで一度だけ実行）

```
npm install pptxgenjs react-icons react react-dom sharp
```

## 生成する

```
node build.js
```

`Beyond_the_Savior_v2.pptx` が同じフォルダに出力されるので、
`docs/Beyond_the_Savior.pptx` に上書きコピーしてください。

## PDFも作る

GitHub上ではPDFがそのままブラウザで読めるので、`docs/` にはPDF版も置いています。
スライドを更新したら、PDFも作り直して差し替えてください。

```
soffice --headless --convert-to pdf Beyond_the_Savior_v2.pptx
```

出力された `Beyond_the_Savior_v2.pdf` を `docs/Beyond_the_Savior.pdf` に上書きコピーします。
（LibreOfficeが必要です。Windowsでは `"C:\Program Files\LibreOffice\program\soffice.exe"` を指定してください）

## ファイルの役割

- `build.js` … スライド22枚の内容とレイアウトの定義
- `icons.js` … アイコン（react-icons）をPNGに変換してスライドに貼るための補助
