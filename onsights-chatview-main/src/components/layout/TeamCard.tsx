import React from "react";

const members = ["Anna", "Daniel", "Sandra", "Nicolas"];

const TeamCard = () => (
  <div className="flex flex-col items-center justify-center bg-gradient-to-r from-yellow-400 via-orange-400 to-yellow-600 rounded-xl shadow-lg p-4 mb-4 mt-2">
    <h2 className="text-xl font-bold text-white mb-2 tracking-wide drop-shadow">Integrantes do Grupo</h2>
    <div className="flex gap-4">
      {members.map((name) => (
        <div key={name} className="bg-black/40 text-yellow-200 px-4 py-2 rounded-lg font-semibold shadow">
          {name}
        </div>
      ))}
    </div>
  </div>
);

export default TeamCard;
