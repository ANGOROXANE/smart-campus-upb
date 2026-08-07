import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer
} from "recharts";


function Historique() {

  const data = [
    {
      heure: "08h",
      temperature: 24,
    },
    {
      heure: "10h",
      temperature: 26,
    },
    {
      heure: "12h",
      temperature: 30,
    },
    {
      heure: "14h",
      temperature: 28,
    },
    {
      heure: "16h",
      temperature: 27,
    },
  ];


  return (
    <div>

      <h1 className="text-3xl font-bold mb-6">
        Historique des données
      </h1>


      <div className="bg-white p-6 rounded-xl shadow">

        <h2 className="text-xl font-semibold mb-4">
          Évolution température
        </h2>


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
            />

          </LineChart>

        </ResponsiveContainer>

      </div>

    </div>
  );
}

export default Historique;