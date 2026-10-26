import React, { useState } from 'react';
import {
  UploadCloud, FileSpreadsheet, CheckCircle,
  Download, ArrowRight, ShieldCheck, FileText
} from 'lucide-react';
import { api } from '../../services/api';

const LEAD_FIELDS = [
  { id: 'ignore', label: '-- Do Not Import (Ignore) --' },
  { id: 'company_name', label: 'Company Name *' },
  { id: 'official_website', label: 'Official Website' },
  { id: 'general_business_email', label: 'Business Email' },
  { id: 'public_business_phone', label: 'Business Phone' },
  { id: 'industry', label: 'Industry / Sector' },
  { id: 'business_category', label: 'Business Category' },
  { id: 'city', label: 'City' },
  { id: 'state', label: 'State' },
  { id: 'country', label: 'Country' },
  { id: 'public_business_address', label: 'Full Street Address' },
  { id: 'publicly_listed_contact_name', label: 'Contact Person / Founder' },
  { id: 'publicly_listed_designation', label: 'Job Title / Designation' },
  { id: 'company_linkedin_url', label: 'Company LinkedIn URL' },
  { id: 'source_url', label: 'Source URL' },
];

export const ImportExportView: React.FC = () => {
  const [step, setStep] = useState<1 | 2 | 3 | 4>(1);
  const [file, setFile] = useState<File | null>(null);
  const [uploading, setUploading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Preview data
  const [tempFileId, setTempFileId] = useState('');
  const [headers, setHeaders] = useState<string[]>([]);
  const [sampleRows, setSampleRows] = useState<any[]>([]);
  const [columnMapping, setColumnMapping] = useState<Record<string, string>>({});
  const [totalDetectedRows, setTotalDetectedRows] = useState(0);

  // Validation Preview
  const [validationData, setValidationData] = useState<any>(null);
  const [validating, setValidating] = useState(false);
  const [skipDuplicates, setSkipDuplicates] = useState(true);
  const [mergeExisting, setMergeExisting] = useState(false);

  // Import Result
  const [importResult, setImportResult] = useState<any>(null);
  const [committing, setCommitting] = useState(false);

  // Export state
  const [exportStage, setExportStage] = useState('');
  const [exportPriority, setExportPriority] = useState('');

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      setFile(e.target.files[0]);
      setError(null);
    }
  };

  const handleUpload = async () => {
    if (!file) return;
    setUploading(true);
    setError(null);
    try {
      const res = await api.uploadImportFile(file);
      setTempFileId(res.temp_file_id);
      setHeaders(res.headers);
      setSampleRows(res.sample_rows);
      setColumnMapping(res.suggested_mappings || {});
      setTotalDetectedRows(res.total_detected_rows);
      setStep(2);
    } catch (err: any) {
      setError(err.message || 'Failed to upload and parse file');
    } finally {
      setUploading(false);
    }
  };

  const handleValidateMapping = async () => {
    setValidating(true);
    setError(null);
    try {
      const val = await api.validateImport(tempFileId, columnMapping, skipDuplicates, mergeExisting);
      setValidationData(val);
      setStep(3);
    } catch (err: any) {
      setError(err.message || 'Validation failed');
    } finally {
      setValidating(false);
    }
  };

  const handleCommitImport = async () => {
    setCommitting(true);
    setError(null);
    try {
      const res = await api.commitImport(tempFileId, columnMapping, skipDuplicates, mergeExisting);
      setImportResult(res);
      setStep(4);
    } catch (err: any) {
      setError(err.message || 'Import execution failed');
    } finally {
      setCommitting(false);
    }
  };

  const handleDownloadExport = (format: 'xlsx' | 'csv') => {
    const params: Record<string, string> = {};
    if (exportStage) params.stage = exportStage;
    if (exportPriority) params.priority = exportPriority;
    const url = api.getExportUrl(format, params);
    window.open(url, '_blank');
  };

  return (
    <div className="space-y-8">
      {/* SECTION 1: EXCEL / CSV IMPORT PIPELINE */}
      <div className="bg-white p-6 rounded-xl border border-slate-200 shadow-sm space-y-6">
        <div>
          <h2 className="text-xl font-bold text-slate-900 flex items-center gap-2">
            <FileSpreadsheet className="w-5 h-5 text-brand-700" />
            <span>Pipeline B: Excel & CSV Dataset Ingestion</span>
          </h2>
          <p className="text-xs text-slate-500 mt-1">
            Upload company datasets in .csv or .xlsx format with smart column mapping, duplicate detection, and safe field merging.
          </p>
        </div>

        {/* Wizard Steps Tracker */}
        <div className="flex items-center justify-between max-w-xl mx-auto py-2 text-xs">
          {[
            { num: 1, title: 'Upload File' },
            { num: 2, title: 'Map Columns' },
            { num: 3, title: 'Review & Dedupe' },
            { num: 4, title: 'Import Summary' },
          ].map((s) => (
            <div key={s.num} className="flex items-center gap-2">
              <div
                className={`w-6 h-6 rounded-full flex items-center justify-center font-bold ${
                  step === s.num
                    ? 'bg-brand-700 text-white'
                    : step > s.num
                    ? 'bg-emerald-600 text-white'
                    : 'bg-slate-200 text-slate-600'
                }`}
              >
                {step > s.num ? '✓' : s.num}
              </div>
              <span className={`font-semibold ${step === s.num ? 'text-brand-900' : 'text-slate-500'}`}>
                {s.title}
              </span>
            </div>
          ))}
        </div>

        {error && (
          <div className="p-3 bg-red-50 border border-red-200 rounded-lg text-red-700 text-xs">
            {error}
          </div>
        )}

        {/* STEP 1: UPLOAD */}
        {step === 1 && (
          <div className="border-2 border-dashed border-slate-300 rounded-xl p-8 text-center space-y-4 hover:border-brand-500 transition-colors">
            <div className="mx-auto w-12 h-12 rounded-full bg-blue-50 flex items-center justify-center text-brand-700">
              <UploadCloud className="w-6 h-6" />
            </div>
            <div>
              <p className="text-sm font-semibold text-slate-800">Choose a CSV or XLSX file to import</p>
              <p className="text-xs text-slate-400 mt-1">Files up to 15 MB supported</p>
            </div>
            <input
              type="file"
              accept=".csv, .xlsx, .xls"
              onChange={handleFileChange}
              className="text-xs text-slate-500 file:mr-4 file:py-2 file:px-4 file:rounded-md file:border-0 file:text-xs file:font-semibold file:bg-brand-50 file:text-brand-700 hover:file:bg-brand-100"
            />
            {file && (
              <div className="pt-2">
                <button
                  onClick={handleUpload}
                  disabled={uploading}
                  className="px-6 py-2 bg-brand-700 hover:bg-brand-800 disabled:opacity-50 text-white rounded-lg text-xs font-bold shadow-sm transition-colors"
                >
                  {uploading ? 'Parsing File...' : `Upload & Preview (${file.name})`}
                </button>
              </div>
            )}
          </div>
        )}

        {/* STEP 2: COLUMN MAPPING */}
        {step === 2 && (
          <div className="space-y-4">
            <div className="flex items-center justify-between text-xs">
              <span className="font-bold text-slate-800">
                Found {headers.length} Columns across {totalDetectedRows} Rows
              </span>
              <button
                onClick={() => setStep(1)}
                className="text-slate-500 hover:text-slate-800 underline"
              >
                Choose another file
              </button>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-3 text-xs bg-slate-50 p-4 rounded-xl border border-slate-200">
              {headers.map((hdr) => (
                <div key={hdr} className="flex items-center justify-between gap-2 p-2 bg-white rounded border border-slate-200">
                  <span className="font-semibold text-slate-800 truncate max-w-[160px]" title={hdr}>
                    {hdr}
                  </span>
                  <ArrowRight className="w-3.5 h-3.5 text-slate-400 flex-shrink-0" />
                  <select
                    value={columnMapping[hdr] || 'ignore'}
                    onChange={(e) => setColumnMapping({ ...columnMapping, [hdr]: e.target.value })}
                    className="flex-1 px-2 py-1 text-xs bg-slate-50 border border-slate-300 rounded focus:ring-1 focus:ring-brand-500 focus:outline-none"
                  >
                    {LEAD_FIELDS.map((f) => (
                      <option key={f.id} value={f.id}>{f.label}</option>
                    ))}
                  </select>
                </div>
              ))}
            </div>

            {/* Sample Rows Preview */}
            <div className="space-y-2">
              <span className="text-xs font-bold text-slate-600">Sample Data Preview (First 5 Rows)</span>
              <div className="overflow-x-auto border border-slate-200 rounded-lg">
                <table className="w-full text-left text-xs">
                  <thead className="bg-slate-100 text-slate-700">
                    <tr>
                      {headers.map(h => <th key={h} className="px-3 py-2 font-semibold">{h}</th>)}
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-100">
                    {sampleRows.map((r, i) => (
                      <tr key={i} className="hover:bg-slate-50">
                        {headers.map(h => (
                          <td key={h} className="px-3 py-1.5 text-slate-600 truncate max-w-[140px]">{String(r[h] || '')}</td>
                        ))}
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>

            <div className="flex justify-end pt-2">
              <button
                onClick={handleValidateMapping}
                disabled={validating}
                className="px-6 py-2 bg-brand-700 hover:bg-brand-800 text-white rounded-lg text-xs font-bold shadow-sm transition-colors"
              >
                {validating ? 'Validating Records...' : 'Proceed to Deduplication Review →'}
              </button>
            </div>
          </div>
        )}

        {/* STEP 3: DEDUPLICATION & VALIDATION REVIEW */}
        {step === 3 && validationData && (
          <div className="space-y-5">
            <div className="grid grid-cols-3 gap-3">
              <div className="p-4 bg-emerald-50 border border-emerald-200 rounded-xl text-center">
                <div className="text-xl font-bold text-emerald-800">{validationData.valid_new_records}</div>
                <div className="text-xs text-emerald-700 font-semibold mt-0.5">New Unique Records</div>
              </div>
              <div className="p-4 bg-amber-50 border border-amber-200 rounded-xl text-center">
                <div className="text-xl font-bold text-amber-800">{validationData.duplicate_records}</div>
                <div className="text-xs text-amber-700 font-semibold mt-0.5">Duplicate Matches</div>
              </div>
              <div className="p-4 bg-red-50 border border-red-200 rounded-xl text-center">
                <div className="text-xl font-bold text-red-800">{validationData.invalid_records}</div>
                <div className="text-xs text-red-700 font-semibold mt-0.5">Missing Company Name</div>
              </div>
            </div>

            {/* Deduplication Strategy Settings */}
            <div className="p-4 bg-slate-50 border border-slate-200 rounded-xl space-y-2 text-xs">
              <span className="font-bold text-slate-800">Duplicate Handling Strategy:</span>
              <div className="flex flex-col sm:flex-row gap-4 pt-1">
                <label className="flex items-center gap-2 cursor-pointer">
                  <input
                    type="checkbox"
                    checked={skipDuplicates}
                    onChange={(e) => setSkipDuplicates(e.target.checked)}
                    className="rounded text-brand-600 focus:ring-brand-500"
                  />
                  <span>Skip duplicate companies (Prevent duplicate leads in CRM)</span>
                </label>
                <label className="flex items-center gap-2 cursor-pointer">
                  <input
                    type="checkbox"
                    checked={mergeExisting}
                    onChange={(e) => setMergeExisting(e.target.checked)}
                    className="rounded text-brand-600 focus:ring-brand-500"
                  />
                  <span>Merge into existing (Only populate fields that are currently empty)</span>
                </label>
              </div>
            </div>

            {/* Preview of Evaluated Rows */}
            <div className="space-y-2 text-xs">
              <span className="font-bold text-slate-700">Pre-Import Sample Assessment</span>
              <div className="border border-slate-200 rounded-lg overflow-x-auto">
                <table className="w-full text-left">
                  <thead className="bg-slate-100 text-slate-700 font-semibold">
                    <tr>
                      <th className="px-3 py-2">Row #</th>
                      <th className="px-3 py-2">Company</th>
                      <th className="px-3 py-2">Website</th>
                      <th className="px-3 py-2">Contact Info</th>
                      <th className="px-3 py-2">Action / Status</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-100">
                    {validationData.preview_items?.map((p: any, idx: number) => (
                      <tr key={idx} className="hover:bg-slate-50">
                        <td className="px-3 py-1.5 font-mono text-slate-400">{p.row_index}</td>
                        <td className="px-3 py-1.5 font-bold text-slate-800">{p.company_name}</td>
                        <td className="px-3 py-1.5 text-brand-700">{p.website || '-'}</td>
                        <td className="px-3 py-1.5 text-slate-600">{p.email || p.phone || '-'}</td>
                        <td className="px-3 py-1.5">
                          <span className={`px-2 py-0.5 rounded font-semibold text-[10px] ${
                            p.action.includes('NEW_RECORD') ? 'bg-emerald-100 text-emerald-800' :
                            p.action.includes('DUPLICATE') ? 'bg-amber-100 text-amber-800' :
                            'bg-red-100 text-red-800'
                          }`}>
                            {p.action}
                          </span>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>

            <div className="flex justify-between pt-2">
              <button
                onClick={() => setStep(2)}
                className="px-4 py-2 border border-slate-300 text-slate-700 hover:bg-slate-50 rounded-lg text-xs font-semibold"
              >
                ← Back to Mapping
              </button>
              <button
                onClick={handleCommitImport}
                disabled={committing}
                className="px-6 py-2 bg-emerald-700 hover:bg-emerald-800 disabled:opacity-50 text-white rounded-lg text-xs font-bold shadow-sm transition-colors"
              >
                {committing ? 'Importing Leads...' : 'Confirm & Commit Import to CRM ✓'}
              </button>
            </div>
          </div>
        )}

        {/* STEP 4: IMPORT RESULT REPORT */}
        {step === 4 && importResult && (
          <div className="space-y-4 text-center py-6">
            <div className="w-12 h-12 bg-emerald-100 text-emerald-700 rounded-full flex items-center justify-center mx-auto">
              <CheckCircle className="w-6 h-6" />
            </div>
            <h3 className="text-lg font-bold text-slate-900">Import Completed Successfully!</h3>
            <div className="flex justify-center gap-6 text-xs text-slate-600">
              <div><span className="font-bold text-emerald-700 text-sm">{importResult.imported_records}</span> Imported</div>
              <div><span className="font-bold text-amber-700 text-sm">{importResult.skipped_records}</span> Skipped</div>
              <div><span className="font-bold text-blue-700 text-sm">{importResult.merged_records}</span> Merged</div>
            </div>
            <div className="pt-4">
              <button
                onClick={() => { setStep(1); setFile(null); }}
                className="px-5 py-2 bg-brand-700 hover:bg-brand-800 text-white text-xs font-bold rounded-lg shadow-sm"
              >
                Import Another File
              </button>
            </div>
          </div>
        )}
      </div>

      {/* SECTION 2: EXPORT CENTER */}
      <div className="bg-white p-6 rounded-xl border border-slate-200 shadow-sm space-y-4">
        <div>
          <h2 className="text-xl font-bold text-slate-900 flex items-center gap-2">
            <Download className="w-5 h-5 text-emerald-600" />
            <span>Export Center (Excel & CSV)</span>
          </h2>
          <p className="text-xs text-slate-500 mt-1">
            Download your CRM leads with source URLs, verification badges, scores, and full formula-injection security defense.
          </p>
        </div>

        <div className="p-4 bg-slate-50 rounded-xl border border-slate-200 grid grid-cols-1 sm:grid-cols-3 gap-4 items-center">
          <div>
            <label className="block text-xs font-semibold text-slate-700 mb-1">Filter by CRM Stage</label>
            <select
              value={exportStage}
              onChange={(e) => setExportStage(e.target.value)}
              className="w-full px-2.5 py-1.5 text-xs bg-white border border-slate-300 rounded focus:outline-none"
            >
              <option value="">All Stages</option>
              <option value="Qualified">Qualified</option>
              <option value="Ready for Review">Ready for Review</option>
              <option value="Contacted">Contacted</option>
              <option value="Interested">Interested</option>
              <option value="Converted">Converted</option>
            </select>
          </div>

          <div>
            <label className="block text-xs font-semibold text-slate-700 mb-1">Filter by Priority</label>
            <select
              value={exportPriority}
              onChange={(e) => setExportPriority(e.target.value)}
              className="w-full px-2.5 py-1.5 text-xs bg-white border border-slate-300 rounded focus:outline-none"
            >
              <option value="">All Priorities</option>
              <option value="High Priority">High Priority (80–100)</option>
              <option value="Medium Priority">Medium Priority (60–79)</option>
              <option value="Low Priority">Low Priority (40–59)</option>
            </select>
          </div>

          <div className="flex gap-2 self-end">
            <button
              onClick={() => handleDownloadExport('xlsx')}
              className="flex-1 py-2 px-3 bg-emerald-700 hover:bg-emerald-800 text-white rounded text-xs font-bold shadow-sm flex items-center justify-center gap-1.5"
            >
              <FileSpreadsheet className="w-4 h-4" />
              <span>Export .XLSX</span>
            </button>
            <button
              onClick={() => handleDownloadExport('csv')}
              className="flex-1 py-2 px-3 bg-blue-700 hover:bg-blue-800 text-white rounded text-xs font-bold shadow-sm flex items-center justify-center gap-1.5"
            >
              <FileText className="w-4 h-4" />
              <span>Export .CSV</span>
            </button>
          </div>
        </div>

        <div className="text-[11px] text-slate-400 flex items-center gap-1.5">
          <ShieldCheck className="w-4 h-4 text-emerald-600" />
          <span>Security guard active: Spreadsheet formula injection characters (=, +, -, @) are automatically sanitized.</span>
        </div>
      </div>
    </div>
  );
};
