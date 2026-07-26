import { Clock, CheckSquare, MessageSquare } from "lucide-react";
import "./SummaryView.css";

function formatTime(seconds) {
  const m = Math.floor(seconds / 60);
  const s = Math.floor(seconds % 60);
  return `${m}:${s.toString().padStart(2, "0")}`;
}

export default function SummaryView({ result, onSeek }) {
  const { transcription, summary } = result;
  const { talking_points, action_items, meeting_date, summary: overview, model_used } = summary;

  return (
    <div className="summary">

      {/* Meta row */}
      <div className="summary__meta">
        {meeting_date && (
          <span className="summary__badge">{meeting_date}</span>
        )}
        <span className="summary__badge summary__badge--dim">
          {model_used}
        </span>
        <span className="summary__badge summary__badge--dim">
          {transcription.language.toUpperCase()} · {Math.round(transcription.duration_seconds / 60)} min
        </span>
      </div>

      {/* Overview */}
      <section className="summary__section">
        <p className="summary__overview">{overview}</p>
      </section>

      {/* Talking points */}
      {talking_points.length > 0 && (
        <section className="summary__section">
          <h2 className="summary__heading">
            <MessageSquare size={14} />
            Talking points
          </h2>

          <div className="summary__topics">
            {talking_points.map((tp, i) => (
              <div key={i} className="topic">
                <div className="topic__header">
                  <span className="topic__title">{tp.title}</span>
                  <button
                    className="topic__timestamp"
                    onClick={() => onSeek(tp.ref_start)}
                    title={`Jump to ${formatTime(tp.ref_start)}`}
                  >
                    <Clock size={11} />
                    {formatTime(tp.ref_start)}
                  </button>
                </div>
                <ul className="topic__bullets">
                  {tp.bullets.map((b, j) => (
                    <li key={j}>{b}</li>
                  ))}
                </ul>
              </div>
            ))}
          </div>
        </section>
      )}

      {/* Action items */}
      {action_items.length > 0 && (
        <section className="summary__section">
          <h2 className="summary__heading">
            <CheckSquare size={14} />
            Action items
          </h2>

          <ul className="summary__actions">
            {action_items.map((ai, i) => (
              <li key={i} className="action">
                <span className="action__task">{ai.task}</span>
                <span className="action__meta">
                  {ai.owner && <span className="action__owner">{ai.owner}</span>}
                  {ai.due   && <span className="action__due">{ai.due}</span>}
                </span>
              </li>
            ))}
          </ul>
        </section>
      )}

    </div>
  );
}
