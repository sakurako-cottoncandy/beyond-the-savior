const React = require("react");
const ReactDOMServer = require("react-dom/server");
const sharp = require("sharp");
const Fi = require("react-icons/fi");

// Renders a react-icons Fi icon to a base64 PNG data URI.
// color: hex without '#'. size: output pixel size (square).
async function iconPng(name, color, size = 256) {
  const Icon = Fi[name];
  if (!Icon) throw new Error(`Unknown icon: ${name}`);
  const svg = ReactDOMServer.renderToStaticMarkup(
    React.createElement(Icon, { color: `#${color}`, size, style: { display: "block" } })
  );
  const buf = await sharp(Buffer.from(svg)).resize(size, size).png().toBuffer();
  return "image/png;base64," + buf.toString("base64");
}

module.exports = { iconPng };
