import { BrowserRouter, Routes, Route } from "react-router-dom";

import Dashboard from "./pages/Dashboard";
import TempsReel from "./pages/TempsReel";
import Carte from "./pages/Carte";
import Historique from "./pages/Historique";
import Alertes from "./pages/Alertes";
import Administration from "./pages/Administration";

import Sidebar from "./components/Sidebar";
import Navbar from "./components/Navbar";

function App() {
  return (
    <BrowserRouter>
      <div className="flex min-h-screen bg-gray-100">
        <Sidebar />

        <div className="flex-1">
          <Navbar />

          <main className="p-6">
            <Routes>
              <Route path="/" element={<Dashboard />} />
              <Route path="/temps-reel" element={<TempsReel />} />
              <Route path="/carte" element={<Carte />} />
              <Route path="/historique" element={<Historique />} />
              <Route path="/alertes" element={<Alertes />} />
              <Route path="/administration" element={<Administration />} />
            </Routes>
          </main>
        </div>
      </div>
    </BrowserRouter>
  );
}

export default App;