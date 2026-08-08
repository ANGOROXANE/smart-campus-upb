function TempsReel() {
  const sensors = [
    {
      name: "Température Salle A101",
      value: "27 °C",
    },
    {
      name: "Humidité",
      value: "65 %",
    },
    {
      name: "Présence",
      value: "Oui",
    },
    {
      name: "Consommation électrique",
      value: "4.5 kW",
    },
    {
      name: "Qualité de l'air",
      value: "Bonne",
    },
    {
      name: "Porte principale",
      value: "Fermée",
    },
  ];

  return (
    <div>
      <h1 className="text-3xl font-bold mb-6">
        Temps réel des capteurs
      </h1>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        {sensors.map((sensor, index) => (
          <div
            key={index}
            className="bg-white p-6 rounded-xl shadow"
          >
            <div className="text-4xl">
              {sensor.icon}
            </div>

            <h2 className="font-semibold mt-3">
              {sensor.name}
            </h2>

            <p className="text-2xl font-bold mt-2">
              {sensor.value}
            </p>
          </div>
        ))}
      </div>
    </div>
  );
}

export default TempsReel;