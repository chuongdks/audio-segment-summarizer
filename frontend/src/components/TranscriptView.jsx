import { useRef, useEffect } from "react";
import "./TranscriptView.css";

function formatTime(seconds) {
  const m = Math.floor(seconds / 60);
  const s = Math.floor(seconds % 60);
  return `${m}:${s.toString().padStart(2, "0")}`;
}

/**
 * Finds the index of the segment that is currently playing.
 * A segment is "active" if currentTime falls within its start..end range.
 * Falls back to the last segment whose start <= currentTime.
 */
function getActiveIndex(segments, currentTime) {
  let active = 0;
  for (let i = 0; i < segments.length; i++) {
    if (segments[i].start <= currentTime) {
      active = i;
    } else {
      break;
    }
  }
  return active;
}

export default function TranscriptView({ segments, currentTime, onSeek }) {
  const rowRefs = useRef([]);          // one ref per segment row
  const lastScrolled = useRef(-1);     // avoid redundant scrolls

  const activeIndex = getActiveIndex(segments, currentTime);

  // Scroll active segment into view when it changes
  useEffect(() => {
    if (activeIndex === lastScrolled.current) return;
    lastScrolled.current = activeIndex;
    rowRefs.current[activeIndex]?.scrollIntoView({
      behavior: "smooth",
      block: "center",
    });
  }, [activeIndex]);

  return (
    <div className="transcript">
      {segments.map((seg, i) => {
        const isActive = i === activeIndex && currentTime > 0;
        return (
          <div
            key={seg.id}
            ref={(el) => (rowRefs.current[i] = el)}
            className={`transcript__row ${isActive ? "transcript__row--active" : ""}`}
          >
            <button
              className="transcript__timestamp"
              onClick={() => onSeek(seg.start)}
              title={`Jump to ${formatTime(seg.start)}`}
            >
              {formatTime(seg.start)}
            </button>
            <p className="transcript__text">{seg.text}</p>
          </div>
        );
      })}
    </div>
  );
}
