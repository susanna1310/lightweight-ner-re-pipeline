import React, { useRef, useState } from "react";

function FileUpload({ onFileChange }) {
  const inputRef = useRef(null);
  const [fileName, setFileName] = useState("");
  const [isDragging, setIsDragging] = useState(false);

  const selectFile = (file) => {
    setFileName(file ? file.name : "");
    onFileChange(file);
  };

  const handleFileChange = (e) => {
    selectFile(e.target.files[0]);
  };

  const handleDrop = (e) => {
    e.preventDefault();
    setIsDragging(false);
    const file = e.dataTransfer.files?.[0];
    if (file) selectFile(file);
  };

  return (
    <div
      onClick={() => inputRef.current?.click()}
      onDragOver={(e) => {
        e.preventDefault();
        setIsDragging(true);
      }}
      onDragLeave={() => setIsDragging(false)}
      onDrop={handleDrop}
      className={`flex flex-col items-center justify-center gap-2 w-full rounded-box border-2 border-dashed px-6 py-10 cursor-pointer transition-colors
        ${isDragging ? "border-primary bg-primary/5" : "border-primary/30 bg-base-100 hover:border-primary hover:bg-primary/5"}`}
    >
      <svg
        xmlns="http://www.w3.org/2000/svg"
        className="h-8 w-8 text-primary/60"
        fill="none"
        viewBox="0 0 24 24"
        stroke="currentColor"
        strokeWidth={1.5}
      >
        <path strokeLinecap="round" strokeLinejoin="round" d="M12 16.5V9m0 0-3 3m3-3 3 3M4.5 19.5h15a1.5 1.5 0 0 0 1.5-1.5v-6a1.5 1.5 0 0 0-1.5-1.5H15l-1.5-2.25h-3L9 10.5H4.5A1.5 1.5 0 0 0 3 12v6a1.5 1.5 0 0 0 1.5 1.5Z" />
      </svg>
      <p className="text-sm font-medium">
        <span className="text-primary">Click to upload</span> or drag and drop
      </p>
      <p className="text-xs text-base-content/50 truncate max-w-full">
        {fileName || "No file chosen"}
      </p>
      <input
        ref={inputRef}
        type="file"
        className="hidden"
        onClick={(e) => e.stopPropagation()}
        onChange={handleFileChange}
      />
    </div>
  );
}

export default FileUpload;
