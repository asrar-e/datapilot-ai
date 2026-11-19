import {
  useEffect,
  useRef,
  useState,

} from "react";
import {
  Activity,
  BarChart3,
  Bell,
  ChevronRight,
  CircleHelp,
  Clock3,
  Database,
  FileSpreadsheet,
  LayoutDashboard,
  MessageSquareText,
  Search,
  Send,
  Settings2,
  Sparkles,
  Upload,
  Zap,
} from "lucide-react";
import {
  askDataset,
  getDatasets,
  uploadDataset,
  type Dataset,
  type QueryResponse,
} from "./lib/api";
import "./App.css";

const suggestions = [
  "Show total revenue",
  "Which region has the highest sales?",
  "Show the top 10 products",
  "Show monthly sales trends",
];

function App() {
  const [activePage, setActivePage] = useState("Overview");
  const [datasets, setDatasets] = useState<Dataset[]>([]);
  const [selectedDatasetId, setSelectedDatasetId] = useState("");
  const [question, setQuestion] = useState("");
  const [queryResponse, setQueryResponse] = useState<QueryResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [uploading, setUploading] = useState(false);
  const [error, setError] = useState("");
  const [apiOnline, setApiOnline] = useState(false);
  const fileInput = useRef<HTMLInputElement>(null);

  const selectedDataset = datasets.find(
    (dataset) => dataset.dataset_id === selectedDatasetId,
  );

  async function refreshDatasets() {
    try {
      const response = await getDatasets();
      setDatasets(response.datasets);
      setApiOnline(true);

      setSelectedDatasetId((current) => {
        if (current && response.datasets.some(
          (dataset) => dataset.dataset_id === current,
        )) {
          return current;
        }
        return response.datasets[0]?.dataset_id || "";
      });
    } catch (err) {
      setApiOnline(false);
      setError(
        err instanceof Error ? err.message : "Could not load datasets.",
      );
    }
  }

  useEffect(() => {
    void refreshDatasets();
  }, []);

  async function handleUpload(
    event: React.ChangeEvent<HTMLInputElement>,
  ) {
    const file = event.target.files?.[0];
    if (!file) return;

    setUploading(true);
    setError("");

    try {
      const response = await uploadDataset(file);
      await refreshDatasets();
      setSelectedDatasetId(response.dataset.dataset_id);
      setQueryResponse(null);
      setActivePage("Datasets");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Upload failed.");
    } finally {
      setUploading(false);
      event.target.value = "";
    }
  }

  async function submitQuestion() {
    if (!selectedDatasetId) {
      setError("Upload or select a dataset before asking a question.");
      setActivePage("Datasets");
      return;
    }

    if (question.trim().length < 3) {
      setError("Please enter a question with at least 3 characters.");
      return;
    }

    setLoading(true);
    setError("");
    setQueryResponse(null);

    try {
      const response = await askDataset(
        selectedDatasetId,
        question.trim(),
      );
      setQueryResponse(response);
      setActivePage("AI Analyst");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Query failed.");
    } finally {
      setLoading(false);
    }
  }

  const totalRows = datasets.reduce(
    (total, dataset) => total + Number(dataset.row_count || 0),
    0,
  );

  const resultRows = queryResponse?.result?.rows || [];
  const resultColumns = queryResponse?.result?.columns || [];

  function getCell(
    row: Record<string, unknown> | unknown[],
    column: string,
    index: number,
  ) {
    if (Array.isArray(row)) return row[index];
    return row[column];
  }

  return (
    <div className="app-shell">
      <aside className="sidebar">
        <div className="brand">
          <div className="brand-mark"><BarChart3 size={21} /></div>
          <div>
            <div className="brand-name">datapilot<span>.ai</span></div>
            <div className="brand-caption">INTELLIGENCE WORKSPACE</div>
          </div>
        </div>

        <div className="workspace-switch">
          <div className="workspace-avatar">D</div>
          <div className="workspace-copy">
            <strong>DataPilot workspace</strong>
            <span>Analytics environment</span>
          </div>
        </div>

        <div className="sidebar-navigation">
          <div className="nav-group">
            <div className="nav-label">WORKSPACE</div>
            {[
              { name: "Overview", icon: LayoutDashboard },
              { name: "AI Analyst", icon: Sparkles },
              { name: "Datasets", icon: Database },
            ].map(({ name, icon: Icon }) => (
              <button
                key={name}
                className={`nav-item ${activePage === name ? "active" : ""}`}
                onClick={() => setActivePage(name)}
              >
                <Icon size={17} />
                <span>{name}</span>
                {name === "AI Analyst" && <span className="nav-new">AI</span>}
              </button>
            ))}
          </div>

          <div className="nav-group">
            <div className="nav-label">MANAGEMENT</div>
            <button
              className={`nav-item ${activePage === "Query history" ? "active" : ""}`}
              onClick={() => setActivePage("Query history")}
            >
              <Clock3 size={17} /><span>Query history</span>
            </button>
            <button
              className={`nav-item ${activePage === "Settings" ? "active" : ""}`}
              onClick={() => setActivePage("Settings")}
            >
              <Settings2 size={17} /><span>Settings</span>
            </button>
          </div>
        </div>

        <div className="sidebar-bottom">
          <div className="usage-card">
            <div className="usage-heading">
              <span>Connected datasets</span>
              <span>{datasets.length}</span>
            </div>
            <div className="usage-track">
              <div className="usage-fill" />
            </div>
            <p>{totalRows.toLocaleString()} records available</p>
          </div>
          <div className="profile-button">
            <div className="profile-avatar">D</div>
            <div className="profile-copy">
              <strong>DataPilot Admin</strong>
              <span>Local workspace</span>
            </div>
          </div>
        </div>
      </aside>

      <main className="main-content">
        <header className="topbar">
          <div className="breadcrumb">
            <span>Workspace</span>
            <ChevronRight size={14} />
            <strong>{activePage}</strong>
          </div>
          <div className="topbar-actions">
            <div className="system-status">
              <span style={{ background: apiOnline ? "#32c98a" : "#e7a34b" }} />
              {apiOnline ? "API connected" : "API disconnected"}
            </div>
            <button className="icon-button" aria-label="Search">
              <Search size={18} />
            </button>
            <button className="icon-button" aria-label="Notifications">
              <Bell size={18} />
            </button>
            <button className="help-button">
              <CircleHelp size={16} /> Help center
            </button>
          </div>
        </header>

        <div className="page-content">
          {error && (
            <div className="live-error" role="alert">
              {error}
              <button onClick={() => setError("")}>Dismiss</button>
            </div>
          )}

          {activePage === "Overview" && (
            <>
              <section className="welcome-row">
                <div>
                  <div className="eyebrow">
                    <span className="eyebrow-dot" /> LIVE ANALYTICS WORKSPACE
                  </div>
                  <h1>Your data, <span>in focus.</span></h1>
                  <p className="welcome-subtitle">
                    Your analytics workspace, connected to PostgreSQL.
                  </p>
                </div>
                <div className="welcome-actions">
                  <button
                    className="secondary-button"
                    onClick={() => fileInput.current?.click()}
                    disabled={uploading}
                  >
                    <Upload size={16} />
                    {uploading ? "Uploading..." : "Upload data"}
                  </button>
                  <button
                    className="primary-button"
                    onClick={() => setActivePage("AI Analyst")}
                  >
                    <Sparkles size={16} /> Ask AI analyst
                  </button>
                </div>
              </section>

              <input
                ref={fileInput}
                type="file"
                accept=".csv,.xlsx"
                hidden
                onChange={handleUpload}
              />

              <section className="metrics-grid">
                <MetricCard
                  label="Total datasets"
                  value={datasets.length.toString()}
                  icon={<Database size={18} />}
                />
                <MetricCard
                  label="Records available"
                  value={totalRows.toLocaleString()}
                  icon={<FileSpreadsheet size={18} />}
                />
                <MetricCard
                  label="API status"
                  value={apiOnline ? "Connected" : "Offline"}
                  icon={<Zap size={18} />}
                />
                <MetricCard
                  label="Selected dataset"
                  value={selectedDataset?.dataset_name || "None"}
                  icon={<Activity size={18} />}
                />
              </section>

              <section className="panel datasets-panel">
                <div className="section-heading">
                  <div>
                    <h2>Your datasets</h2>
                    <p>Live data retrieved from the backend</p>
                  </div>
                  <button
                    className="text-link"
                    onClick={() => setActivePage("Datasets")}
                  >
                    View all <ChevronRight size={14} />
                  </button>
                </div>
                <DatasetTable datasets={datasets.slice(0, 5)} />
              </section>

              <section className="panel analyst-panel live-ask-panel">
                <div className="analyst-heading">
                  <div className="analyst-icon"><Sparkles size={19} /></div>
                  <div>
                    <div className="panel-kicker">YOUR AI COPILOT</div>
                    <h2>Ask your data</h2>
                  </div>
                </div>
                <DatasetSelector
                  datasets={datasets}
                  value={selectedDatasetId}
                  onChange={setSelectedDatasetId}
                />
                <QuestionInput
                  question={question}
                  setQuestion={setQuestion}
                  submitQuestion={submitQuestion}
                  loading={loading}
                />
              </section>
            </>
          )}

          {activePage === "Datasets" && (
            <section>
              <div className="welcome-row">
                <div>
                  <div className="eyebrow">DATA MANAGEMENT</div>
                  <h1>Your <span>datasets.</span></h1>
                  <p className="welcome-subtitle">
                    Upload, inspect and select your PostgreSQL datasets.
                  </p>
                </div>
                <button
                  className="primary-button"
                  onClick={() => fileInput.current?.click()}
                  disabled={uploading}
                >
                  <Upload size={16} />
                  {uploading ? "Uploading..." : "Upload dataset"}
                </button>
              </div>
              <input
                ref={fileInput}
                type="file"
                accept=".csv,.xlsx"
                hidden
                onChange={handleUpload}
              />
              <div className="panel datasets-panel">
                <div className="section-heading">
                  <div>
                    <h2>Uploaded data sources</h2>
                    <p>{datasets.length} datasets registered</p>
                  </div>
                  <button className="text-link" onClick={() => void refreshDatasets()}>
                    Refresh <Activity size={14} />
                  </button>
                </div>
                <DatasetTable
                  datasets={datasets}
                  selectedId={selectedDatasetId}
                  onSelect={setSelectedDatasetId}
                />
              </div>
            </section>
          )}

          {activePage === "AI Analyst" && (
            <section className="live-analyst-page">
              <div className="welcome-row">
                <div>
                  <div className="eyebrow">NATURAL LANGUAGE ANALYTICS</div>
                  <h1>AI <span>Analyst.</span></h1>
                  <p className="welcome-subtitle">
                    Ask a question. DataPilot generates, validates and executes SQL.
                  </p>
                </div>
              </div>

              <div className="panel live-query-panel">
                <div className="analyst-heading">
                  <div className="analyst-icon"><Sparkles size={19} /></div>
                  <div>
                    <div className="panel-kicker">ASK YOUR DATA</div>
                    <h2>What would you like to know?</h2>
                  </div>
                </div>

                <DatasetSelector
                  datasets={datasets}
                  value={selectedDatasetId}
                  onChange={(id) => {
                    setSelectedDatasetId(id);
                    setQueryResponse(null);
                  }}
                />

                {selectedDataset && (
                  <p className="live-dataset-info">
                    {selectedDataset.original_filename} ·{" "}
                    {selectedDataset.row_count.toLocaleString()} rows ·{" "}
                    {selectedDataset.column_count} columns
                  </p>
                )}

                <QuestionInput
                  question={question}
                  setQuestion={setQuestion}
                  submitQuestion={submitQuestion}
                  loading={loading}
                />

                <div className="suggestions live-suggestions">
                  {suggestions.map((item) => (
                    <button key={item} onClick={() => setQuestion(item)}>
                      {item}<ChevronRight size={14} />
                    </button>
                  ))}
                </div>
              </div>

              {loading && (
                <div className="panel live-result-panel">
                  <p>Generating SQL and executing your query...</p>
                </div>
              )}

              {queryResponse && (
                <>
                  <div className="panel live-result-panel">
                    <div className="section-heading">
                      <div>
                        <div className="panel-kicker">QUERY RESULT</div>
                        <h2>{queryResponse.question}</h2>
                        <p>
                          {queryResponse.result.row_count} rows returned
                        </p>
                      </div>
                      <span className="status-ready">Successful</span>
                    </div>

                    {queryResponse.generated_query.explanation && (
                      <p className="live-explanation">
                        {queryResponse.generated_query.explanation}
                      </p>
                    )}

                    <div className="live-table-wrap">
                      <table className="live-results-table">
                        <thead>
                          <tr>
                            {resultColumns.map((column) => (
                              <th key={column}>{column}</th>
                            ))}
                          </tr>
                        </thead>
                        <tbody>
                          {resultRows.map((row, rowIndex) => (
                            <tr key={rowIndex}>
                              {resultColumns.map((column, columnIndex) => (
                                <td key={column}>
                                  {String(
                                    getCell(row, column, columnIndex) ?? "",
                                  )}
                                </td>
                              ))}
                            </tr>
                          ))}
                        </tbody>
                      </table>
                    </div>
                  </div>

                  <div className="panel live-sql-panel">
                    <div className="section-heading">
                      <div>
                        <div className="panel-kicker">GENERATED SQL</div>
                        <h2>SQL statement</h2>
                      </div>
                      <button
                        className="text-link"
                        onClick={() => {
                          void navigator.clipboard.writeText(
                            queryResponse.generated_query.sql,
                          );
                        }}
                      >
                        Copy SQL
                      </button>
                    </div>
                    <pre className="live-sql-code">
                      <code>{queryResponse.generated_query.sql}</code>
                    </pre>
                    <p className="input-hint">
                      SQL is validated by the backend before execution.
                    </p>
                  </div>
                </>
              )}
            </section>
          )}

          {activePage === "Query history" && (
            <section>
              <div className="welcome-row">
                <div>
                  <div className="eyebrow">WORKSPACE</div>
                  <h1>Query <span>history.</span></h1>
                  <p className="welcome-subtitle">
                    Query history persistence will be added in the next backend phase.
                  </p>
                </div>
              </div>
              <div className="panel live-result-panel">
                <MessageSquareText size={22} />
                <p>Previous queries are not currently stored by the backend.</p>
              </div>
            </section>
          )}

          {activePage === "Settings" && (
            <section>
              <div className="welcome-row">
                <div>
                  <div className="eyebrow">CONFIGURATION</div>
                  <h1>Workspace <span>settings.</span></h1>
                  <p className="welcome-subtitle">
                    Current local development configuration.
                  </p>
                </div>
              </div>
              <div className="panel live-result-panel">
                <p>Backend API: {import.meta.env.VITE_API_BASE_URL || "http://127.0.0.1:8000"}</p>
                <p>Connection: {apiOnline ? "Connected" : "Disconnected"}</p>
                <p>Datasets: {datasets.length}</p>
              </div>
            </section>
          )}

          <footer className="page-footer">
            <span>© 2026 DataPilot AI</span>
            <span><i /> Built for smarter decisions</span>
            <span>v0.2.0 · Connected preview</span>
          </footer>
        </div>
      </main>
    </div>
  );
}

