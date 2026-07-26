import { useRef, useState } from "react";
import { Upload, Mic } from "lucide-react";
import "./UploadZone.css";

const ACCEPTED = ".mp3,.mp4,.wav,.m4a,.ogg,.flac,.webm";

export default function UploadZone({ onFile }) {
  const inputRef = useRef(null);
  const [dragging, setDragging] = useState(false);

  function handleDrop(e) {
    e.preventDefault();
    setDragging(false);
    const file = e.dataTransfer.files?.[0];
    if (file) onFile(file);
  }

  function handlePick(e) {
    const file = e.target.files?.[0];
    if (file) onFile(file);
  }

  return (
    <div
      className={`upload-zone ${dragging ? "upload-zone--dragging" : ""}`}
      onDragOver={(e) => { e.preventDefault(); setDragging(true); }}
      onDragLeave={() => setDragging(false)}
      onDrop={handleDrop}
      onClick={() => inputRef.current?.click()}
      role="button"
      tabIndex={0}
      onKeyDown={(e) => e.key === "Enter" && inputRef.current?.click()}
      aria-label="Upload audio file"
    >
      <input
        ref={inputRef}
        type="file"
        accept={ACCEPTED}
        onChange={handlePick}
        style={{ display: "none" }}
      />

      <div className="upload-zone__icon">
        {dragging ? <Mic size={28} /> : <Upload size={28} />}
      </div>

      <p className="upload-zone__primary">
        {dragging ? "Drop to transcribe" : "Drop your recording here"}
      </p>
      <p className="upload-zone__secondary">
        or <span className="upload-zone__link">browse files</span>
        <span className="upload-zone__formats"> · mp3, wav, m4a, mp4, flac</span>
      </p>
    </div>
  );
}
