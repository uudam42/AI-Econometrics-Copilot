"use client";

import { useState } from "react";
import { Button } from "@/components/ui/button";
import type {
  ExportFormat,
  ExportSourceType,
  PublicationExportConfig,
  TableStyle,
} from "@/types/publication_export";

const FORMAT_OPTIONS: { value: ExportFormat; label: string }[] = [
  { value: "docx", label: "Word (.docx)" },
  { value: "latex", label: "LaTeX (.tex)" },
  { value: "markdown", label: "Markdown (.md)" },
  { value: "html", label: "HTML" },
  { value: "json", label: "JSON" },
];

const TABLE_STYLES: { value: TableStyle; label: string }[] = [
  { value: "academic", label: "Academic" },
  { value: "compact", label: "Compact" },
  { value: "detailed", label: "Detailed" },
];

interface Props {
  sourceType: ExportSourceType;
  sourceId: string;
  projectId?: string;
  onSubmit: (config: PublicationExportConfig) => void;
  loading?: boolean;
}

export function PublicationExportForm({
  sourceType,
  sourceId,
  projectId,
  onSubmit,
  loading,
}: Props) {
  const [title, setTitle] = useState("");
  const [authorName, setAuthorName] = useState("");
  const [institution, setInstitution] = useState("");
  const [supervisor, setSupervisor] = useState("");
  const [tableStyle, setTableStyle] = useState<TableStyle>("academic");
  const [formats, setFormats] = useState<ExportFormat[]>(["docx"]);

  const [includeCover, setIncludeCover] = useState(true);
  const [includeVariables, setIncludeVariables] = useState(true);
  const [includeStats, setIncludeStats] = useState(true);
  const [includeRegression, setIncludeRegression] = useState(true);
  const [includeComparison, setIncludeComparison] = useState(true);
  const [includeDiagnostics, setIncludeDiagnostics] = useState(true);
  const [includeFigures, setIncludeFigures] = useState(true);
  const [includeMethodology, setIncludeMethodology] = useState(true);
  const [includeLimitations, setIncludeLimitations] = useState(true);
  const [includeReproducibility, setIncludeReproducibility] = useState(true);

  function toggleFormat(f: ExportFormat) {
    setFormats((prev) =>
      prev.includes(f) ? prev.filter((x) => x !== f) : [...prev, f]
    );
  }

  function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (!title.trim() || formats.length === 0) return;

    const config: PublicationExportConfig = {
      project_id: projectId,
      source_type: sourceType,
      source_id: sourceId,
      title: title.trim(),
      author_name: authorName.trim() || undefined,
      institution_name: institution.trim() || undefined,
      course_or_supervisor: supervisor.trim() || undefined,
      selected_table_style: tableStyle,
      include_cover_page: includeCover,
      include_variable_table: includeVariables,
      include_descriptive_statistics: includeStats,
      include_regression_table: includeRegression,
      include_model_comparison: includeComparison,
      include_diagnostics: includeDiagnostics,
      include_figures: includeFigures,
      include_methodology_section: includeMethodology,
      include_limitations_section: includeLimitations,
      include_reproducibility_appendix: includeReproducibility,
      output_formats: formats,
    };
    onSubmit(config);
  }

  return (
    <form onSubmit={handleSubmit} className="space-y-6">
      {/* Title & Author */}
      <fieldset className="space-y-3">
        <legend className="text-sm font-semibold text-muted-foreground">
          Export Metadata
        </legend>
        <input
          type="text"
          placeholder="Report Title *"
          value={title}
          onChange={(e) => setTitle(e.target.value)}
          className="w-full rounded border px-3 py-2 text-sm"
          required
        />
        <div className="grid grid-cols-1 gap-3 sm:grid-cols-2">
          <input
            type="text"
            placeholder="Author Name"
            value={authorName}
            onChange={(e) => setAuthorName(e.target.value)}
            className="rounded border px-3 py-2 text-sm"
          />
          <input
            type="text"
            placeholder="Institution"
            value={institution}
            onChange={(e) => setInstitution(e.target.value)}
            className="rounded border px-3 py-2 text-sm"
          />
        </div>
        <input
          type="text"
          placeholder="Course / Supervisor (optional)"
          value={supervisor}
          onChange={(e) => setSupervisor(e.target.value)}
          className="w-full rounded border px-3 py-2 text-sm"
        />
      </fieldset>

      {/* Table Style */}
      <fieldset className="space-y-2">
        <legend className="text-sm font-semibold text-muted-foreground">
          Table Style
        </legend>
        <div className="flex gap-3">
          {TABLE_STYLES.map((s) => (
            <label key={s.value} className="flex items-center gap-1.5 text-sm">
              <input
                type="radio"
                name="tableStyle"
                value={s.value}
                checked={tableStyle === s.value}
                onChange={() => setTableStyle(s.value)}
              />
              {s.label}
            </label>
          ))}
        </div>
      </fieldset>

      {/* Sections */}
      <fieldset className="space-y-2">
        <legend className="text-sm font-semibold text-muted-foreground">
          Sections to Include
        </legend>
        <div className="grid grid-cols-2 gap-2 text-sm">
          {[
            { label: "Cover Page", checked: includeCover, set: setIncludeCover },
            { label: "Variable Table", checked: includeVariables, set: setIncludeVariables },
            { label: "Descriptive Statistics", checked: includeStats, set: setIncludeStats },
            { label: "Regression Table", checked: includeRegression, set: setIncludeRegression },
            { label: "Model Comparison", checked: includeComparison, set: setIncludeComparison },
            { label: "Diagnostics", checked: includeDiagnostics, set: setIncludeDiagnostics },
            { label: "Figures", checked: includeFigures, set: setIncludeFigures },
            { label: "Methodology", checked: includeMethodology, set: setIncludeMethodology },
            { label: "Limitations", checked: includeLimitations, set: setIncludeLimitations },
            { label: "Reproducibility Appendix", checked: includeReproducibility, set: setIncludeReproducibility },
          ].map((s) => (
            <label key={s.label} className="flex items-center gap-1.5">
              <input
                type="checkbox"
                checked={s.checked}
                onChange={(e) => s.set(e.target.checked)}
              />
              {s.label}
            </label>
          ))}
        </div>
      </fieldset>

      {/* Output Formats */}
      <fieldset className="space-y-2">
        <legend className="text-sm font-semibold text-muted-foreground">
          Output Formats *
        </legend>
        <div className="flex flex-wrap gap-3 text-sm">
          {FORMAT_OPTIONS.map((f) => (
            <label key={f.value} className="flex items-center gap-1.5">
              <input
                type="checkbox"
                checked={formats.includes(f.value)}
                onChange={() => toggleFormat(f.value)}
              />
              {f.label}
            </label>
          ))}
        </div>
      </fieldset>

      <Button type="submit" disabled={loading || !title.trim() || formats.length === 0}>
        {loading ? "Generating..." : "Generate Publication Export"}
      </Button>
    </form>
  );
}