function MetricCard({
  label,
  value,
  icon,
}: {
  label: string;
  value: string;
  icon: React.ReactNode;
}) {
  return (
    <div className="metric-card">
      <div className="metric-top">
        <span>{label}</span>
        <div className="metric-icon">{icon}</div>
      </div>
      <div className="metric-value live-metric-value">{value}</div>
    </div>
  );
}

function DatasetSelector({
  datasets,
  value,
  onChange,
}: {
  datasets: Dataset[];
  value: string;
  onChange: (value: string) => void;
}) {
  return (
    <div className="live-field">
      <label htmlFor="dataset-select">Active dataset</label>
      <select
        id="dataset-select"
        value={value}
        onChange={(event) => onChange(event.target.value)}
      >
        <option value="">Select a dataset</option>
        {datasets.map((dataset) => (
          <option key={dataset.dataset_id} value={dataset.dataset_id}>
            {dataset.dataset_name} · {dataset.row_count.toLocaleString()} rows
          </option>
        ))}
      </select>
    </div>
  );
}

function QuestionInput({
  question,
  setQuestion,
  submitQuestion,
  loading,
}: {
  question: string;
  setQuestion: (value: string) => void;
  submitQuestion: () => void;
  loading: boolean;
}) {
  return (
    <div className="question-input">
      <input
        value={question}
        onChange={(event) => setQuestion(event.target.value)}
        onKeyDown={(event) => {
          if (event.key === "Enter" && !event.shiftKey) {
            event.preventDefault();
            submitQuestion();
          }
        }}
        placeholder="Ask anything about your data..."
      />
      <button
        aria-label="Send question"
        onClick={submitQuestion}
        disabled={loading}
      >
        <Send size={16} />
      </button>
    </div>
  );
}

