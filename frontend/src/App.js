import { BrowserRouter, Routes, Route } from "react-router-dom";
import { Toaster } from "sonner";
import Layout from "./components/Layout";
import Dashboard from "./pages/Dashboard";
import RiskSegments from "./pages/RiskSegments";
import ModelPerformance from "./pages/ModelPerformance";
import DQDrift from "./pages/DQDrift";
import RunHistory from "./pages/RunHistory";
import Upload from "./pages/Upload";
import "./App.css";

function App() {
  return (
    <div className="App min-h-screen bg-[#F8FAFC]">
      <BrowserRouter>
        <Routes>
          <Route path="/" element={<Layout />}>
            <Route index element={<Dashboard />} />
            <Route path="risk-segments" element={<RiskSegments />} />
            <Route path="model-performance" element={<ModelPerformance />} />
            <Route path="dq-drift" element={<DQDrift />} />
            <Route path="run-history" element={<RunHistory />} />
            <Route path="upload" element={<Upload />} />
          </Route>
        </Routes>
      </BrowserRouter>
      <Toaster position="top-right" richColors closeButton />
    </div>
  );
}

export default App;
