import { BrowserRouter, HashRouter, Route, Routes } from "react-router-dom";
import { GradingPage } from "./pages/GradingPage";
import { SettingsPage } from "./pages/SettingsPage";

const Router = import.meta.env.PROD ? HashRouter : BrowserRouter;

export function App() {
  return (
    <Router>
      <Routes>
        <Route path="/" element={<GradingPage />} />
        <Route path="/settings" element={<SettingsPage />} />
        <Route path="*" element={<GradingPage />} />
      </Routes>
    </Router>
  );
}