function DatasetTable({
  datasets,
  selectedId,
  onSelect,
}: {
  datasets: Dataset[];
  selectedId?: string;
  onSelect?: (id: string) => void;
}) {
  if (datasets.length === 0) {
    return <p className="live-empty">No datasets uploaded yet. Upload a CSV or XLSX file to get started.</p>;
  }

  return (
    <div className="dataset-table">
      <div className="table-header">
        <span>DATASET</span>
        <span>ROWS</span>
        <span>FILE TYPE</span>
        <span>STATUS</span>
        <span />
      </div>
      {datasets.map((dataset) => (
        <button
          type="button"
          className={`dataset-row live-dataset-row ${
            selectedId === dataset.dataset_id ? "selected" : ""
          }`}
          key={dataset.dataset_id}
          onClick={() => onSelect?.(dataset.dataset_id)}
        >
          <div className="dataset-name">
            <div className="file-icon"><FileSpreadsheet size={17} /></div>
            <div>
              <strong>{dataset.dataset_name}</strong>
              <span>{dataset.original_filename}</span>
            </div>
          </div>
          <span className="table-value">
            {dataset.row_count.toLocaleString()}
          </span>
          <span className="table-muted">
            {dataset.file_type.toUpperCase()}
          </span>
          <span className="status-ready">
            <i /> {dataset.ingestion_status}
          </span>
          <span className="table-muted">
            {new Date(dataset.uploaded_at).toLocaleDateString()}
          </span>
        </button>
      ))}
    </div>
  );
}

export default App;
