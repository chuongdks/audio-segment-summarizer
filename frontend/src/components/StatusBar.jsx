import "./StatusBar.css";

const MESSAGES = {
  transcribing: "Transcribing audio…",
  summarizing:  "Summarizing with local AI…",
};

export default function StatusBar({ status, error, onRetry }) {
  if (status === "error") {
    return (
      <div className="status-bar status-bar--error">
        <span className="status-bar__dot" />
        <span className="status-bar__text">{error}</span>
        <button className="status-bar__retry" onClick={onRetry}>
          Try again
        </button>
      </div>
    );
  }

  return (
    <div className="status-bar">
      <span className="status-bar__spinner" />
      <span className="status-bar__text">{MESSAGES[status]}</span>
    </div>
  );
}
