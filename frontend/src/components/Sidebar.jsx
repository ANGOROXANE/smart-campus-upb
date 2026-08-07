import { Link } from "react-router-dom";

function Sidebar() {
  return (
    <aside className="w-64 bg-gray-900 text-white min-h-screen p-5">
      <h1 className="text-2xl font-bold mb-8">
        Smart Campus UPB
      </h1>

      <nav className="space-y-4">
        <Link to="/" className="block">
            Accueil
        </Link>

        <Link to="/temps-reel" className="block">
            Temps réel
        </Link>

        <Link to="/carte" className="block">
            Carte
        </Link>

        <Link to="/historique" className="block">
            Historique
        </Link>

        <Link to="/alertes" className="block">
            Alertes
        </Link>

        <Link to="/administration" className="block">
            Administration
        </Link>
      </nav>
    </aside>
  );
}

export default Sidebar;