import "./App.css";
import FileUpload from "./components/FileUpload";
import Selector from "./components/Selector";
import Sidebar from "./components/Sidebar";
import React from "react";
import { useEffect ,useState, useCallback, useMemo } from "react";
const API_BASE_URL = "http://localhost:5000"
const DE_IDENTIFICATION = "2014 De-Identification"

function App() {
  const thresholdOptions = [0.0, 0.05, 0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 0.99, 1.0];
  const modelOptions = ["2010 Medical Relations", "2012 Temporal-Relations",  DE_IDENTIFICATION, "2018 ADE"]

  const [selectedFile, setSelectedFile] = useState(null);
  const [selectedLabel, setSelectedLabel] = useState("ALL LABELS");
  const [selectedThreshold, setSelectedThreshold] = useState("0.05");
  const [selectedModel, setSelectedModel] = useState(localStorage.getItem('selectedModel') || "2010 Medical Relations");
  const [labels, setLabels] = useState([]);
  const [loading, setLoading] = useState(false);
  const [text, setText] = useState("");
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const [currentEntity, setCurrentEntity] = useState(null);
  const [relations, setRelations] = useState(null);
  const [renderedHtml, setRenderedHtml] = useState("");
  const [hoveredTargetId, setHoveredTargetId] = useState(null);
  const [error, setError] = useState(null);

  const convertMarkToButton = useCallback((html, rels, entityIds) => {
    const div = document.createElement("div");
    div.innerHTML = html;

    const marks = div.querySelectorAll("mark");

    marks.forEach((mark, index) => {
      const span = mark.querySelector("span");
      const label = span?.textContent?.trim() || "UNKNOWN";
      span?.remove();

      const entityText = mark.textContent.trim();
      const entityId = entityIds ? entityIds[index] : index;

      const button = document.createElement("button");
      button.setAttribute("data-entity", entityText);
      button.setAttribute("data-label", label);
      button.setAttribute("id", `${entityId}`);

      button.className = "btn btn-sm rounded-md m-1";
      button.style.cssText = mark.style.cssText;
      button.style.fontWeight = "normal";

      const hasRelation = rels.some(([sourceId]) => sourceId === entityId);
      if (hasRelation) {
        button.innerHTML = `<span class="dot text-gray-50 text-xs">●</span>${entityText} <span class="text-xs ml-2">${label}</span>`;
      } else {
        button.innerHTML = `${entityText} <span class="text-xs ml-2">${label}</span>`;
      }

      mark.replaceWith(button);
    });

    return div.innerHTML;
  }, []);

  useEffect(() => {
    const container = document.getElementById("htmlContainer");
    if (!container) return;

    const handleClick = (e) => {
      const button = e.target.closest("button[data-entity]");
      if (!button) return;

      const entityText = button.getAttribute("data-entity");
      const entityLabel = button.getAttribute("data-label");
      const entityId = button.getAttribute("id");

      setCurrentEntity((prev) => {
        const isSame = prev?.entityText === entityText && prev?.entityLabel === entityLabel;
        setSidebarOpen(!isSame);
        return isSame ? null : { entityText, entityLabel, entityId };
      });
    };
    container.addEventListener("click", handleClick);
    return () => container.removeEventListener("click", handleClick);
  }, [renderedHtml]);

  useEffect(() => {
    const container = document.getElementById("htmlContainer");
    if (!container) return;
    container.querySelectorAll("button[data-entity]").forEach((btn) => {
      btn.classList.remove("ring-2", "ring-primary", "ring-offset-1");
    });
    if (currentEntity?.entityId != null) {
      document.getElementById(currentEntity.entityId)?.classList.add("ring-2", "ring-primary", "ring-offset-1");
    }
  }, [currentEntity, renderedHtml]);

  useEffect(() => {
    const container = document.getElementById("htmlContainer");
    if (!container) return;
    container.querySelectorAll("button[data-entity]").forEach((btn) => {
      btn.classList.remove("ring-2", "ring-secondary", "ring-offset-1");
    });
    if (hoveredTargetId != null) {
      const el = document.getElementById(hoveredTargetId);
      if (el) {
        el.classList.add("ring-2", "ring-secondary", "ring-offset-1");
        el.scrollIntoView({ behavior: "smooth", block: "center" });
      }
    }
  }, [hoveredTargetId, renderedHtml]);

  const updateHtml = (html, rels, entityIds) => {
    const modifiedHtml = convertMarkToButton(html, rels, entityIds);
    setRenderedHtml(modifiedHtml);
  };

  useEffect(() => {
    if (renderedHtml && document.getElementById("htmlContainer")) {
      document.getElementById("htmlContainer").innerHTML = renderedHtml;
    }
  }, [renderedHtml]);

  const backendErrorMessage = (err, context) =>
    `Couldn't ${context || "reach the backend"}. Make sure the backend is running and its models are loaded. (${err.message})`;

  const updateFromServer = async (url, body, onSuccess, context) => {
    try {
      setLoading(true);
      setError(null);
      const response = await fetch(url, {
        method: "POST",
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(body),
      });
      const data = await response.json();
      if (!response.ok) {
        throw new Error(data.error || "Something went wrong on the backend.");
      }
      setText(data.text);
      setLabels(data.labels?.concat("ALL LABELS") || []);
      setRelations(data.relations || []);
      updateHtml(data.html, data.relations || []);
      onSuccess?.();
      setLoading(false);
    } catch (err) {
      console.error("Error:", err);
      setError(backendErrorMessage(err, context));
      setLoading(false);
    }
  };

  const clearSelection = () => {
    setSidebarOpen(false);
    setCurrentEntity(null);
    setHoveredTargetId(null);
  };

  const handleModelChange = (newModel) => {
    clearSelection();
    updateFromServer(API_BASE_URL + "/api/model", { model: newModel, text }, () => {
      setSelectedModel(newModel);
      localStorage.setItem('selectedModel', newModel);
      setSelectedLabel("ALL LABELS");
    }, `load the "${newModel}" model`);
  }

  const handleLabelChange = (label) => {
    setLoading(true);
    setError(null);
    clearSelection();

    fetch(API_BASE_URL + "/api/filter", {
      method: "POST",
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({ text: text, label: label })
    })
      .then((response) => response.json().then((data) => ({ ok: response.ok, data })))
      .then(({ ok, data }) => {
        if (!ok) throw new Error(data.error || "Something went wrong on the backend.");
        const { html, entityIds } = data;
        setSelectedLabel(label);
        setLoading(false);
        updateHtml(html, relations, entityIds);
      })
      .catch((error) => {
        console.error("Error sending data to Python endpoint:", error);
        setError(backendErrorMessage(error, `apply the "${label}" label filter`));
        setLoading(false);
      });
  }

  const handleThresholdChange = (threshold) => {
    clearSelection();
    updateFromServer(API_BASE_URL + "/api/threshold", { text, threshold }, () => {
      setSelectedThreshold(threshold);
      setSelectedLabel("ALL LABELS");
    }, `apply the ${threshold} threshold`);
  };

  const handleFileChange = (file) => {
    if(file) {
      setLoading(true);
      setError(null);
      const formData = new FormData();
      formData.append("file", file);

      fetch(API_BASE_URL + "/api/upload", {
        method: "POST",
        body: formData,
      })
        .then((response) => response.json().then((data) => ({ ok: response.ok, data })))
        .then(({ ok, data }) => {
          if (!ok) throw new Error(data.error || "Something went wrong on the backend.");
          const { html, labels: labelList, text, relations: rels } = data;
          labelList.push("ALL LABELS")
          setSelectedFile(file);
          setLabels(labelList);
          setText(text);
          setRelations(rels || []);
          updateHtml(html, rels || []);
        })
        .catch((err) => {
          console.error("Upload error:", err);
          setError(backendErrorMessage(err, `upload "${file.name}"`));
        })
        .finally(() => setLoading(false));
    }
  };

  const filteredRelations = useMemo(() => {
    if (currentEntity) {
      const id = parseInt(currentEntity.entityId, 10);
      const filtered_relations = relations?.filter(([sourceId]) => sourceId === id);
      return filtered_relations.map(([_, targetId, label, value, targetText, targetLabel]) => {
        return [targetText, targetLabel, label, value.toFixed(2), targetId];
      });
    }
    return null;
  }, [currentEntity, relations]);

  const handleReset = () => {
    setSelectedFile(null);
    setText("");
    setLabels([]);
    setRelations(null);
    setRenderedHtml("");
    setSelectedLabel("ALL LABELS");
    clearSelection();
    const container = document.getElementById("htmlContainer");
    if (container) container.innerHTML = "";
  };

  const showSidebar = sidebarOpen && selectedModel !== DE_IDENTIFICATION;

  return (
    <div className="flex flex-col h-screen bg-base-200">
      {error && (
        <div className="alert alert-error rounded-none justify-between px-6 py-2 text-sm">
          <span>{error}</span>
          <button className="btn btn-ghost btn-xs" onClick={() => setError(null)} aria-label="Dismiss">
            ✕
          </button>
        </div>
      )}
      <header className="navbar bg-gradient-to-r from-primary/10 via-secondary/10 to-accent/10 border-b border-base-300 px-6 min-h-0 py-3 gap-4 flex-wrap">
        <div className="flex-1 flex items-center gap-2">
          <span className="inline-block h-2.5 w-2.5 rounded-full bg-primary"></span>
          <span className="text-lg font-semibold tracking-tight">Clinical NER &amp; RE Explorer</span>
        </div>
        {selectedFile && (
          <div className="flex flex-wrap items-end gap-3">
            <Selector onChange={handleModelChange} selectedOption={selectedModel} options={modelOptions} header={"Model"} width="w-30"></Selector>
            {selectedModel !== DE_IDENTIFICATION && (
              <Selector onChange={handleThresholdChange} selectedOption={selectedThreshold} options={thresholdOptions} header={"Threshold"}></Selector>
            )}
            <Selector onChange={handleLabelChange} selectedOption={selectedLabel} options={labels} header={"Label"} width="w-[150px]"></Selector>
            <button className="btn btn-sm btn-outline btn-primary" onClick={handleReset}>
              New file
            </button>
          </div>
        )}
      </header>

      {!selectedFile && (
        <main className="flex-1 flex items-center justify-center px-4">
          <div className="text-center max-w-md">
            <div className="mx-auto mb-4 flex h-12 w-12 items-center justify-center rounded-full bg-primary/10 text-primary">
              <svg xmlns="http://www.w3.org/2000/svg" className="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
                <path strokeLinecap="round" strokeLinejoin="round" d="M19.5 14.25v-2.625a3.375 3.375 0 0 0-3.375-3.375h-1.5A1.125 1.125 0 0 1 13.5 7.125v-1.5a3.375 3.375 0 0 0-3.375-3.375H8.25m0 12.75h7.5m-7.5 3H12M10.5 2.25H5.625c-.621 0-1.125.504-1.125 1.125v17.25c0 .621.504 1.125 1.125 1.125h12.75c.621 0 1.125-.504 1.125-1.125V11.25a9 9 0 0 0-9-9Z" />
              </svg>
            </div>
            <h1 className="text-2xl font-bold mb-2">Upload a clinical document</h1>
            <p className="text-base-content/60 mb-6">
              Extract <span className="text-primary font-medium">entities</span> and{" "}
              <span className="text-secondary font-medium">relations</span> from medical text using the trained i2b2 NER/RE models.
            </p>
            <FileUpload onFileChange={handleFileChange} />
          </div>
        </main>
      )}

      {selectedFile && (
        <main className="relative flex flex-1 overflow-hidden px-6 py-5 gap-4">
          {loading && (
            <div className="absolute inset-0 z-10 flex justify-center items-center bg-base-200/60">
              <span className="loading loading-spinner loading-lg text-primary"></span>
            </div>
          )}
          <div className={`${showSidebar ? "w-1/2" : "w-full"} overflow-y-auto rounded-box bg-base-100 shadow-sm border-t-4 border-primary p-6 leading-relaxed`}>
            <div id="htmlContainer" style={{ display: loading ? "none" : "block" }} />
          </div>
          {showSidebar && (
            <Sidebar
              relations={filteredRelations}
              isOpen={sidebarOpen}
              entity={currentEntity}
              onHoverTarget={setHoveredTargetId}
              onClose={() => {
                setSidebarOpen(false);
                setCurrentEntity(null);
                setHoveredTargetId(null);
              }}
            />
          )}
        </main>
      )}
    </div>
  );
}

export default App;
