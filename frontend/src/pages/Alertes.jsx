import { useEffect, useState } from "react";
import { api } from "../services/api";

function Alertes() {
  const [alerts, setAlerts] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  const loadAlerts = async () => {
    try {
      setError(null);

      const measurements = await api.getLatestMeasurements(50);

      const generatedAlerts = [];

      measurements.forEach((measurement) => {
        // Alerte température
        if (
          measurement.temperature !== null &&
          measurement.temperature !== undefined &&
          measurement.temperature >= 30
        ) {
          generatedAlerts.push({
            type: "🌡️ Température",
            message: `Température élevée dans la salle ${measurement.room} : ${measurement.temperature} °C`,
            level: "Attention",
          });
        }

        // Information de présence
        if (measurement.presence === true) {
          generatedAlerts.push({
            type: "👤 Présence",
            message: `Présence détectée dans la salle ${measurement.room}`,
            level: "Information",
          });
        }
      });

      setAlerts(generatedAlerts);
    } catch (err) {
      console.error(err);
      setError("Impossible de récupérer les alertes.");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadAlerts();

    // Actualisation automatique toutes les 10 secondes
    const interval = setInterval(loadAlerts, 10000);

    return () => clearInterval(interval);
  }, []);

  return (
    <div>
      <h1 className="text-3xl font-bold mb-6">
        Alertes système
      </h1>

      {loading && (
        <p className="text-gray-600">
          Chargement des alertes...
        </p>
      )}

      {error && (
        <p className="text-red-600">
          {error}
        </p>
      )}

      {!loading && !error && alerts.length === 0 && (
        <div className="bg-white p-5 rounded-xl shadow">
          <p className="text-gray-600">
            Aucune alerte actuellement.
          </p>
        </div>
      )}

      {!loading && !error && alerts.length > 0 && (
        <div className="space-y-4">
          {alerts.map((alert, index) => (
            <div
              key={index}
              className="bg-white p-5 rounded-xl shadow"
            >
              <h2 className="text-xl font-bold">
                {alert.type}
              </h2>

              <p className="mt-2">
                {alert.message}
              </p>

              <span className="font-semibold block mt-2">
                Niveau : {alert.level}
              </span>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

export default Alertes;