function Carte() {

  const buildings = [
    {
      name: "Bâtiment A",
      rooms: 15,
      status: "Normal",
      color: "🟢"
    },
    {
      name: "Bâtiment B",
      rooms: 20,
      status: "Alerte température",
      color: "🔴"
    },
    {
      name: "Bâtiment C",
      rooms: 10,
      status: "Occupation élevée",
      color: "🟠"
    }
  ];


  return (
    <div>

      <h1 className="text-3xl font-bold mb-6">
        Carte du campus UPB
      </h1>


      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">

        {buildings.map((building,index)=>(

          <div
            key={index}
            className="bg-white rounded-xl shadow p-6"
          >

            <div className="text-4xl">
              {building.color}
            </div>

            <h2 className="text-xl font-bold mt-3">
              {building.name}
            </h2>

            <p>
              Salles : {building.rooms}
            </p>

            <p>
              Etat : {building.status}
            </p>

          </div>

        ))}

      </div>

    </div>
  );
}


export default Carte;