import { downloadExcelUrl, downloadPdfUrl } from "../api";

export default function DownloadButtons({ visible, topN }) {
  if (!visible) return null;

  return (
    <div className="button-row">
      <a className="btn-download" href={downloadExcelUrl(topN)} style={buttonLinkStyle}>
        Download Excel {topN !== "all" ? `(Top ${topN})` : ""}
      </a>
      <a className="btn-download" href={downloadPdfUrl(topN)} style={buttonLinkStyle}>
        Download PDF {topN !== "all" ? `(Top ${topN})` : ""}
      </a>
    </div>
  );
}

const buttonLinkStyle = {
  padding: "10px 18px",
  borderRadius: "6px",
  textDecoration: "none",
  color: "white",
  display: "inline-block",
};
