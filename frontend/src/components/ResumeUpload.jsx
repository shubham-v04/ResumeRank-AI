import { useRef, useState } from "react";

const ALLOWED_EXTENSIONS = [".pdf", ".docx"];

function isAllowed(file) {
  return ALLOWED_EXTENSIONS.some((ext) => file.name.toLowerCase().endsWith(ext));
}

function formatTotalSize(files) {
  const totalBytes = files.reduce((sum, f) => sum + f.size, 0);
  if (totalBytes < 1024 * 1024) return `${(totalBytes / 1024).toFixed(0)} KB`;
  return `${(totalBytes / (1024 * 1024)).toFixed(1)} MB`;
}

export default function ResumeUpload({ files, onChange }) {
  const [isDragging, setIsDragging] = useState(false);
  const [showList, setShowList] = useState(false);
  const inputRef = useRef(null);

  const addFiles = (newFiles) => {
    const incoming = Array.from(newFiles);
    const valid = incoming.filter(isAllowed);
    const rejectedCount = incoming.length - valid.length;

    const existingNames = new Set(files.map((f) => f.name));
    const merged = [...files, ...valid.filter((f) => !existingNames.has(f.name))];
    onChange(merged, rejectedCount);
  };

  const handleDrop = (e) => {
    e.preventDefault();
    setIsDragging(false);
    addFiles(e.dataTransfer.files);
  };

  const removeFile = (nameToRemove) => {
    onChange(files.filter((f) => f.name !== nameToRemove));
  };

  const clearAll = () => {
    onChange([]);
    setShowList(false);
  };

  return (
    <div>
      <label>Upload Resumes (PDF or Word, multiple allowed)</label>
      <div
        onDragOver={(e) => {
          e.preventDefault();
          setIsDragging(true);
        }}
        onDragLeave={() => setIsDragging(false)}
        onDrop={handleDrop}
        onClick={() => inputRef.current.click()}
        style={{
          border: `2px dashed ${isDragging ? "#1f7a5c" : "#ccc"}`,
          borderRadius: "8px",
          padding: "24px",
          textAlign: "center",
          cursor: "pointer",
          background: isDragging ? "#e4f2ec" : "#fafafa",
          transition: "border-color 0.2s, background-color 0.2s",
        }}
      >
        <p style={{ margin: 0, color: "#555" }}>
          Drag and drop resumes here, or click to browse
        </p>
        <input
          ref={inputRef}
          type="file"
          accept=".pdf,.docx"
          multiple
          style={{ display: "none" }}
          onChange={(e) => addFiles(e.target.files)}
        />
      </div>

      {files.length > 0 && (
        <div style={{ marginTop: "10px" }}>
          <div
            style={{
              display: "flex",
              justifyContent: "space-between",
              alignItems: "center",
              padding: "8px 12px",
              background: "#f4f5f7",
              borderRadius: "6px",
              fontSize: "13px",
            }}
          >
            <span>
              <strong>{files.length}</strong> file{files.length !== 1 ? "s" : ""} selected
              <span style={{ color: "#888" }}> ({formatTotalSize(files)} total)</span>
            </span>
            <span style={{ display: "flex", gap: "12px" }}>
              <button
                type="button"
                onClick={() => setShowList(!showList)}
                style={{ background: "none", border: "none", color: "#1f7a5c", cursor: "pointer", fontSize: "13px", fontWeight: 600, padding: 0 }}
              >
                {showList ? "Hide files" : "View files"}
              </button>
              <button
                type="button"
                onClick={clearAll}
                style={{ background: "none", border: "none", color: "#b91c1c", cursor: "pointer", fontSize: "13px", padding: 0 }}
              >
                Clear all
              </button>
            </span>
          </div>

          {showList && (
            <ul style={{ listStyle: "none", padding: 0, marginTop: "6px", maxHeight: "280px", overflowY: "auto" }}>
              {files.map((file) => (
                <li
                  key={file.name}
                  style={{
                    display: "flex",
                    justifyContent: "space-between",
                    alignItems: "center",
                    padding: "6px 10px",
                    background: "#fafcfb",
                    borderRadius: "6px",
                    marginBottom: "4px",
                    fontSize: "13px",
                  }}
                >
                  <span>
                    {file.name} <span style={{ color: "#888" }}>({(file.size / 1024).toFixed(0)} KB)</span>
                  </span>
                  <button
                    type="button"
                    onClick={() => removeFile(file.name)}
                    style={{ background: "none", border: "none", color: "#b91c1c", cursor: "pointer", fontSize: "13px" }}
                  >
                    Remove
                  </button>
                </li>
              ))}
            </ul>
          )}
        </div>
      )}
    </div>
  );
}
