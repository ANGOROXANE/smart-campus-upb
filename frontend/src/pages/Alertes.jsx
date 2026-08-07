function Alertes() {

  const alerts = [
    {
      type: " Incendie",
      message: "Fumée détectée salle B203",
      level: "Critique",
    },

    {
      type: " Température",
      message: "Température élevée salle A101",
      level: "Attention",
    },

    {
      type: " Capteur",
      message: "Capteur humidité hors ligne",
      level: "Erreur",
    },

    {
      type: " Sécurité",
      message: "Salle occupée après fermeture",
      level: "Attention",
    },
  ];


  return (
    <div>

      <h1 className="text-3xl font-bold mb-6">
        Alertes système
      </h1>


      <div className="space-y-4">

        {alerts.map((alert,index)=>(

          <div
            key={index}
            className="bg-white p-5 rounded-xl shadow"
          >

            <h2 className="text-xl font-bold">
              {alert.type}
            </h2>

            <p>
              {alert.message}
            </p>

            <span className="font-semibold">
              Niveau : {alert.level}
            </span>

          </div>

        ))}

      </div>

    </div>
  );
}


export default Alertes;