import { useState } from "react";
import "./App.css";

const API_URL = "http://localhost:8000";

function App() {
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const [uploading, setUploading] = useState(false);
  const [uploadStatus, setUploadStatus] = useState(null);

  const sessionId = "default"; // single session for now

  async function sendQuestion() {
    if (!input.trim()) return;

    const question = input;
    setInput("");

    // Optimistically add the user's message to the chat immediately,
    // so the UI feels responsive while we wait for the backend
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
    } catch (error) {
      setMessages((prev) => [
        ...prev,
        {
          role: "assistant",
          text: "Error: could not reach the server.",
          sources: [],
        },
      ]);
    } finally {
      setLoading(false);
    }
  }

  function handleKeyDown(e) {
    if (e.key === "Enter") sendQuestion();
  }

  return (
    <div className="chat-container">
      <h1>DocuChat-AI</h1>

      <div className="upload-row">
        <label className="upload-button">
          {uploading ? "Uploading..." : "Upload PDF"}
          <input
            type="file"
            accept="application/pdf"
            onChange={handleFileUpload}
            disabled={uploading}
            style={{ display: "none" }}
          />
        </label>
        {uploadStatus && (
          <span className={`upload-status ${uploadStatus.type}`}>
            {uploadStatus.message}
          </span>
        )}
      </div>

      <div className="messages">
        {messages.map((msg, i) => (
          <div key={i} className={`message ${msg.role}`}>
            <p>{msg.text}</p>
            {msg.sources && msg.sources.length > 0 && (
              <div className="sources">
                {msg.sources.map((s, j) => (
                  <span key={j} className="source-tag">
                    {s.source} (p{s.pages})
                  </span>
                ))}
              </div>
            )}
          </div>
        ))}
        {loading && <div className="message assistant">Thinking...</div>}
      </div>

      <div className="input-row">
        <input
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={handleKeyDown}
          placeholder="Ask a question about your documents..."
          disabled={loading}
        />
        <button onClick={sendQuestion} disabled={loading}>
          Send
        </button>
      </div>
    </div>
  );

  async function handleFileUpload(e) {
    const file = e.target.files[0];
    if (!file) return;

    setUploading(true);
    setUploadStatus(null);

    const formData = new FormData();
    formData.append("file", file);

    try {
      const response = await fetch(`${API_URL}/upload`, {
        method: "POST",
        body: formData,
        // No Content-Type header here — the browser sets it automatically
        // for FormData, including the required multipart boundary.
      });

      const data = await response.json();

      if (data.error) {
        setUploadStatus({ type: "error", message: data.error });
      } else {
        setUploadStatus({
          type: "success",
          message: `"${data.filename}" indexed — ${data.chunks_added} chunks added.`,
        });
      }
    } catch (error) {
      setUploadStatus({
        type: "error",
        message: "Upload failed — could not reach the server.",
      });
    } finally {
      setUploading(false);
      e.target.value = ""; // reset the file input so the same file can be re-selected later
    }
  }
}

export default App;
