import { useEffect, useState } from "react";
import { api } from "../services/api";

function Carte() {
  const [rooms, setRooms] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    async function loadRooms() {
      try {
        const data = await api.getRooms();
        setRooms(data);
      } catch (err) {
        console.error(err);
        setError("Impossible de récupérer les salles.");
      } finally {
        setLoading(false);
      }
    }

    loadRooms();
  }, []);

  const buildings = Object.values(
    rooms.reduce((acc, room) => {
      const buildingName = room.building;

      if (!acc[buildingName]) {
        acc[buildingName] = {
          name: buildingName,
          rooms: 0,
        };
      }

      acc[buildingName].rooms += 1;

      return acc;
    }, {})
  );

  return (
    <div>
      <h1 className="text-3xl font-bold mb-6">
        Carte du campus UPB
      </h1>

      {loading && (
        <p className="text-gray-600">
          Chargement des bâtiments...
        </p>
      )}

      {error && (
        <p className="text-red-600">
          {error}
        </p>
      )}

      {!loading && !error && buildings.length === 0 && (
        <div className="bg-white rounded-xl shadow p-6">
          <p className="text-gray-600">
            Aucune salle ou bâtiment disponible pour le moment.
          </p>
        </div>
      )}

      {!loading && !error && buildings.length > 0 && (
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          {buildings.map((building) => (
            <div
              key={building.name}
              className="bg-white rounded-xl shadow p-6"
            >
              <div className="text-4xl">
                🏢
              </div>

              <h2 className="text-xl font-bold mt-3">
                {building.name}
              </h2>

              <p className="mt-2">
                Salles : {building.rooms}
              </p>

              <p className="mt-2">
                État : Normal
              </p>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

export default Carte;