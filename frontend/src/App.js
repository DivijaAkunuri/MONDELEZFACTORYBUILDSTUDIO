import "@/App.css";
import { BrowserRouter, Routes, Route, Navigate } from "react-router-dom";
import { Toaster } from "sonner";

import Estimator from "@/pages/Estimator";
import CivilScope from "@/pages/CivilScope";
import InfraExternal from "@/pages/InfraExternal";
import UtilitiesProcess from "@/pages/UtilitiesProcess";
import ReportsExport from "@/pages/ReportsExport";

function App() {
  return (
    <div className="App">
      <BrowserRouter>
        <Routes>
          <Route
            path="/"
            element={<Navigate to="/estimator" replace />}
          />

          <Route
            path="/estimator"
            element={<Estimator />}
          />

          <Route
            path="/civil-scope"
            element={<CivilScope />}
          />

          <Route
            path="/infra-external"
            element={<InfraExternal />}
          />

          <Route
            path="/utilities-process"
            element={<UtilitiesProcess />}
          />

          <Route
            path="/reports"
            element={<ReportsExport />}
          />
        </Routes>
      </BrowserRouter>

      <Toaster
        position="top-right"
        richColors
      />
    </div>
  );
}

export default App;
