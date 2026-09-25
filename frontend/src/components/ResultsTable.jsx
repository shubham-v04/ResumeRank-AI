import { useState, Fragment } from "react";

const API_BASE = "http://localhost:8000";

const badgeStyle = {
  display: "inline-block",
  fontSize: "11px",
  padding: "2px 8px",
  borderRadius: "10px",
  marginRight: "4px",
  marginTop: "4px",
};

function SkillCell({ row }) {
  if (row.skill_match_percent === null || row.skill_match_percent === undefined) {
    return <span style={{ color: "#aaa" }}>-</span>;
  }
  const total = row.skills_matched.length + row.skills_missing.length;
  return (
    <div>
      <div>{row.skill_match_percent}% ({row.skills_matched.length}/{total})</div>
      {row.skills_missing.length > 0 && (
        <div>
          {row.skills_missing.map((skill) => (
            <span key={skill} style={{ ...badgeStyle, background: "#fee2e2", color: "#991b1b" }}>
              {skill}
            </span>
          ))}
        </div>
      )}
    </div>
  );
}

function ExperienceCell({ row }) {
  if (row.years_experience === null || row.years_experience === undefined) {
    return <span style={{ color: "#aaa" }}>Unknown</span>;
  }
  if (row.meets_experience === null || row.meets_experience === undefined) {
    return <span>{row.years_experience} yrs</span>;
  }
  const color = row.meets_experience ? "#16a34a" : "#b91c1c";
  const icon = row.meets_experience ? "\u2713" : "\u2717";
  return (
    <span style={{ color, fontWeight: 500 }}>
      {icon} {row.years_experience} yrs
    </span>
  );
}

function AiInsightsPanel({ row }) {
  const hasAnyInsights = row.ai_summary || row.ai_strengths?.length || row.ai_concerns?.length || row.skills_detected?.length || row.education;

  if (!hasAnyInsights) {
    return (
      <div style={{ padding: "14px 20px", color: "#888", fontSize: "13px" }}>
        No AI insights available for this candidate.
      </div>
    );
  }

  return (
    <div style={{ padding: "16px 20px", background: "#fafcfb", display: "grid", gap: "14px" }}>
      {row.ai_summary && (
        <div>
          <div style={insightLabelStyle}>Summary</div>
          <div style={{ fontSize: "14px" }}>{row.ai_summary}</div>
        </div>
      )}

      <div style={{ display: "flex", gap: "32px", flexWrap: "wrap" }}>
        {row.ai_strengths?.length > 0 && (
          <div>
            <div style={insightLabelStyle}>Strengths</div>
            <ul style={{ margin: "4px 0 0", paddingLeft: "18px", fontSize: "13px" }}>
              {row.ai_strengths.map((s, i) => <li key={i} style={{ color: "#166534" }}>{s}</li>)}
            </ul>
          </div>
        )}

        {row.ai_concerns?.length > 0 && (
          <div>
            <div style={insightLabelStyle}>Concerns</div>
            <ul style={{ margin: "4px 0 0", paddingLeft: "18px", fontSize: "13px" }}>
              {row.ai_concerns.map((c, i) => <li key={i} style={{ color: "#991b1b" }}>{c}</li>)}
            </ul>
          </div>
        )}
      </div>

      {row.skills_detected?.length > 0 && (
        <div>
          <div style={insightLabelStyle}>Detected Skills</div>
          <div style={{ marginTop: "4px" }}>
            {row.skills_detected.map((skill) => (
              <span key={skill} style={{ ...badgeStyle, background: "#e4f2ec", color: "#145c44" }}>
                {skill}
              </span>
            ))}
          </div>
        </div>
      )}

      {row.education && (
        <div>
          <div style={insightLabelStyle}>Education</div>
          <div style={{ fontSize: "13px" }}>{row.education}</div>
        </div>
      )}
    </div>
  );
}

const insightLabelStyle = {
  fontSize: "11px",
  fontWeight: 700,
  textTransform: "uppercase",
  letterSpacing: "0.03em",
  color: "#667079",
};

export default function ResultsTable({ results }) {
  const [expandedIndex, setExpandedIndex] = useState(null);

  if (results.length === 0) return null;

  const toggleRow = (i) => {
    setExpandedIndex(expandedIndex === i ? null : i);
  };

  return (
    <table>
      <thead>
        <tr>
          <th>Rank</th>
          <th>Name</th>
          <th>Email</th>
          <th>Match Score</th>
          <th>Skill Match</th>
          <th>Experience</th>
          <th>Resume</th>
          <th>AI Insights</th>
        </tr>
      </thead>
      <tbody>
        {results.map((r, i) => (
          <Fragment key={r.filename + i}>
            <tr>
              <td>{i + 1}</td>
              <td>{r.name}</td>
              <td>{r.email}</td>
              <td>{r.score}%</td>
              <td><SkillCell row={r} /></td>
              <td><ExperienceCell row={r} /></td>
              <td>
                <a href={`${API_BASE}${r.resume_url}`} target="_blank" rel="noopener noreferrer" className="btn-view-resume" title={r.filename}>
                  View
                </a>
              </td>
              <td>
                <button
                  type="button"
                  onClick={() => toggleRow(i)}
                  className="btn-view-resume"
                  style={{ background: expandedIndex === i ? "#1f7a5c" : undefined, color: expandedIndex === i ? "white" : undefined }}
                >
                  {expandedIndex === i ? "Hide" : "Details"}
                </button>
              </td>
            </tr>
            {expandedIndex === i && (
              <tr>
                <td colSpan={8} style={{ padding: 0 }}>
                  <AiInsightsPanel row={r} />
                </td>
              </tr>
            )}
          </Fragment>
        ))}
      </tbody>
    </table>
  );
}
