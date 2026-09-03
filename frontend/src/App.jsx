import { useState, useRef, useEffect } from "react";
import "./App.css";

const API_URL = "http://localhost:8000";

function App() {
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const [uploading, setUploading] = useState(false);
  const [uploadStatus, setUploadStatus] = useState(null);
  const [documents, setDocuments] = useState([]);
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const bottomRef = useRef(null);
  const sessionId = "default";

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, loading]);

  useEffect(() => {
    fetchDocuments();
  }, []);

  async function fetchDocuments() {
    try {
      const res = await fetch(`${API_URL}/documents`);
      const data = await res.json();
      setDocuments(data.documents);
    } catch {
      // sidebar just stays empty if this fails
    }
  }

  async function sendQuestion() {
    if (!input.trim()) return;
    const question = input;
    setInput("");
    setMessages((prev) => [...prev, { role: "user", text: question }]);
    setLoading(true);

    try {
      const response = await fetch(`${API_URL}/ask`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ question, session_id: sessionId, k: 5 }),
      });
      const data = await response.json();
      setMessages((prev) => [
        ...prev,
        { role: "assistant", text: data.answer, sources: data.sources },
      ]);
    } catch {
      setMessages((prev) => [
        ...prev,
        { role: "assistant", text: "Couldn't reach the server.", sources: [] },
      ]);
    } finally {
      setLoading(false);
    }
  }

  function handleKeyDown(e) {
    if (e.key === "Enter") sendQuestion();
  }

  async function handleFileUpload(e) {
    const file = e.target.files[0];
    if (!file) return;
    setUploading(true);
    setUploadStatus(null);

    const formData = new FormData();
    formData.append("file", file);

    try {
      const response = await fetch(`${API_URL}/upload`, { method: "POST", body: formData });
      const data = await response.json();
      if (data.error) {
        setUploadStatus({ type: "error", message: data.error });
      } else {
        setUploadStatus({ type: "success", message: `${data.filename} indexed` });
        fetchDocuments();
      }
    } catch {
      setUploadStatus({ type: "error", message: "Upload failed." });
    } finally {
      setUploading(false);
      e.target.value = "";
      setTimeout(() => setUploadStatus(null), 4000);
    }
  }

  return (
    <div className="app">
      {sidebarOpen && (
        <div className="sidebar-backdrop" onClick={() => setSidebarOpen(false)} />
      )}

      <aside className={`sidebar ${sidebarOpen ? "open" : ""}`}>
        <div className="sidebar-header">DocuChat</div>

        <label className="upload-trigger">
          {uploading ? "Uploading…" : "+ Add document"}
          <input
            type="file"
            accept="application/pdf"
            onChange={handleFileUpload}
            disabled={uploading}
            hidden
          />
        </label>

        {uploadStatus && (
          <div className={`upload-banner ${uploadStatus.type}`}>{uploadStatus.message}</div>
        )}

        <div className="doc-list-label">Indexed documents</div>
        <div className="doc-list">
          {documents.length === 0 && <div className="doc-empty">None yet</div>}
          {documents.map((doc, i) => (
            <div key={i} className="doc-item">
              <span className="doc-name">{doc.name}</span>
              <span className="doc-count">{doc.chunks}</span>
            </div>
          ))}
        </div>
      </aside>

      <main className="main">
        <div className="mobile-topbar">
          <button className="hamburger" onClick={() => setSidebarOpen(true)}>☰</button>
          <span className="mobile-brand">DocuChat</span>
        </div>

        <div className="thread">
          {messages.length === 0 && (
            <div className="empty-state">Ask a question about your documents.</div>
          )}

          {messages.map((msg, i) => (
            <div key={i} className={`turn ${msg.role}`}>
              <div className="turn-label">{msg.role === "user" ? "You" : "Answer"}</div>
              <div className="turn-text">{msg.text}</div>
              {msg.sources?.length > 0 && (
                <div className="sources">
                  {msg.sources.map((s, j) => (
                    <span key={j} className="source-chip">
                      {s.source} · p{s.pages}
                    </span>
                  ))}
                </div>
              )}
            </div>
          ))}

          {loading && (
            <div className="turn assistant">
              <div className="turn-label">Answer</div>
              <div className="turn-text thinking">Thinking…</div>
            </div>
          )}
          <div ref={bottomRef} />
        </div>

        <div className="composer-wrap">
          <div className="composer">
            <input
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={handleKeyDown}
              placeholder="Ask a question…"
              disabled={loading}
            />
            <button onClick={sendQuestion} disabled={loading || !input.trim()}>
              ↑
            </button>
          </div>
        </div>
      </main>
    </div>
  );
}

export default App;