import { useState } from "react";
import { Clock, CheckSquare, Square, MessageSquare, ChevronRight } from "lucide-react";
import "./SummaryView.css";

function formatTime(seconds) {
  const m = Math.floor(seconds / 60);
  const s = Math.floor(seconds % 60);
  return `${m}:${s.toString().padStart(2, "0")}`;
}

// Clickable timestamp pill
function TimestampLink({ seconds, onSeek }) {
  if (seconds === 0) return null;
  return (
    <button
      className="timestamp-link"
      onClick={() => onSeek(seconds)}
      title={`Jump to ${formatTime(seconds)}`}
    >
      <Clock size={10} />
      {formatTime(seconds)}
    </button>
  );
}

// Bullet list shared by sections and subsections
function BulletList({ bullets }) {
  if (!bullets?.length) return null;
  return (
    <ul className="bullet-list">
      {bullets.map((b, i) => (
        <li key={i}>{b}</li>
      ))}
    </ul>
  );
}

// A collapsible subsection inside a talking point
function SubSection({ sub, onSeek }) {
  const [open, setOpen] = useState(true);
  return (
    <div className="subsection">
      <button
        className="subsection__header"
        onClick={() => setOpen((o) => !o)}
      >
        <ChevronRight
          size={12}
          className={`subsection__chevron ${open ? "subsection__chevron--open" : ""}`}
        />
        <span className="subsection__title">{sub.title}</span>
        <TimestampLink seconds={sub.ref_start} onSeek={onSeek} />
      </button>
      {open && <BulletList bullets={sub.bullets} />}
    </div>
  );
}

// A top-level talking point section
function TalkingPointCard({ tp, onSeek }) {
  const [open, setOpen] = useState(true);
  const hasContent = tp.bullets?.length > 0 || tp.subsections?.length > 0;

  return (
    <div className="topic">
      <button
        className="topic__header"
        onClick={() => setOpen((o) => !o)}
      >
        <ChevronRight
          size={13}
          className={`topic__chevron ${open ? "topic__chevron--open" : ""}`}
        />
        <span className="topic__title">{tp.title}</span>
        <TimestampLink seconds={tp.ref_start} onSeek={onSeek} />
      </button>

      {open && hasContent && (
        <div className="topic__body">
          {/* Top-level bullets (points that don't belong to a subsection) */}
          <BulletList bullets={tp.bullets} />

          {/* Nested subsections */}
          {tp.subsections?.map((sub, i) => (
            <SubSection key={i} sub={sub} onSeek={onSeek} />
          ))}
        </div>
      )}
    </div>
  );
}

// A single action item with a checkbox
function ActionRow({ item, onToggle }) {
  return (
    <li className={`action ${item.completed ? "action--done" : ""}`}>
      <button
        className="action__checkbox"
        onClick={onToggle}
        aria-label={item.completed ? "Mark incomplete" : "Mark complete"}
      >
        {item.completed
          ? <CheckSquare size={15} />
          : <Square size={15} />
        }
      </button>

      <span className="action__task">{item.task}</span>

      <span className="action__meta">
        {item.owner && <span className="action__owner">{item.owner}</span>}
        {item.due   && <span className="action__due">{item.due}</span>}
      </span>
    </li>
  );
}

// ── Main export ───────────────────────────────────────────────────────────────

export default function SummaryView({ result, onSeek }) {
  const { transcription, summary } = result;
  const { talking_points, meeting_date, summary: overview, model_used } = summary;

  // Local checkbox state — starts from what the model returned
  const [actionItems, setActionItems] = useState(summary.action_items);

  function toggleAction(index) {
    setActionItems((prev) =>
      prev.map((ai, i) =>
        i === index ? { ...ai, completed: !ai.completed } : ai
      )
    );
  }

  const doneCount = actionItems.filter((a) => a.completed).length;

  return (
    <div className="summary">

      {/* Meta badges */}
      <div className="summary__meta">
        {meeting_date && (
          <span className="summary__badge">{meeting_date}</span>
        )}
        <span className="summary__badge summary__badge--dim">{model_used}</span>
        <span className="summary__badge summary__badge--dim">
          {transcription.language.toUpperCase()} · {Math.round(transcription.duration_seconds / 60)} min
        </span>
      </div>

      {/* Overview paragraph */}
      <section className="summary__section">
        <p className="summary__overview">{overview}</p>
      </section>

      {/* Talking points */}
      {talking_points.length > 0 && (
        <section className="summary__section">
          <h2 className="summary__heading">
            <MessageSquare size={13} />
            Talking points
          </h2>
          <div className="summary__topics">
            {talking_points.map((tp, i) => (
              <TalkingPointCard key={i} tp={tp} onSeek={onSeek} />
            ))}
          </div>
        </section>
      )}

      {/* Action items */}
      {actionItems.length > 0 && (
        <section className="summary__section">
          <h2 className="summary__heading">
            <CheckSquare size={13} />
            Action items
            <span className="summary__action-count">
              {doneCount}/{actionItems.length}
            </span>
          </h2>
          <ul className="summary__actions">
            {actionItems.map((ai, i) => (
              <ActionRow key={i} item={ai} onToggle={() => toggleAction(i)} />
            ))}
          </ul>
        </section>
      )}

    </div>
  );
}
