import { useMemo, useState } from "react";

import { useRef } from "react";

const envApiBase = import.meta.env.VITE_API_BASE_URL;
const API_BASE = (envApiBase || window.location.origin).replace(/\/$/, "");
const MAX_FILES = 100;
const ACCEPTED_TYPES =
  ".png,.jpg,.jpeg,.gif,.svg,.ppt,.pptx,.PNG,.JPG,.JPEG,.GIF,.SVG,.PPT,.PPTX";

const PROMPT_CATEGORIES = [
  {
    id: "templates",
    label: "Templates",
    guidance:
      "generate metadata slide by slide; prioritize layout, structure, and usage tags.",
  },
  {
    id: "single-slides",
    label: "Single slides",
    guidance: "prioritize layout, structure, and presentation function.",
  },
  {
    id: "icons-vectors",
    label: "Icon & vectors",
    guidance:
      "prioritize representational meaning, search synonyms, and system style; avoid layout and structure tags.",
  },
  {
    id: "images",
    label: "Images",
    guidance: "prioritize visible subjects and scenes; avoid vector or layout logic.",
  },
  {
    id: "logos",
    label: "Logos",
    guidance: "prioritize mark type and color behavior; avoid usage or layout tags.",
  },
  {
    id: "elements",
    label: "Elements",
    guidance:
      "prioritize functional role (e.g. data indicator, process flow, map, frame, container, UI device, arrow, connector) over appearance.",
  },
];

const DEFAULT_CATEGORY = PROMPT_CATEGORIES[0].id;

const BASE_PROMPT = `IMAGE ASSET METADATA GENERATION PROMPT (GENERAL + ASSET GUIDANCE)
You are an AI assistant tasked with generating search-optimized metadata for visual assets used in a professional presentation asset library.

The system accepts uploads in the following formats: PNG, JPG, SVG, GIF, PPT, PPTX.
Assets may be icons, vectors, slides, templates, images, logos, or elements.

Shape

MANDATORY OUTPUT FORMAT

For single-asset files (icons, vectors, images, logos, elements, single-slide files):

Output exactly TWO lines only

Line 1 starts with: Asset Name:

Line 2 starts with: Tags:

No explanations, no extra lines, no formatting

For template files (PPT or PPTX containing multiple slides):

Treat the file as a template

Generate metadata slide by slide

For each slide, output exactly TWO lines using the same format

Repeat for all slides in order

Do not merge slides or add separators

Shape

ASSET NAME RULES

Provide asset names in BOTH English and Arabic

Use sentence case

Length: 3–4 words per language

Do NOT include the word slide, شريحة, or any variation

Names must be professional, neutral, and represent what the asset depicts, not how it is drawn

Shape

TAGS RULES

Single-line, comma-separated list

Tags must be bilingual (English + Arabic)

Minimum 30 tags per asset or per slide

Avoid redundancy

Tags must reflect what users would realistically search for, not descriptive prose

Shape

TAG GENERATION PRINCIPLES

Describe only what is visually recognizable

Use clear, searchable nouns for recognizable subjects or symbols

Visually recognizable symbols are not considered inferred meaning

Avoid interpretive, qualitative, or prose-like tags (e.g. clean lines, grid feel)

Avoid micro-level drawing descriptions

Shape

STYLE TAG GUIDANCE

Use atomic, structural, system-based style attributes that support filtering, such as:
outlined, filled, flat, isometric, 2D, 3D, single color, dual color, multicolor, monochrome, rounded corners, sharp edges

Avoid subjective or interpretive style language.

Shape

SEARCH VARIANTS & NUMBERING

Whenever a tag includes a concept that users may search in multiple common forms, include all standard variants, especially for numbers.

Examples:

single color, one color, 1 color, لون واحد, 1 لون

dual color, two color, 2 color, لونين, 2 لون

3d, three dimensions, ثلاثي الأبعاد

Apply this consistently wherever numbers or dimensions appear.

Shape

KEYWORD CONSISTENCY

When visually relevant, include functional presentation keywords such as:
cover, agenda, timeline, process, table, chart, diagram, dashboard, grid, framework, kpi, performance, data, infographic, comparison, hierarchy, funnel, matrix

Do not force keywords if they are not visually evident.

Shape

LOCATION & IDENTITY

Do not mention countries, cities, organizations, or identities unless explicitly visible.

Shape

TONE

Professional

Corporate

Brand-library ready

Search- and filter-optimized

ASSET-TYPE PRIORITIZATION GUIDANCE (APPLY AFTER THE ABOVE)

Use the following guidance only to prioritize tag types, not to hard-classify assets.

`;

const PROMPT_FOOTER =
  "\n\nThis guidance should shape emphasis, not introduce new tag types or override visual evidence.";

