import { useState } from "react";
import { FolderOpen, PlusCircle, PieChart, Users, Building2, Wallet } from "lucide-react";

export default function AppMockup() {
  const [activeTab, setActiveTab] = useState("overview");
  const [remainingBudget, setRemainingBudget] = useState(60000);
  const [spentVenue, setSpentVenue] = useState(65000);

  const [vendors, setVendors] = useState([
    { id: 1, name: "Austin Convention Center", category: "Venue", status: "Secured", statusColor: "emerald" },
    { id: 2, name: "Apex AV Solutions", category: "Production", status: "Pending", statusColor: "amber" },
  ]);

  const handleAddExpense = () => {
    if (remainingBudget >= 2500) {
      setRemainingBudget((prev) => prev - 2500);
      setSpentVenue((prev) => prev + 2500);
      setVendors((prev) => [
        ...prev,
        {
          id: Date.now(),
          name: `Misc Vendor ${Math.floor(Math.random() * 1000)}`,
          category: "Logistics",
          status: "Reviewing",
          statusColor: "blue",
        },
      ]);
    }
  };

  const navItems = [
    { id: "overview", icon: PieChart, label: "Overview" },
    { id: "attendees", icon: Users, label: "Attendees" },
    { id: "venues", icon: Building2, label: "Venues" },
    { id: "budget", icon: Wallet, label: "Budget" },
  ];

  const totalBudget = 150000;
  const venuePercentage = (spentVenue / totalBudget) * 100;

  return (
    <div className="rounded-xl border border-zinc-200/80 bg-white shadow-2xl shadow-zinc-200/50 flex flex-col overflow-hidden transition-all duration-500">
      {/* App Header */}
      <div className="h-12 border-b border-zinc-100 flex items-center px-4 justify-between bg-zinc-50/50">
        <div className="flex items-center gap-3">
          <div className="flex gap-1.5">
            <div className="w-2.5 h-2.5 rounded-full bg-zinc-200" />
            <div className="w-2.5 h-2.5 rounded-full bg-zinc-200" />
            <div className="w-2.5 h-2.5 rounded-full bg-zinc-200" />
          </div>
          <div className="h-4 w-px bg-zinc-200 mx-2" />
          <span className="text-xs font-medium text-zinc-500 flex items-center gap-2">
            <FolderOpen className="w-3.5 h-3.5" /> Global Tech Summit 2024
          </span>
        </div>
        <div className="flex items-center gap-3">
          <div className="h-6 w-32 sm:w-48 bg-zinc-100 rounded-md border border-zinc-200" />
          <div className="w-6 h-6 rounded-full bg-zinc-200 border border-zinc-300" />
        </div>
      </div>

      {/* App Body */}
      <div className="flex h-[400px] md:h-[450px]">
        {/* Sidebar */}
        <div className="w-48 border-r border-zinc-100 bg-zinc-50/30 p-3 hidden sm:flex flex-col gap-1 text-xs font-medium text-zinc-600">
          {navItems.map((item) => (
            <button
              key={item.id}
              onClick={() => setActiveTab(item.id)}
              className={`px-2 py-1.5 rounded-md flex items-center gap-2 transition-colors w-full text-left ${
                activeTab === item.id ? "bg-zinc-100 text-zinc-900" : "hover:bg-zinc-100/50 text-zinc-500"
              }`}
            >
              <item.icon className="w-4 h-4" /> {item.label}
            </button>
          ))}
        </div>

        {/* Main Content */}
        <div className="flex-1 p-6 bg-white overflow-hidden flex flex-col gap-6">
          <div className="flex justify-between items-end">
            <div>
              <h3 className="text-lg font-semibold tracking-tight text-zinc-900">Budget Allocation</h3>
              <p className="text-xs text-zinc-500 mt-1">Tracked against ${totalBudget.toLocaleString()} total budget</p>
            </div>
            <button
              onClick={handleAddExpense}
              className="px-3 py-1.5 bg-zinc-900 text-white rounded-md text-xs font-medium shadow-sm hover:bg-zinc-800 active:scale-95 transition-all flex items-center gap-1.5"
            >
              <PlusCircle className="w-3.5 h-3.5" />
              Add Expense
            </button>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div className="md:col-span-2 p-4 rounded-lg border border-zinc-100 bg-zinc-50/50 flex flex-col gap-3">
              <div className="flex justify-between text-xs text-zinc-500 font-medium">
                <span>Venue & Catering</span>
                <span className="text-zinc-900">${spentVenue.toLocaleString()}</span>
              </div>
              <div className="w-full h-1.5 rounded-full bg-zinc-200 overflow-hidden">
                <div
                  className="h-full bg-zinc-800 rounded-full transition-all duration-500 ease-out"
                  style={{ width: `${Math.min(venuePercentage, 100)}%` }}
                />
              </div>
              <div className="flex justify-between text-xs text-zinc-500 font-medium mt-2">
                <span>Marketing</span>
                <span className="text-zinc-900">$25,000</span>
              </div>
              <div className="w-full h-1.5 rounded-full bg-zinc-200 overflow-hidden">
                <div className="w-[16%] h-full bg-zinc-400 rounded-full" />
              </div>
            </div>
            <div className="md:col-span-1 p-4 rounded-lg border border-zinc-100 bg-zinc-50/50 flex flex-col justify-center items-center text-center">
              <span className="text-xs text-zinc-500 font-medium mb-1">Remaining</span>
              <span className={`text-2xl font-semibold tracking-tight transition-colors duration-300 ${remainingBudget < 20000 ? "text-red-600" : "text-zinc-900"}`}>
                ${remainingBudget.toLocaleString()}
              </span>
            </div>
          </div>

          <div className="flex-1 border border-zinc-100 rounded-lg overflow-hidden flex flex-col">
            <div className="grid grid-cols-4 px-4 py-2 bg-zinc-50/80 border-b border-zinc-100 text-xs font-medium text-zinc-500">
              <div className="col-span-2">Vendor</div>
              <div>Category</div>
              <div className="text-right">Status</div>
            </div>
            <div className="overflow-y-auto flex-1">
              {vendors.map((vendor) => (
                <div key={vendor.id} className="grid grid-cols-4 px-4 py-3 border-b border-zinc-50 text-xs items-center hover:bg-zinc-50/50 transition-colors">
                  <div className="col-span-2 font-medium text-zinc-900 truncate pr-4">{vendor.name}</div>
                  <div className="text-zinc-500">{vendor.category}</div>
                  <div className="text-right">
                    <span className={`px-2 py-1 rounded-md font-medium border text-[10px] sm:text-xs
                      ${vendor.statusColor === "emerald" ? "bg-emerald-50 text-emerald-600 border-emerald-100" : ""}
                      ${vendor.statusColor === "amber" ? "bg-amber-50 text-amber-600 border-amber-100" : ""}
                      ${vendor.statusColor === "blue" ? "bg-blue-50 text-blue-600 border-blue-100" : ""}
                    `}>
                      {vendor.status}
                    </span>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
