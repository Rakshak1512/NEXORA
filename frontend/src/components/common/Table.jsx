import React from 'react';

const Table = ({ headers, children, emptyMessage = "No records found" }) => {
  return (
    <div className="w-full overflow-x-auto rounded-xl border border-[#1A2740]">
      <table className="w-full text-left text-sm text-slate-300">
        <thead className="bg-[#0A1220] text-xs uppercase tracking-wider text-slate-400 border-b border-[#1A2740]">
          <tr>
            {headers.map((h, i) => (
              <th key={i} className="px-5 py-3.5 font-semibold">
                {h}
              </th>
            ))}
          </tr>
        </thead>
        <tbody className="divide-y divide-[#1A2740]/60 bg-[#0D1524]/60">
          {children}
        </tbody>
      </table>
    </div>
  );
};

export default Table;