const buildPrompt = (categoryId) => {
  const category = PROMPT_CATEGORIES.find((item) => item.id === categoryId);
  const guidance = category ? category.guidance : PROMPT_CATEGORIES[0].guidance;
  return `${BASE_PROMPT}${guidance}${PROMPT_FOOTER}`;
};

const DEFAULT_PROMPT = buildPrompt(DEFAULT_CATEGORY);

async function downloadExcel(url, filename) {
  const response = await fetch(url);
  if (!response.ok) {
    throw new Error("Failed to download the Excel file.");
  }
  const blob = await response.blob();
  const objectUrl = URL.createObjectURL(blob);
  const link = document.createElement("a");
  link.href = objectUrl;
  link.download = filename;
  document.body.appendChild(link);
  link.click();
  link.remove();
  URL.revokeObjectURL(objectUrl);
}

function App() {
  const [files, setFiles] = useState([]);
  const [promptCategory, setPromptCategory] = useState(DEFAULT_CATEGORY);
  const [prompt, setPrompt] = useState(DEFAULT_PROMPT);
  const [status, setStatus] = useState("idle");
  const [error, setError] = useState("");
  const [results, setResults] = useState([]);
  const [downloadUrl, setDownloadUrl] = useState("");
  const [jobId, setJobId] = useState("");
  const [copiedKey, setCopiedKey] = useState("");
  const fileInputRef = useRef(null);

  const totalFiles = files.length;
  const totalResults = results.length;

  const statusLabel = useMemo(() => {
    if (status === "processing") return "Processing assets...";
    if (status === "done") return "Metadata ready.";
    if (status === "error") return "Something went wrong.";
    return "Ready to process.";
  }, [status]);

  const fileKey = (file) => `${file.name}-${file.size}-${file.lastModified}`;

  const handleFileChange = (event) => {
    const selected = Array.from(event.target.files || []);
    if (!selected.length) {
      return;
    }
    setFiles((prev) => {
      const mergedMap = new Map(prev.map((file) => [fileKey(file), file]));
      selected.forEach((file) => mergedMap.set(fileKey(file), file));
      const merged = Array.from(mergedMap.values());
      if (merged.length > MAX_FILES) {
        setError(`Please upload up to ${MAX_FILES} files at a time.`);
        return merged.slice(0, MAX_FILES);
      }
      setError("");
      return merged;
    });
    event.target.value = "";
  };

  const handleRemoveFile = (indexToRemove) => {
    setFiles((prev) => prev.filter((_, index) => index !== indexToRemove));
  };

  const handlePromptCategoryChange = (event) => {
    const nextCategory = event.target.value;
    setPromptCategory(nextCategory);
    setPrompt(buildPrompt(nextCategory));
  };

  const handleClearFiles = () => {
    setFiles([]);
    setError("");
    if (fileInputRef.current) {
      fileInputRef.current.value = "";
    }
  };

  const copyText = async (text, key) => {
    if (!text) {
      return;
    }
    try {
      if (navigator.clipboard?.writeText) {
        await navigator.clipboard.writeText(text);
      } else {
        const textarea = document.createElement("textarea");
        textarea.value = text;
        textarea.style.position = "fixed";
        textarea.style.opacity = "0";
        document.body.appendChild(textarea);
        textarea.focus();
        textarea.select();
        document.execCommand("copy");
        textarea.remove();
      }
      setCopiedKey(key);
      window.setTimeout(() => setCopiedKey(""), 1400);
    } catch {
      setCopiedKey("");
    }
  };

  const handleSubmit = async () => {
    if (!files.length) {
      setError("Please upload at least one file.");
      return;
    }

    setStatus("processing");
    setError("");
    setResults([]);
    setDownloadUrl("");
    setJobId("");

    const formData = new FormData();
    files.forEach((file) => formData.append("files", file));
    formData.append("prompt", prompt);

    try {
      const response = await fetch(`${API_BASE}/api/process`, {
        method: "POST",
        body: formData,
      });
      const text = await response.text();
      let data = null;
      if (text) {
        try {
          data = JSON.parse(text);
        } catch {
          if (!response.ok) {
            throw new Error(text || `Request failed (${response.status}).`);
          }
          throw new Error("Unexpected response format.");
        }
      } else if (!response.ok) {
        throw new Error(`Request failed (${response.status}).`);
      } else {
        throw new Error("Empty response from server.");
      }
      if (!response.ok) {
        throw new Error(data?.detail || "Processing failed.");
      }
      const url = `${API_BASE}${data.download_url}`;
      setResults(data.results || []);
      setDownloadUrl(url);
      setJobId(data.job_id || "");
      setStatus("done");
      if (data.job_id) {
        await downloadExcel(url, `asset_metadata_${data.job_id}.xlsx`);
      }
    } catch (err) {
      setError(err.message || "Processing failed.");
      setStatus("error");
    }
  };

  return (
    <div className="app">
      <header className="hero">
        <div>
          <span className="badge">Asset Metadata Studio</span>
          <h1>Visual asset naming, done fast.</h1>
          <p>
            Upload slides, images, icons, or PPT files. Generate bilingual names
            and tags with GPT-5.1 and export to Excel in one pass.
          </p>
        </div>
        <div className="hero-card">
          <div>
            <p className="hero-label">Batch limit</p>
            <p className="hero-value">{MAX_FILES} files</p>
          </div>
          <div>
            <p className="hero-label">Parallelism</p>
            <p className="hero-value">6 assets</p>
          </div>
        </div>
      </header>

      <main className="grid">
        <section className="card">
          <div className="card-title">
            <h2>Upload assets</h2>
            <span className="muted">PNG, JPG, SVG, GIF, PPT/PPTX</span>
          </div>
          <input
            type="file"
            multiple
            accept={ACCEPTED_TYPES}
            onChange={handleFileChange}
            ref={fileInputRef}
          />
          <div className="file-meta">
            <span>{totalFiles ? `${totalFiles} selected` : "No files yet"}</span>
            <div className="file-actions">
              {totalFiles ? (
                <button
                  type="button"
                  className="file-clear"
                  onClick={handleClearFiles}
                >
                  Remove all
                </button>
              ) : null}
              <span className="muted">Max {MAX_FILES}</span>
            </div>
          </div>
          <div className="file-list">
            {files.map((file, index) => (
              <div className="file-item" key={`${file.name}-${index}`}>
                <span className="pill">{file.name}</span>
                <button
                  type="button"
                  className="file-remove"
                  onClick={() => handleRemoveFile(index)}
                  aria-label={`Remove ${file.name}`}
                >
                  Remove
                </button>
              </div>
            ))}
          </div>
        </section>

        <section className="card">
          <div className="card-title">
            <h2>Prompt</h2>
            <span className="muted">Editable per batch</span>
          </div>
          <div className="prompt-controls">
            <label className="muted" htmlFor="prompt-category">
              Prompt category
            </label>
            <select
              id="prompt-category"
              value={promptCategory}
              onChange={handlePromptCategoryChange}
            >
              {PROMPT_CATEGORIES.map((category) => (
                <option key={category.id} value={category.id}>
                  {category.label}
                </option>
              ))}
            </select>
          </div>
          <textarea
            value={prompt}
            onChange={(event) => setPrompt(event.target.value)}
            rows={14}
          />
        </section>

        <section className="card actions">
          <div className="card-title">
            <h2>Generate</h2>
            <span className="muted">{statusLabel}</span>
          </div>
          {error ? <p className="error">{error}</p> : null}
          <div className="action-row">
            <button
              className="primary"
              onClick={handleSubmit}
              disabled={status === "processing"}
            >
              {status === "processing" ? "Working..." : "Generate metadata"}
            </button>
            {downloadUrl ? (
              <button
                className="ghost"
                onClick={() =>
                  downloadExcel(
                    downloadUrl,
                    jobId ? `asset_metadata_${jobId}.xlsx` : "asset_metadata.xlsx"
                  )
                }
              >
                Download Excel
              </button>
            ) : null}
          </div>
          <p className="muted">
            Each slide or image is processed independently to avoid mixed tags.
          </p>
        </section>

        {results.length ? (
          <section className="card results">
            <div className="card-title">
              <h2>Results</h2>
              <span className="muted">{totalResults} assets</span>
            </div>
            <div className="table-wrap">
              <table>
                <thead>
                  <tr>
                    <th>Uploaded</th>
                    <th>English name</th>
                    <th>Arabic name</th>
                    <th>Tags</th>
                  </tr>
                </thead>
                <tbody>
                  {results.map((result, index) => (
                    <tr key={`${result.uploaded}-${index}`}>
                      <td>{result.uploaded}</td>
                      <td>
                        <div className="cell">
                          <span>{result.english}</span>
                          <button
                            type="button"
                            className="copy-button"
                            onClick={() =>
                              copyText(result.english, `${index}-english`)
                            }
                          >
                            {copiedKey === `${index}-english`
                              ? "Copied"
                              : "Copy"}
                          </button>
                        </div>
                      </td>
                      <td>
                        <div className="cell">
                          <span>{result.arabic}</span>
                          <button
                            type="button"
                            className="copy-button"
                            onClick={() =>
                              copyText(result.arabic, `${index}-arabic`)
                            }
                          >
                            {copiedKey === `${index}-arabic`
                              ? "Copied"
                              : "Copy"}
                          </button>
                        </div>
                      </td>
                      <td>
                        <div className="cell">
                          <span>{result.tags}</span>
                          <button
                            type="button"
                            className="copy-button"
                            onClick={() => copyText(result.tags, `${index}-tags`)}
                          >
                            {copiedKey === `${index}-tags`
                              ? "Copied"
                              : "Copy"}
                          </button>
                        </div>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </section>
        ) : null}
      </main>
    </div>
  );
}

export default App;
