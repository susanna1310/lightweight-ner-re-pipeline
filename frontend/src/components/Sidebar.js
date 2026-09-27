import React, { useMemo } from "react";
import { AgGridReact } from "ag-grid-react";
import { ModuleRegistry } from 'ag-grid-community';
import { AllCommunityModule } from 'ag-grid-community';
ModuleRegistry.registerModules([AllCommunityModule]);

function Sidebar({ relations, isOpen, entity, onClose, onHoverTarget }) {
  const rowData = useMemo(() => {
    if (!relations || !Array.isArray(relations)) return [];
    return relations.map(([target, targetLabel, label, value, targetId]) => ({
      relationToText: target,
      entityLabel: targetLabel,
      relationLabel: label,
      value: value,
      targetId,
    }));
  }, [relations]);

  const handleCellMouseOver = (params) => onHoverTarget?.(params.data.targetId);
  const handleCellMouseOut = () => onHoverTarget?.(null);

  const defaultColDef = useMemo(() => ({
    resizable: false,      
    suppressMovable: true,
  }), []);

  const columnDefs = useMemo(() => [
    {
      headerName: "Relation to Text",
      field: "relationToText",
      flex: 2,
      sortable: true,
      unSortIcon: true,
      wrapText: true,
      autoHeight: true,
      cellClass: 'ag-cell-wrap-text'
    },
    {
      headerName: "Entity Label",
      field: "entityLabel",
      flex: 1,
      sortable: true,
      unSortIcon: true,
      autoHeight: true,
    },
    {
      headerName: "Relation",
      field: "relationLabel",
      flex: 1,
      sortable: true,
      unSortIcon: true,
      autoHeight: true,
    },
    {
      headerName: "Value",
      field: "value",
      flex: 1,
      sortable: true,
      unSortIcon: true,
      sort: 'desc',
      autoHeight: true,
    },
  ], []);


  if (!isOpen || !entity) return null;

  return (
    <div
      className="w-1/2 h-full bg-base-100 rounded-box shadow-sm p-5 sticky top-0 self-start flex flex-col"
      style={{ maxHeight: "100%" }}
    >
      <div className="flex items-start justify-between pb-3 border-b border-base-300">
        <div>
          <p className="text-xs uppercase tracking-wide text-base-content/50">Entity</p>
          <p className="text-base font-semibold text-primary">{entity.entityText}</p>
          <span className="badge badge-secondary badge-outline badge-sm mt-1">{entity.entityLabel}</span>
        </div>
        <button className="btn btn-sm btn-circle btn-ghost" onClick={onClose} aria-label="Close">
          ✕
        </button>
      </div>

      <div className="flex flex-col flex-grow pt-3">
        <p className="text-xs uppercase tracking-wide text-base-content/50 mb-2">Relations</p>
        {rowData.length > 0 ? (
          <div className="ag-theme-alpine h-full w-full">
            <AgGridReact
              rowData={rowData}
              columnDefs={columnDefs}
              defaultColDef={defaultColDef}
              onCellMouseOver={handleCellMouseOver}
              onCellMouseOut={handleCellMouseOut}
            />
          </div>
        ) : (
          <p className="text-sm text-base-content/50">No relations</p>
        )}
      </div>
    </div>
  );
}

export default Sidebar;