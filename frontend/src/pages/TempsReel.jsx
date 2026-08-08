import { useEffect, useState } from "react";
import { api } from "../services/api";

function TempsReel() {
  const [measurements, setMeasurements] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  const loadMeasurements = async () => {
    try {
      setError(null);

      const data = await api.getLatestMeasurements(10);

      setMeasurements(data);
    } catch (err) {
      console.error(err);
      setError("Impossible de récupérer les mesures.");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadMeasurements();

    // Actualisation automatique toutes les 10 secondes
    const interval = setInterval(loadMeasurements, 10000);

    return () => clearInterval(interval);
  }, []);

  if (loading) {
    return (
      <div>
        <h1 className="text-3xl font-bold mb-6">
          Temps réel des capteurs
        </h1>

        <p>Chargement des mesures...</p>
      </div>
    );
  }

  if (error) {
    return (
      <div>
        <h1 className="text-3xl font-bold mb-6">
          Temps réel des capteurs
        </h1>

        <p className="text-red-600">{error}</p>
      </div>
    );
  }

  return (
    <div>
      <h1 className="text-3xl font-bold mb-6">
        Temps réel des capteurs
      </h1>

      {measurements.length === 0 ? (
        <div className="bg-white p-6 rounded-xl shadow">
          <p className="text-gray-600">
            Aucune mesure disponible pour le moment.
          </p>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          {measurements.map((measurement, index) => (
            <div
              key={`${measurement.room}-${measurement.sensor}-${index}`}
              className="bg-white p-6 rounded-xl shadow"
            >
              <div className="text-4xl">
                🌡️
              </div>

              <h2 className="font-semibold mt-3">
                Salle {measurement.room}
              </h2>

              <p className="text-gray-600 mt-1">
                Capteur : {measurement.sensor}
              </p>

              {measurement.temperature !== null &&
                measurement.temperature !== undefined && (
                  <p className="text-2xl font-bold mt-2">
                    {measurement.temperature} °C
                  </p>
                )}

              {measurement.presence !== null &&
                measurement.presence !== undefined && (
                  <p className="mt-2">
                    Présence :{" "}
                    <strong>
                      {measurement.presence ? "Oui" : "Non"}
                    </strong>
                  </p>
                )}

              <p className="text-sm text-gray-500 mt-3">
                {new Date(measurement.timestamp).toLocaleString("fr-FR")}
              </p>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

export default TempsReel;