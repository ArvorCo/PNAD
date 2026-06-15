const fs = require("fs");
const path = require("path");
const { Document, Packer, Paragraph, TextRun, AlignmentType, Header, Footer, PageNumber, BorderStyle } = require("docx");

const md = fs.readFileSync(path.join(__dirname, "..", "docs", "artigo_quaest_100626.md"), "utf8");
const lines = md.split("\n").map(l => l.trim()).filter(l => l.length);

const children = [];
let sawTitle = false;
let sawSubtitle = false;

for (const line of lines) {
  if (line.startsWith("# ")) {
    children.push(new Paragraph({
      style: "ArticleTitle",
      children: [new TextRun(line.slice(2))],
    }));
    sawTitle = true;
  } else if (line.startsWith("## ") && sawTitle && !sawSubtitle) {
    children.push(new Paragraph({
      style: "Subtitle2",
      children: [new TextRun({ text: line.slice(3), italics: true })],
    }));
    sawSubtitle = true;
  } else if (line.startsWith("## ")) {
    children.push(new Paragraph({
      style: "SectionHead",
      children: [new TextRun(line.slice(3))],
    }));
  } else if (/^\*[^*].*\*$/.test(line)) {
    children.push(new Paragraph({
      style: "Signature",
      children: [new TextRun({ text: line.slice(1, -1), italics: true })],
    }));
  } else {
    children.push(new Paragraph({
      style: "Body",
      children: [new TextRun(line)],
    }));
  }
}

const doc = new Document({
  creator: "Leonardo Dias - Arvor Intelligence",
  title: "Os intergalácticos: a direita que vota em Lula com vergonha de dizer",
  description: "Artigo de análise sobre o dossiê Quaest/Genial 10/06/2026",
  styles: {
    default: { document: { run: { font: "Georgia", size: 23 } } },
    paragraphStyles: [
      { id: "ArticleTitle", name: "Article Title", basedOn: "Normal",
        run: { size: 52, bold: true, color: "12151C", font: "Georgia" },
        paragraph: { spacing: { before: 120, after: 200, line: 276 } } },
      { id: "Subtitle2", name: "Linha Fina", basedOn: "Normal",
        run: { size: 28, color: "555A66", font: "Georgia" },
        paragraph: { spacing: { after: 360 }, border: { bottom: { style: BorderStyle.SINGLE, size: 6, color: "12151C", space: 12 } } } },
      { id: "SectionHead", name: "Section Head", basedOn: "Normal",
        run: { size: 32, bold: true, color: "12151C", font: "Georgia" },
        paragraph: { spacing: { before: 360, after: 160 } } },
      { id: "Body", name: "Body", basedOn: "Normal",
        run: { size: 23, color: "1A1D24", font: "Georgia" },
        paragraph: { alignment: AlignmentType.JUSTIFIED, spacing: { after: 160, line: 312 } } },
      { id: "Signature", name: "Signature", basedOn: "Normal",
        run: { size: 22, color: "555A66", font: "Georgia" },
        paragraph: { spacing: { before: 360 }, border: { top: { style: BorderStyle.SINGLE, size: 6, color: "C9C2B3", space: 12 } } } },
    ],
  },
  sections: [{
    properties: { page: { margin: { top: 1440, right: 1700, bottom: 1440, left: 1700 } } },
    headers: {
      default: new Header({ children: [new Paragraph({
        alignment: AlignmentType.RIGHT,
        children: [new TextRun({ text: "ARVOR INTELLIGENCE · AUDITORIA QUAEST 10/06/2026", size: 16, color: "8A8FA0", font: "Arial", bold: true })],
      })] }),
    },
    footers: {
      default: new Footer({ children: [new Paragraph({
        alignment: AlignmentType.CENTER,
        children: [
          new TextRun({ text: "Página ", size: 16, color: "8A8FA0", font: "Arial" }),
          new TextRun({ children: [PageNumber.CURRENT], size: 16, color: "8A8FA0", font: "Arial" }),
          new TextRun({ text: " de ", size: 16, color: "8A8FA0", font: "Arial" }),
          new TextRun({ children: [PageNumber.TOTAL_PAGES], size: 16, color: "8A8FA0", font: "Arial" }),
        ],
      })] }),
    },
    children,
  }],
});

Packer.toBuffer(doc).then(buf => {
  const out = path.join(__dirname, "..", "docs", "artigo_quaest_100626.docx");
  fs.writeFileSync(out, buf);
  console.log("written:", out, buf.length, "bytes");
});
