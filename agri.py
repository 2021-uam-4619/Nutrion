import React, { useState, useEffect, useMemo } from 'react';
import { 
  LayoutDashboard, 
  Sprout, 
  Beef, 
  Droplets, 
  Receipt, 
  FileText, 
  Plus, 
  Trash2, 
  Edit3, 
  TrendingUp, 
  User,
  Clock,
  Wallet,
  CheckCircle2,
  AlertCircle
} from 'lucide-react';

const App = () => {
  // --- State Management ---
  const [activeTab, setActiveTab] = useState('livestock');
  const [transactions, setTransactions] = useState([]);
  const [editingId, setEditingId] = useState(null);

  // --- Initial State Form Logic ---
  const [formData, setFormData] = useState({
    date: new Date().toISOString().split('T')[0],
    category: 'livestock', // livestock, crop, water, operational
    subCategory: 'Wanda',
    description: '',
    amount: '',
    managedBy: 'Self',
    paidAmount: '',
    animalType: 'Cow', // For livestock
    cropName: 'Wheat', // For crops
    farmerName: '',    // For water
    startTime: '',     // For water
    endTime: '',       // For water
    rate: '',          // For water
    type: 'Expense'    // Expense or Income
  });

  // --- Calculations ---
  const stats = useMemo(() => {
    const totals = {
      livestockExp: 0,
      cropExp: 0,
      waterInc: 0,
      opExp: 0,
      totalPayable: 0,
      totalReceivable: 0
    };

    transactions.forEach(t => {
      const amount = parseFloat(t.amount || 0);
      const paid = parseFloat(t.paidAmount || 0);
      
      if (t.category === 'livestock') totals.livestockExp += amount;
      if (t.category === 'crop') totals.cropExp += amount;
      if (t.category === 'water') totals.waterInc += amount;
      if (t.category === 'operational') totals.opExp += amount;

      if (t.type === 'Expense') {
        totals.totalPayable += (amount - paid);
      } else if (t.type === 'Income') {
        totals.totalReceivable += (amount - paid);
      }
    });

    return totals;
  }, [transactions]);

  // --- Handlers ---
  const handleInputChange = (e) => {
    const { name, value } = e.target;
    setFormData(prev => ({ ...prev, [name]: value }));
  };

  const calculateWaterBill = () => {
    if (formData.startTime && formData.endTime && formData.rate) {
      // Split time string to avoid any literal parsing issues
      const [startH, startM] = formData.startTime.split(':').map(Number);
      const [endH, endM] = formData.endTime.split(':').map(Number);
      
      const startInMinutes = startH * 60 + startM;
      const endInMinutes = endH * 60 + endM;
      
      let diffInMinutes = endInMinutes - startInMinutes;
      if (diffInMinutes < 0) diffInMinutes += 24 * 60; // Handle overnight usage
      
      const hours = diffInMinutes / 60;
      return (hours * parseFloat(formData.rate)).toFixed(2);
    }
    return 0;
  };

  const saveTransaction = (e) => {
    e.preventDefault();
    let finalAmount = formData.amount;
    if (formData.category === 'water') {
      finalAmount = calculateWaterBill();
    }

    const newEntry = {
      ...formData,
      id: editingId || Date.now(),
      amount: finalAmount,
      timestamp: new Date().toLocaleString()
    };

    if (editingId) {
      setTransactions(transactions.map(t => t.id === editingId ? newEntry : t));
      setEditingId(null);
    } else {
      setTransactions([newEntry, ...transactions]);
    }

    // Reset Form based on current tab context
    setFormData({
      date: new Date().toISOString().split('T')[0],
      category: activeTab,
      subCategory: activeTab === 'livestock' ? 'Wanda' : activeTab === 'crop' ? 'Khad' : activeTab === 'operational' ? 'Salary' : 'Other',
      description: '',
      amount: '',
      managedBy: 'Self',
      paidAmount: '',
      animalType: 'Cow',
      cropName: 'Wheat',
      farmerName: '',
      startTime: '',
      endTime: '',
      rate: '',
      type: activeTab === 'water' ? 'Income' : 'Expense'
    });
  };

  const deleteTransaction = (id) => {
    setTransactions(transactions.filter(t => t.id !== id));
  };

  const editTransaction = (t) => {
    setFormData(t);
    setEditingId(t.id);
    setActiveTab(t.category);
    window.scrollTo({ top: 0, behavior: 'smooth' });
  };

  // --- Components ---
  const Card = ({ children, className = "" }) => (
    <div className={`bg-white rounded-xl shadow-sm border border-slate-200 p-6 ${className}`}>
      {children}
    </div>
  );

  const StatBox = ({ label, value, color, icon: Icon }) => (
    <Card className="flex items-center gap-4">
      <div className={`p-3 rounded-lg ${color} bg-opacity-10`}>
        <Icon className={`w-6 h-6 ${color.replace('bg-', 'text-')}`} />
      </div>
      <div>
        <p className="text-sm text-slate-500 font-medium uppercase tracking-wider">{label}</p>
        <p className="text-2xl font-bold text-slate-800">Rs. {Number(value).toLocaleString()}</p>
      </div>
    </Card>
  );

  return (
    <div className="min-h-screen bg-slate-50 font-sans text-slate-900">
      {/* Sidebar Navigation */}
      <nav className="fixed left-0 top-0 h-full w-20 md:w-64 bg-slate-900 text-slate-400 flex flex-col items-center py-8 z-50">
        <div className="mb-10 px-6 flex items-center gap-3 w-full">
          <div className="bg-emerald-500 p-2 rounded-lg">
            <LayoutDashboard className="text-white w-6 h-6" />
          </div>
          <span className="hidden md:block text-white font-bold text-xl tracking-tight">FarmLedger</span>
        </div>
        
        <div className="flex flex-col gap-2 w-full px-4">
          {[
            { id: 'livestock', icon: Beef, label: 'Livestock' },
            { id: 'crop', icon: Sprout, label: 'Crops' },
            { id: 'water', icon: Droplets, label: 'Water Income' },
            { id: 'operational', icon: Receipt, label: 'Operations' },
            { id: 'reports', icon: FileText, label: 'Reports' },
          ].map((item) => (
            <button
              key={item.id}
              onClick={() => {
                setActiveTab(item.id);
                setEditingId(null);
                setFormData(prev => ({
                    ...prev,
                    category: item.id,
                    type: item.id === 'water' ? 'Income' : 'Expense'
                }));
              }}
              className={`flex items-center gap-4 p-3 rounded-xl transition-all ${
                activeTab === item.id 
                ? 'bg-emerald-600 text-white shadow-lg shadow-emerald-900/20' 
                : 'hover:bg-slate-800 hover:text-slate-200'
              }`}
            >
              <item.icon className="w-6 h-6" />
              <span className="hidden md:block font-medium">{item.label}</span>
            </button>
          ))}
        </div>
      </nav>

      {/* Main Content */}
      <main className="ml-20 md:ml-64 p-4 md:p-8">
        <header className="mb-8 flex flex-col md:flex-row md:items-center justify-between gap-4">
          <div>
            <h1 className="text-3xl font-bold text-slate-800 capitalize">{activeTab.replace('-', ' ')} Management</h1>
            <p className="text-slate-500">Manage your farm activities and ledger balances.</p>
          </div>
          <div className="flex items-center gap-3">
            <span className="text-sm bg-slate-200 px-3 py-1 rounded-full font-medium text-slate-700">
              {new Date().toDateString()}
            </span>
          </div>
        </header>

        {/* Dashboard Stats (Top Section) */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
          <StatBox label="Livestock Exp" value={stats.livestockExp} color="bg-orange-500" icon={Beef} />
          <StatBox label="Crop Exp" value={stats.cropExp} color="bg-emerald-500" icon={Sprout} />
          <StatBox label="Water Income" value={stats.waterInc} color="bg-blue-500" icon={Droplets} />
          <StatBox label="Net Balance" value={stats.waterInc - (stats.livestockExp + stats.cropExp + stats.opExp)} color="bg-purple-500" icon={TrendingUp} />
        </div>

        {activeTab !== 'reports' ? (
          <div className="grid grid-cols-1 xl:grid-cols-3 gap-8">
            {/* Input Form Column */}
            <div className="xl:col-span-1">
              <Card>
                <div className="flex items-center gap-2 mb-6 border-b pb-4">
                  <Plus className="text-emerald-600 w-5 h-5" />
                  <h2 className="text-lg font-bold text-slate-800">{editingId ? 'Edit Entry' : 'New Entry'}</h2>
                </div>
                
                <form onSubmit={saveTransaction} className="space-y-4">
                  <div className="grid grid-cols-2 gap-4">
                    <div className="col-span-2">
                      <label className="block text-xs font-bold text-slate-500 mb-1 uppercase">Date</label>
                      <input type="date" name="date" value={formData.date} onChange={handleInputChange} className="w-full bg-slate-50 border border-slate-200 rounded-lg px-4 py-2 focus:ring-2 focus:ring-emerald-500 outline-none" required />
                    </div>

                    {activeTab === 'livestock' && (
                      <div className="col-span-2">
                        <label className="block text-xs font-bold text-slate-500 mb-1 uppercase">Animal Type</label>
                        <select name="animalType" value={formData.animalType} onChange={handleInputChange} className="w-full bg-slate-50 border border-slate-200 rounded-lg px-4 py-2">
                          <option>Cow</option>
                          <option>Goat</option>
                          <option>Buffalo</option>
                          <option>Sheep</option>
                          <option>Others</option>
                        </select>
                      </div>
                    )}

                    {activeTab === 'crop' && (
                      <div className="col-span-2">
                        <label className="block text-xs font-bold text-slate-500 mb-1 uppercase">Crop Name</label>
                        <input type="text" name="cropName" value={formData.cropName} onChange={handleInputChange} className="w-full bg-slate-50 border border-slate-200 rounded-lg px-4 py-2" placeholder="e.g. Wheat, Rice" />
                      </div>
                    )}

                    {activeTab === 'water' ? (
                      <>
                        <div className="col-span-2">
                          <label className="block text-xs font-bold text-slate-500 mb-1 uppercase">Farmer Name</label>
                          <input type="text" name="farmerName" value={formData.farmerName} onChange={handleInputChange} className="w-full bg-slate-50 border border-slate-200 rounded-lg px-4 py-2" required />
                        </div>
                        <div>
                          <label className="block text-xs font-bold text-slate-500 mb-1 uppercase">Start Time</label>
                          <input type="time" name="startTime" value={formData.startTime} onChange={handleInputChange} className="w-full bg-slate-50 border border-slate-200 rounded-lg px-4 py-2" />
                        </div>
                        <div>
                          <label className="block text-xs font-bold text-slate-500 mb-1 uppercase">End Time</label>
                          <input type="time" name="endTime" value={formData.endTime} onChange={handleInputChange} className="w-full bg-slate-50 border border-slate-200 rounded-lg px-4 py-2" />
                        </div>
                        <div className="col-span-2">
                          <label className="block text-xs font-bold text-slate-500 mb-1 uppercase">Rate / Hour (Rs)</label>
                          <input type="number" name="rate" value={formData.rate} onChange={handleInputChange} className="w-full bg-slate-50 border border-slate-200 rounded-lg px-4 py-2" placeholder="800" />
                        </div>
                      </>
                    ) : (
                      <>
                        <div className="col-span-2">
                          <label className="block text-xs font-bold text-slate-500 mb-1 uppercase">Category</label>
                          <select name="subCategory" value={formData.subCategory} onChange={handleInputChange} className="w-full bg-slate-50 border border-slate-200 rounded-lg px-4 py-2">
                            {activeTab === 'livestock' && (
                              <>
                                <option>Wanda</option>
                                <option>Chokar</option>
                                <option>Khal</option>
                                <option>Tori</option>
                                <option>Khas</option>
                                <option>Others</option>
                              </>
                            )}
                            {activeTab === 'crop' && (
                              <>
                                <option>Khad (Fertilizer)</option>
                                <option>Spray</option>
                                <option>Seed</option>
                                <option>Irrigation</option>
                                <option>Others</option>
                              </>
                            )}
                            {activeTab === 'operational' && (
                              <>
                                <option>Salary</option>
                                <option>Fuel</option>
                                <option>Machinery Purchase</option>
                                <option>Maintenance</option>
                                <option>Others</option>
                              </>
                            )}
                          </select>
                        </div>
                        <div className="col-span-2">
                          <label className="block text-xs font-bold text-slate-500 mb-1 uppercase">Total Amount (Rs)</label>
                          <input type="number" name="amount" value={formData.amount} onChange={handleInputChange} className="w-full bg-slate-50 border border-slate-200 rounded-lg px-4 py-2" required />
                        </div>
                      </>
                    )}

                    <div className="col-span-2">
                      <label className="block text-xs font-bold text-slate-500 mb-1 uppercase">Managed By / Paid By</label>
                      <input type="text" name="managedBy" value={formData.managedBy} onChange={handleInputChange} className="w-full bg-slate-50 border border-slate-200 rounded-lg px-4 py-2" placeholder="e.g. Self, Name of Employee" />
                    </div>

                    <div className="col-span-2">
                      <label className="block text-xs font-bold text-slate-500 mb-1 uppercase">Amount Paid Now (Rs)</label>
                      <input type="number" name="paidAmount" value={formData.paidAmount} onChange={handleInputChange} className="w-full bg-slate-50 border border-slate-200 rounded-lg px-4 py-2" placeholder="Leave empty if fully paid" />
                    </div>

                    <div className="col-span-2 pt-2">
                      <button type="submit" className="w-full bg-emerald-600 hover:bg-emerald-700 text-white font-bold py-3 rounded-lg transition-colors flex items-center justify-center gap-2">
                        <CheckCircle2 className="w-5 h-5" />
                        {editingId ? 'Update Ledger' : 'Confirm & Save'}
                      </button>
                      {editingId && (
                        <button type="button" onClick={() => setEditingId(null)} className="w-full mt-2 text-slate-500 text-sm py-2">Cancel Edit</button>
                      )}
                    </div>
                  </div>
                </form>
              </Card>
            </div>

            {/* List Table Column */}
            <div className="xl:col-span-2 space-y-6">
              <Card className="p-0 overflow-hidden">
                <div className="p-6 border-b bg-slate-50 flex items-center justify-between">
                  <h2 className="font-bold text-slate-800 flex items-center gap-2">
                    <Receipt className="w-5 h-5 text-emerald-600" />
                    Recent Transactions
                  </h2>
                </div>
                <div className="overflow-x-auto">
                  <table className="w-full text-left border-collapse">
                    <thead>
                      <tr className="bg-slate-50 border-b text-slate-400 text-xs font-bold uppercase tracking-wider">
                        <th className="px-6 py-4">Date / Detail</th>
                        <th className="px-6 py-4">Financials</th>
                        <th className="px-6 py-4">Managed By</th>
                        <th className="px-6 py-4 text-right">Actions</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-slate-100">
                      {transactions.filter(t => t.category === activeTab).map(t => {
                        const balance = parseFloat(t.amount || 0) - parseFloat(t.paidAmount || 0);
                        return (
                          <tr key={t.id} className="hover:bg-slate-50 transition-colors group">
                            <td className="px-6 py-4">
                              <p className="font-bold text-slate-800 text-sm">{t.date}</p>
                              <p className="text-xs text-slate-500">
                                {t.category === 'water' ? `Farmer: ${t.farmerName}` : `${t.subCategory} (${t.animalType || t.cropName || ''})`}
                              </p>
                              {t.startTime && <p className="text-[10px] text-slate-400">{t.startTime} - {t.endTime}</p>}
                            </td>
                            <td className="px-6 py-4">
                              <p className={`font-bold text-sm ${t.type === 'Income' ? 'text-blue-600' : 'text-slate-800'}`}>
                                Rs. {Number(t.amount).toLocaleString()}
                              </p>
                              <div className="flex items-center gap-1 mt-1">
                                <span className={`text-[10px] px-1.5 py-0.5 rounded ${balance > 0 ? 'bg-red-100 text-red-600' : 'bg-emerald-100 text-emerald-600'}`}>
                                  {balance > 0 ? `Unpaid: ${balance}` : 'Full Paid'}
                                </span>
                              </div>
                            </td>
                            <td className="px-6 py-4">
                              <div className="flex items-center gap-2">
                                <div className="w-6 h-6 rounded-full bg-slate-200 flex items-center justify-center">
                                  <User className="w-3 h-3 text-slate-500" />
                                </div>
                                <span className="text-xs text-slate-600 font-medium">{t.managedBy}</span>
                              </div>
                            </td>
                            <td className="px-6 py-4 text-right">
                              <div className="flex items-center justify-end gap-2 opacity-0 group-hover:opacity-100 transition-opacity">
                                <button onClick={() => editTransaction(t)} className="p-2 hover:bg-emerald-100 text-emerald-600 rounded-lg">
                                  <Edit3 className="w-4 h-4" />
                                </button>
                                <button onClick={() => deleteTransaction(t.id)} className="p-2 hover:bg-red-100 text-red-600 rounded-lg">
                                  <Trash2 className="w-4 h-4" />
                                </button>
                              </div>
                            </td>
                          </tr>
                        );
                      })}
                      {transactions.filter(t => t.category === activeTab).length === 0 && (
                        <tr>
                          <td colSpan="4" className="px-6 py-12 text-center text-slate-400">
                            No records found for this category.
                          </td>
                        </tr>
                      )}
                    </tbody>
                  </table>
                </div>
              </Card>
            </div>
          </div>
        ) : (
          <div className="space-y-8">
            {/* Reports View */}
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
              <Card>
                <h2 className="text-xl font-bold mb-6 flex items-center gap-2">
                  <AlertCircle className="text-orange-500" />
                  Account Payables (Dues to People)
                </h2>
                <div className="space-y-4">
                  {transactions
                    .filter(t => t.type === 'Expense' && (parseFloat(t.amount) - parseFloat(t.paidAmount || 0)) > 0)
                    .map(t => (
                      <div key={t.id} className="flex justify-between items-center p-3 border-b border-slate-100">
                        <div>
                          <p className="font-bold text-sm text-slate-800">{t.managedBy}</p>
                          <p className="text-xs text-slate-500">{t.subCategory} on {t.date}</p>
                        </div>
                        <p className="text-red-600 font-bold">Rs. {(parseFloat(t.amount) - parseFloat(t.paidAmount || 0)).toLocaleString()}</p>
                      </div>
                    ))}
                    {transactions.filter(t => t.type === 'Expense' && (parseFloat(t.amount) - parseFloat(t.paidAmount || 0)) > 0).length === 0 && (
                      <p className="text-slate-400 text-center py-4">No outstanding payables.</p>
                    )}
                </div>
              </Card>

              <Card>
                <h2 className="text-xl font-bold mb-6 flex items-center gap-2">
                  <Wallet className="text-blue-500" />
                  Account Receivables (From Farmers)
                </h2>
                <div className="space-y-4">
                  {transactions
                    .filter(t => t.type === 'Income' && (parseFloat(t.amount) - parseFloat(t.paidAmount || 0)) > 0)
                    .map(t => (
                      <div key={t.id} className="flex justify-between items-center p-3 border-b border-slate-100">
                        <div>
                          <p className="font-bold text-sm text-slate-800">{t.farmerName}</p>
                          <p className="text-xs text-slate-500">Water Bill - {t.date}</p>
                        </div>
                        <p className="text-blue-600 font-bold">Rs. {(parseFloat(t.amount) - parseFloat(t.paidAmount || 0)).toLocaleString()}</p>
                      </div>
                    ))}
                    {transactions.filter(t => t.type === 'Income' && (parseFloat(t.amount) - parseFloat(t.paidAmount || 0)) > 0).length === 0 && (
                      <p className="text-slate-400 text-center py-4">No outstanding receivables.</p>
                    )}
                </div>
              </Card>
            </div>

            <Card className="overflow-hidden p-0">
               <div className="p-6 bg-slate-900 text-white flex justify-between items-center">
                  <h2 className="text-xl font-bold">Full Transaction Ledger</h2>
                  <button onClick={() => window.print()} className="bg-slate-700 hover:bg-slate-600 px-4 py-2 rounded-lg text-xs font-bold transition-all">Download PDF</button>
               </div>
               <div className="overflow-x-auto">
                 <table className="w-full text-left">
                    <thead>
                      <tr className="bg-slate-100 border-b text-slate-500 text-[10px] font-bold uppercase">
                        <th className="px-6 py-4">ID</th>
                        <th className="px-6 py-4">Date</th>
                        <th className="px-6 py-4">Category</th>
                        <th className="px-6 py-4">Description</th>
                        <th className="px-6 py-4">Debit (Exp)</th>
                        <th className="px-6 py-4">Credit (Inc)</th>
                        <th className="px-6 py-4">Balance Due</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-slate-100">
                      {transactions.map((t, idx) => {
                         const balance = (parseFloat(t.amount) - parseFloat(t.paidAmount || 0));
                         return (
                          <tr key={t.id} className="text-sm">
                            <td className="px-6 py-4 text-slate-400 text-[10px]">{t.id}</td>
                            <td className="px-6 py-4 font-medium">{t.date}</td>
                            <td className="px-6 py-4">
                              <span className="capitalize bg-slate-100 px-2 py-1 rounded text-[10px]">{t.category}</span>
                            </td>
                            <td className="px-6 py-4">
                              {t.category === 'water' ? `Tubewell usage: ${t.farmerName}` : `${t.subCategory} for ${t.animalType || t.cropName}`}
                            </td>
                            <td className="px-6 py-4 font-bold text-red-500">{t.type === 'Expense' ? `Rs. ${Number(t.amount).toLocaleString()}` : '-'}</td>
                            <td className="px-6 py-4 font-bold text-emerald-600">{t.type === 'Income' ? `Rs. ${Number(t.amount).toLocaleString()}` : '-'}</td>
                            <td className="px-6 py-4 font-bold text-slate-700">{balance > 0 ? `Rs. ${balance.toLocaleString()}` : '-'}</td>
                          </tr>
                         )
                      })}
                    </tbody>
                 </table>
               </div>
            </Card>
          </div>
        )}
      </main>

      {/* Mobile-only spacing */}
      <div className="h-20 md:hidden"></div>
    </div>
  );
};

export default App;
