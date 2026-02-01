import { useState, useCallback } from "react";
import { useNavigate } from "react-router-dom";
import { toast } from "sonner";
import { api } from "../lib/api";
import { Button } from "../components/ui/button";
import { Upload as UploadIcon, FileText, X, Play, RefreshCw, CheckCircle } from "lucide-react";
import { cn } from "../lib/utils";

export default function Upload() {
  const [file, setFile] = useState(null);
  const [dragActive, setDragActive] = useState(false);
  const [uploading, setUploading] = useState(false);
  const [uploadResult, setUploadResult] = useState(null);
  const [executing, setExecuting] = useState(false);
  const navigate = useNavigate();

  const handleDrag = useCallback((e) => {
    e.preventDefault();
    e.stopPropagation();
    if (e.type === "dragenter" || e.type === "dragover") {
      setDragActive(true);
    } else if (e.type === "dragleave") {
      setDragActive(false);
    }
  }, []);

  const handleDrop = useCallback((e) => {
    e.preventDefault();
    e.stopPropagation();
    setDragActive(false);
    
    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      const droppedFile = e.dataTransfer.files[0];
      if (droppedFile.name.endsWith('.csv')) {
        setFile(droppedFile);
        setUploadResult(null);
      } else {
        toast.error("Please upload a CSV file");
      }
    }
  }, []);

  const handleFileChange = (e) => {
    if (e.target.files && e.target.files[0]) {
      setFile(e.target.files[0]);
      setUploadResult(null);
    }
  };

  const handleUpload = async () => {
    if (!file) return;
    
    try {
      setUploading(true);
      const response = await api.upload(file);
      setUploadResult(response.data);
      toast.success(response.data.message);
    } catch (error) {
      console.error("Upload error:", error);
      toast.error(error.response?.data?.detail || "Failed to upload file");
    } finally {
      setUploading(false);
    }
  };

  const handleExecute = async () => {
    if (!uploadResult?.run_id) return;
    
    try {
      setExecuting(true);
      toast.info("Running pipeline...");
      const response = await api.execute(uploadResult.run_id);
      toast.success(response.data.message);
      navigate("/");
    } catch (error) {
      console.error("Execute error:", error);
      toast.error(error.response?.data?.detail || "Failed to execute pipeline");
    } finally {
      setExecuting(false);
    }
  };

  const removeFile = () => {
    setFile(null);
    setUploadResult(null);
  };

  return (
    <div className="max-w-2xl mx-auto space-y-8" data-testid="upload-page">
      {/* Header */}
      <div className="text-center">
        <h2 className="text-2xl font-bold">Upload Data</h2>
        <p className="text-muted-foreground mt-2">Upload a CSV file with loan application data to analyze</p>
      </div>

      {/* Upload Area */}
      <div
        onDragEnter={handleDrag}
        onDragLeave={handleDrag}
        onDragOver={handleDrag}
        onDrop={handleDrop}
        className={cn(
          "relative border-2 border-dashed rounded-lg p-12 text-center transition-colors",
          dragActive ? "border-primary bg-primary/5" : "border-border hover:border-primary/50",
          file && "border-green-500 bg-green-50"
        )}
      >
        {file ? (
          <div className="space-y-4">
            <div className="w-16 h-16 mx-auto rounded-full bg-green-100 flex items-center justify-center">
              <FileText className="w-8 h-8 text-green-600" />
            </div>
            <div>
              <p className="font-medium">{file.name}</p>
              <p className="text-sm text-muted-foreground">
                {(file.size / 1024).toFixed(1)} KB
              </p>
            </div>
            <button
              onClick={removeFile}
              className="inline-flex items-center gap-1 text-sm text-muted-foreground hover:text-foreground"
              data-testid="remove-file-btn"
            >
              <X className="w-4 h-4" />
              Remove
            </button>
          </div>
        ) : (
          <div className="space-y-4">
            <div className="w-16 h-16 mx-auto rounded-full bg-muted flex items-center justify-center">
              <UploadIcon className="w-8 h-8 text-muted-foreground" />
            </div>
            <div>
              <p className="font-medium">Drop your CSV file here</p>
              <p className="text-sm text-muted-foreground">or click to browse</p>
            </div>
            <input
              type="file"
              accept=".csv"
              onChange={handleFileChange}
              className="absolute inset-0 w-full h-full opacity-0 cursor-pointer"
              data-testid="file-input"
            />
          </div>
        )}
      </div>

      {/* Actions */}
      {file && !uploadResult && (
        <div className="flex justify-center">
          <Button
            onClick={handleUpload}
            disabled={uploading}
            data-testid="upload-btn"
            className="gap-2"
          >
            {uploading ? (
              <RefreshCw className="w-4 h-4 animate-spin" />
            ) : (
              <UploadIcon className="w-4 h-4" />
            )}
            {uploading ? "Uploading..." : "Upload File"}
          </Button>
        </div>
      )}

      {/* Upload Result */}
      {uploadResult && (
        <div className="bg-white border border-border rounded-md p-6 space-y-6">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-full bg-green-100 flex items-center justify-center">
              <CheckCircle className="w-5 h-5 text-green-600" />
            </div>
            <div>
              <p className="font-semibold">Upload Successful</p>
              <p className="text-sm text-muted-foreground">{uploadResult.message}</p>
            </div>
          </div>
          
          <div className="grid grid-cols-2 gap-4 p-4 bg-muted/50 rounded-md">
            <div>
              <p className="text-xs text-muted-foreground uppercase tracking-widest">Run ID</p>
              <p className="font-mono text-sm">{uploadResult.run_id.slice(0, 16)}...</p>
            </div>
            <div>
              <p className="text-xs text-muted-foreground uppercase tracking-widest">Records</p>
              <p className="font-semibold">{uploadResult.records_uploaded}</p>
            </div>
          </div>

          <div className="flex justify-center">
            <Button
              onClick={handleExecute}
              disabled={executing}
              data-testid="execute-btn"
              className="gap-2"
            >
              {executing ? (
                <RefreshCw className="w-4 h-4 animate-spin" />
              ) : (
                <Play className="w-4 h-4" />
              )}
              {executing ? "Running Pipeline..." : "Execute Pipeline"}
            </Button>
          </div>
        </div>
      )}

      {/* Sample Format */}
      <div className="bg-white border border-border rounded-md p-6">
        <h3 className="font-semibold mb-4">Expected CSV Format</h3>
        <div className="overflow-x-auto">
          <table className="text-sm">
            <thead>
              <tr className="border-b">
                <th className="text-left py-2 pr-4 font-medium">Column</th>
                <th className="text-left py-2 pr-4 font-medium">Type</th>
                <th className="text-left py-2 font-medium">Description</th>
              </tr>
            </thead>
            <tbody className="text-muted-foreground">
              <tr className="border-b border-border/50">
                <td className="py-2 pr-4 font-mono">loan_id</td>
                <td className="py-2 pr-4">String</td>
                <td className="py-2">Unique loan identifier (required)</td>
              </tr>
              <tr className="border-b border-border/50">
                <td className="py-2 pr-4 font-mono">customer_id</td>
                <td className="py-2 pr-4">String</td>
                <td className="py-2">Customer identifier (required)</td>
              </tr>
              <tr className="border-b border-border/50">
                <td className="py-2 pr-4 font-mono">loan_amount</td>
                <td className="py-2 pr-4">Number</td>
                <td className="py-2">Loan amount in USD (required)</td>
              </tr>
              <tr className="border-b border-border/50">
                <td className="py-2 pr-4 font-mono">interest_rate</td>
                <td className="py-2 pr-4">Number</td>
                <td className="py-2">Annual interest rate % (required)</td>
              </tr>
              <tr className="border-b border-border/50">
                <td className="py-2 pr-4 font-mono">loan_term</td>
                <td className="py-2 pr-4">Integer</td>
                <td className="py-2">Term in months (required)</td>
              </tr>
              <tr className="border-b border-border/50">
                <td className="py-2 pr-4 font-mono">annual_income</td>
                <td className="py-2 pr-4">Number</td>
                <td className="py-2">Annual income in USD</td>
              </tr>
              <tr className="border-b border-border/50">
                <td className="py-2 pr-4 font-mono">dti_ratio</td>
                <td className="py-2 pr-4">Number</td>
                <td className="py-2">Debt-to-income ratio %</td>
              </tr>
              <tr>
                <td className="py-2 pr-4 font-mono">loan_status</td>
                <td className="py-2 pr-4">0/1</td>
                <td className="py-2">0=good, 1=default (target)</td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
