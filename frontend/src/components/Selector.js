import React from "react";

function Selector({ onChange, selectedOption, options, header, width = "w-20" }) {
  const handleLabelChange = (e) => {
    const label = e.target.value;
    onChange(label);
  };

  return (
    <label className="form-control">
      <span className="label-text text-xs font-medium text-base-content/60 mb-1">{header}</span>
      <select
        className={`select select-bordered select-sm ${width}`}
        value={selectedOption}
        onChange={handleLabelChange}
      >
        {options.sort().map((label, index) => (
          <option key={index}>{label}</option>
        ))}
      </select>
    </label>
  );
}

export default Selector;
