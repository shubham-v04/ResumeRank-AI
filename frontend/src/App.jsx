import { useEffect, useRef, useState } from "react";
import JobDescriptionInput from "./components/JobDescriptionInput";
import SkillsInput from "./components/SkillsInput";
import ExperienceInput from "./components/ExperienceInput";
import ResumeUpload from "./components/ResumeUpload";
import AnalyzeButton from "./components/AnalyzeButton";
import ResultsTable from "./components/ResultsTable";
import TopNFilter from "./components/TopNFilter";
import DownloadButtons from "./components/DownloadButtons";
import ErrorBanner from "./components/ErrorBanner";
import ResetButton from "./components/ResetButton";
import { analyzeResumes, getAnalysisProgress } from "./api";

const DRAFT_KEY = "resumerank_draft";
const POLL_INTERVAL_MS = 800;

function loadDraft() {
  try {
    const raw = localStorage.getItem(DRAFT_KEY);
    return raw ? JSON.parse(raw) : null;
  } catch {
    return null;
  }
}

export default function App() {
  const draft = loadDraft();

  const [jobDescription, setJobDescription] = useState(draft?.jobDescription || "");
  const [skills, setSkills] = useState(draft?.skills || []);
  const [minExperience, setMinExperience] = useState(draft?.minExperience || "");
  const [files, setFiles] = useState([]);
  const [results, setResults] = useState([]);
  const [topN, setTopN] = useState("all");
  const [loading, setLoading] = useState(false);
  const [progress, setProgress] = useState(null); // { total, completed } while an analysis runs
  const [error, setError] = useState("");
  const pollRef = useRef(null);

  useEffect(() => {
    localStorage.setItem(
      DRAFT_KEY,
      JSON.stringify({ jobDescription, skills, minExperience })
    );
  }, [jobDescription, skills, minExperience]);

  // Poll the backend's progress endpoint while (and only while) loading
  // is true - starts/stops automatically as loading changes.
  useEffect(() => {
    if (!loading) {
      setProgress(null);
      return;
    }

    const poll = async () => {
      const data = await getAnalysisProgress();
      if (data) setProgress(data);
    };

    poll(); // fetch immediately, don't wait for the first interval tick
    pollRef.current = setInterval(poll, POLL_INTERVAL_MS);

    return () => clearInterval(pollRef.current);
  }, [loading]);

  const handleFilesChange = (newFiles, rejectedCount) => {
    setFiles(newFiles);
    if (rejectedCount) {
      setError(`${rejectedCount} file(s) were skipped - only PDF and Word (.docx) files are supported.`);
    }
  };

  const handleAnalyze = async () => {
    setError("");

    if (!jobDescription.trim()) {
      setError("Please enter a job description first.");
      return;
    }
    if (files.length === 0) {
      setError("Please upload at least one resume.");
      return;
    }

    setLoading(true);
    try {
      const data = await analyzeResumes(jobDescription, files, skills, minExperience);
      setResults(data.results);
      setTopN("all");

      const notes = [];
      if (data.skipped && data.skipped.length > 0) {
        notes.push(`${data.skipped.length} file(s) could not be read: ${data.skipped.join(", ")}`);
      }
      if (data.non_resume_files && data.non_resume_files.length > 0) {
        notes.push(`${data.non_resume_files.length} file(s) didn't look like resumes and were excluded from ranking: ${data.non_resume_files.join(", ")}`);
      }
      if (notes.length > 0) {
        setError(`Note: ${notes.join(" | ")}`);
      }
    } catch (err) {
      setError(err.message);
      setResults([]);
    } finally {
      setLoading(false);
    }
  };

  const handleReset = () => {
    setJobDescription("");
    setSkills([]);
    setMinExperience("");
    setFiles([]);
    setResults([]);
    setTopN("all");
    setError("");
    localStorage.removeItem(DRAFT_KEY);
  };

  const displayedResults = topN === "all" ? results : results.slice(0, topN);

  const loadingMessage =
    progress && progress.total > 0
      ? `Analyzing ${progress.completed} of ${progress.total} resumes...`
      : "Reading and scoring resumes, please wait...";

  return (
    <div className="page">
      <header className="site-header">
        <div className="inner-wrap">
          <span className="wordmark">ResumeRank</span>
          <span className="tagline">Rank resumes against a job in minutes</span>
        </div>
      </header>

      <section className="hero">
        <h1>Find your best-fit candidates faster</h1>
        <p>Paste a job description, drop in resumes, and get a scored, ranked shortlist you can export.</p>
      </section>

      <main>
        <div className="tool-panel">
          <JobDescriptionInput value={jobDescription} onChange={setJobDescription} />
          <SkillsInput skills={skills} onChange={setSkills} />
          <ExperienceInput value={minExperience} onChange={setMinExperience} />
          <ResumeUpload files={files} onChange={handleFilesChange} />

          <div className="button-row">
            <AnalyzeButton onClick={handleAnalyze} loading={loading} />
            <ResetButton onClick={handleReset} />
          </div>

          {loading && (
            <div style={{ marginTop: "18px" }}>
              <p className="loading-text" style={{ marginBottom: "6px" }}>{loadingMessage}</p>
              {progress && progress.total > 0 && (
                <div style={{ background: "#eef0f2", borderRadius: "6px", height: "8px", overflow: "hidden" }}>
                  <div
                    style={{
                      width: `${(progress.completed / progress.total) * 100}%`,
                      background: "#1f7a5c",
                      height: "100%",
                      transition: "width 0.3s ease",
                    }}
                  />
                </div>
              )}
            </div>
          )}

          <ErrorBanner message={error} />

          <TopNFilter value={topN} onChange={setTopN} totalCount={results.length} />
          <ResultsTable results={displayedResults} />
          <DownloadButtons visible={results.length > 0} topN={topN} />
        </div>
      </main>

      <footer className="site-footer">
        ResumeRank - a personal project. Runs entirely on your machine, no data leaves your laptop.
      </footer>
    </div>
  );
}
