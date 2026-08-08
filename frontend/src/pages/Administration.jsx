function Administration() {

  return (
    <div>

      <h1 className="text-3xl font-bold mb-6">
        Administration
      </h1>


      <div className="grid md:grid-cols-3 gap-6">

        <div className="bg-white p-6 rounded-xl shadow">
          👤
          <h2 className="font-bold">
            Utilisateurs
          </h2>
          <p>25 administrateurs</p>
        </div>


        <div className="bg-white p-6 rounded-xl shadow">
          📡
          <h2 className="font-bold">
            Capteurs
          </h2>
          <p>120 capteurs enregistrés</p>
        </div>


        <div className="bg-white p-6 rounded-xl shadow">
          📋
          <h2 className="font-bold">
            Journal événements
          </h2>
          <p>350 événements</p>
        </div>

      </div>

    </div>
  );
}


export default Administration;