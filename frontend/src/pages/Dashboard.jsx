import StatCard from "../components/StatCard";

function Dashboard() {
  return (
    <div>
      <h1 className="text-3xl font-bold mb-6">
        Smart Campus UPB
      </h1>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">

        <StatCard
          title="Bâtiments"
          value="5"
        />

        <StatCard
          title="Salles"
          value="50"
        />

        <StatCard
          title="Capteurs actifs"
          value="120"
        />

        <StatCard
          title="Capteurs hors ligne"
          value="3"
        />

      </div>
    </div>
  );
}

export default Dashboard;