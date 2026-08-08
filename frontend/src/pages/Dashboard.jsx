import { useEffect, useState } from "react";
import StatCard from "../components/StatCard";
import { api } from "../services/api";

function Dashboard() {
  const [rooms, setRooms] = useState([]);
  const [sensors, setSensors] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function loadDashboard() {
      try {
        const [roomsData, sensorsData] = await Promise.all([
          api.getRooms(),
          api.getSensors(),
        ]);

        setRooms(roomsData);
        setSensors(sensorsData);
      } catch (error) {
        console.error("Erreur lors du chargement du dashboard :", error);
      } finally {
        setLoading(false);
      }
    }

    loadDashboard();
  }, []);

  return (
    <div>
      <h1 className="text-3xl font-bold mb-6">
        Smart Campus UPB
      </h1>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        <StatCard
          title="Bâtiments"
          value={loading ? "..." : "—"}
        />

        <StatCard
          title="Salles"
          value={loading ? "..." : rooms.length}
        />

        <StatCard
          title="Capteurs actifs"
          value={loading ? "..." : sensors.length}
        />

        <StatCard
          title="Capteurs hors ligne"
          value="—"
        />
      </div>
    </div>
  );
}

export default Dashboard;