const API_BASE = "http://localhost:8000";

export async function analyzeResumes(jobDescription, files, skills = [], minExperience = "") {
  const formData = new FormData();
  formData.append("job_description", jobDescription);
  formData.append("required_skills", skills.join(","));

  if (minExperience !== "" && minExperience !== null) {
    formData.append("min_experience", minExperience);
  }

  for (const file of files) {
    formData.append("resume_files", file);
  }

  const response = await fetch(`${API_BASE}/analyze`, {
    method: "POST",
    body: formData,
  });

  const data = await response.json();

  if (!response.ok) {
    throw new Error(data.error || "Something went wrong while analyzing resumes.");
  }

  return data;
}

export async function getAnalysisProgress() {
  const response = await fetch(`${API_BASE}/analyze/progress`);
  if (!response.ok) return null;
  return response.json();
}

export function downloadExcelUrl(topN = "all") {
  const query = topN === "all" ? "" : `?limit=${topN}`;
  return `${API_BASE}/download/excel${query}`;
}

export function downloadPdfUrl(topN = "all") {
  const query = topN === "all" ? "" : `?limit=${topN}`;
  return `${API_BASE}/download/pdf${query}`;
}
