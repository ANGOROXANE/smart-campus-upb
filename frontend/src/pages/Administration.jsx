import { useEffect, useState } from "react";
import { api } from "../services/api";

function Administration() {
  const [sensors, setSensors] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function loadSensors() {
      try {
        const data = await api.getSensors();
        setSensors(data);
      } catch (error) {
        console.error(
          "Erreur lors du chargement des capteurs :",
          error
        );
      } finally {
        setLoading(false);
      }
    }

    loadSensors();
  }, []);

  return (
    <div>
      <h1 className="text-3xl font-bold mb-6">
        Administration
      </h1>

      <div className="grid md:grid-cols-3 gap-6">

        <div className="bg-white p-6 rounded-xl shadow">
          <div className="text-3xl mb-3">
            👤
          </div>

          <h2 className="font-bold">
            Utilisateurs
          </h2>

          <p className="mt-2">
            Gestion des utilisateurs
          </p>

          <p className="text-sm text-gray-500 mt-2">
            Données utilisateurs non disponibles via l'API actuelle.
          </p>
        </div>

        <div className="bg-white p-6 rounded-xl shadow">
          <div className="text-3xl mb-3">
            📡
          </div>

          <h2 className="font-bold">
            Capteurs
          </h2>

          <p className="mt-2">
            {loading
              ? "Chargement..."
              : `${sensors.length} capteur${
                  sensors.length > 1 ? "s" : ""
                } enregistré${
                  sensors.length > 1 ? "s" : ""
                }`}
          </p>
        </div>

        <div className="bg-white p-6 rounded-xl shadow">
          <div className="text-3xl mb-3">
            📋
          </div>

          <h2 className="font-bold">
            Journal événements
          </h2>

          <p className="mt-2">
            Journal des événements
          </p>

          <p className="text-sm text-gray-500 mt-2">
            Données événements non disponibles via l'API actuelle.
          </p>
        </div>

      </div>
    </div>
  );
}

export default Administration;