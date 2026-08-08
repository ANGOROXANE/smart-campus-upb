import { useEffect, useState } from "react";
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
} from "recharts";
import { api } from "../services/api";

function Historique() {
  const [data, setData] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  const loadHistory = async () => {
    try {
      setError(null);

      const measurements = await api.getMeasurementHistory("-24h");

      const chartData = measurements
        .filter(
          (measurement) =>
            measurement.temperature !== null &&
            measurement.temperature !== undefined
        )
        .map((measurement) => ({
          heure: new Date(measurement.timestamp).toLocaleTimeString(
            "fr-FR",
            {
              hour: "2-digit",
              minute: "2-digit",
            }
          ),
          temperature: measurement.temperature,
        }));

      setData(chartData);
    } catch (err) {
      console.error(err);
      setError("Impossible de récupérer l'historique.");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadHistory();
  }, []);

  return (
    <div>
      <h1 className="text-3xl font-bold mb-6">
        Historique des données
      </h1>

      <div className="bg-white p-6 rounded-xl shadow">
        <h2 className="text-xl font-semibold mb-4">
          Évolution température — dernières 24h
        </h2>

        {loading && (
          <p className="text-gray-600">
            Chargement de l'historique...
          </p>
        )}

        {error && (
          <p className="text-red-600">
            {error}
          </p>
        )}

        {!loading && !error && data.length === 0 && (
          <p className="text-gray-600">
            Aucune donnée historique disponible pour le moment.
          </p>
        )}

        {!loading && !error && data.length > 0 && (
          <ResponsiveContainer width="100%" height={300}>
            <LineChart data={data}>
              <CartesianGrid />

              <XAxis dataKey="heure" />

              <YAxis />

              <Tooltip />

              <Line
                type="monotone"
                dataKey="temperature"
                strokeWidth={3}
                name="Température"
              />
            </LineChart>
          </ResponsiveContainer>
        )}
      </div>
    </div>
  );
}

export default Historique;