import { useState } from "react";

const PRESETS = [5, 10, 20, 50];

export default function TopNFilter({ value, onChange, totalCount }) {
  const [customInput, setCustomInput] = useState("");

  if (totalCount === 0) return null;

  const applyCustom = () => {
    const n = parseInt(customInput, 10);
    if (n > 0) {
      onChange(n);
    }
  };

  const handleKeyDown = (e) => {
    if (e.key === "Enter") {
      e.preventDefault();
      applyCustom();
    }
  };

  return (
    <div style={{ marginTop: "16px" }}>
      <div style={{ display: "flex", alignItems: "center", gap: "8px", flexWrap: "wrap" }}>
        <span style={{ fontSize: "13px", fontWeight: 600 }}>Show top:</span>

        {PRESETS.map((n) => (
          <button
            key={n}
            type="button"
            onClick={() => onChange(n)}
            className="btn-view-resume"
            style={{
              background: value === n ? "#1f7a5c" : undefined,
              color: value === n ? "white" : undefined,
            }}
          >
            {n}
          </button>
        ))}

        <input
          type="number"
          min="1"
          placeholder="Custom"
          value={customInput}
          onChange={(e) => setCustomInput(e.target.value)}
          onKeyDown={handleKeyDown}
          style={{
            width: "80px",
            padding: "6px 10px",
            border: "1px solid #e2e5ea",
            borderRadius: "6px",
            fontSize: "13px",
          }}
        />
        <button type="button" onClick={applyCustom} className="btn-secondary" style={{ padding: "6px 12px", fontSize: "13px" }}>
          Apply
        </button>

        {value !== "all" && (
          <button
            type="button"
            onClick={() => { onChange("all"); setCustomInput(""); }}
            className="btn-secondary"
            style={{ padding: "6px 12px", fontSize: "13px" }}
          >
            Show All
          </button>
        )}
      </div>

      <p style={{ fontSize: "12px", color: "#667079", marginTop: "6px" }}>
        {value === "all"
          ? `Showing all ${totalCount} candidates`
          : `Showing top ${Math.min(value, totalCount)} of ${totalCount} candidates`}
      </p>
    </div>
  );
}
