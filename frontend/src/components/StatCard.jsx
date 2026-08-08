function StatCard({ title, value }) {
  return (
    <div className="bg-white p-6 rounded-xl shadow">

      <h3 className="text-gray-500 mt-3">
        {title}
      </h3>

      <p className="text-3xl font-bold">
        {value}
      </p>
    </div>
  );
}

export default StatCard;