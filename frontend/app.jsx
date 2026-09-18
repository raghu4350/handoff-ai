const { useState, useEffect } = React;

const App = () => {
  const [deals, setDeals] = useState([]);
  const [records, setRecords] = useState({ handoffs: [], escalations: [] });
  const [selectedDeal, setSelectedDeal] = useState(null);
  
  const [isEvaluating, setIsEvaluating] = useState(false);
  const [evaluationResult, setEvaluationResult] = useState(null);

  const [showOverview, setShowOverview] = useState(true);
  const [isCreatingDeal, setIsCreatingDeal] = useState(false);
  const [isAdHocQuery, setIsAdHocQuery] = useState(false);

  useEffect(() => {
    fetchDeals();
    fetchRecords();
  }, []);

  const fetchDeals = async () => {
    try {
      const res = await fetch("/api/deals");
      const data = await res.json();
      setDeals(data);
    } catch (err) {
      console.error("Failed to fetch deals", err);
    }
  };

  const fetchRecords = async () => {
    try {
      const res = await fetch("/api/records");
      const data = await res.json();
      setRecords(data);
    } catch (err) {
      console.error("Failed to fetch records", err);
    }
  };

  const deleteDeal = async (id) => {
    if (!confirm("Are you sure you want to delete this deal?")) return;
    try {
      await fetch(`/api/deals/${id}`, { method: "DELETE" });
      if (selectedDeal && selectedDeal.id === id) {
        setSelectedDeal(null);
        setShowOverview(true);
      }
      fetchDeals();
    } catch (err) {
      console.error("Failed to delete deal", err);
    }
  };

  const clearRecords = async () => {
    if (!confirm("Are you sure you want to completely wipe the SQLite records history?")) return;
    try {
      await fetch("/api/records", { method: "DELETE" });
      fetchRecords();
    } catch (err) {
      console.error("Failed to clear records", err);
    }
  };

  const runHandoff = async () => {
    if (!selectedDeal) return;
    setIsEvaluating(true);
    setEvaluationResult(null);
    try {
      const res = await fetch("/api/handoff/evaluate", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ deal_id: selectedDeal.id })
      });
      const data = await res.json();
      setEvaluationResult(data);
      fetchRecords(); // Refresh DB tables
    } catch (err) {
      console.error("Handoff failed", err);
      alert("Handoff Evaluation Failed: " + err.message);
    } finally {
      setIsEvaluating(false);
    }
  };

  const runAdHocHandoff = async (prompt) => {
    if (!prompt.trim()) return;
    setIsEvaluating(true);
    setEvaluationResult(null);
    try {
      const res = await fetch("/api/handoff/evaluate_raw", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ prompt })
      });
      const data = await res.json();
      setEvaluationResult(data);
      fetchRecords(); // Refresh DB tables
    } catch (err) {
      console.error("Handoff failed", err);
      alert("Handoff Evaluation Failed: " + err.message);
    } finally {
      setIsEvaluating(false);
    }
  };

  return (
    <div className="flex bg-[#f8fafc]">
      <Sidebar 
        deals={deals} 
        selectedDeal={selectedDeal} 
        isAdHocQuery={isAdHocQuery}
        showOverview={showOverview}
        onSelectOverview={() => {
          setShowOverview(true);
          setSelectedDeal(null);
          setIsCreatingDeal(false);
          setIsAdHocQuery(false);
          setEvaluationResult(null);
        }}
        onSelectDeal={(d) => { 
          setSelectedDeal(d); 
          setShowOverview(false);
          setIsCreatingDeal(false); 
          setIsAdHocQuery(false);
          setEvaluationResult(null);
        }} 
        onCreateNew={() => {
          setIsCreatingDeal(true);
          setShowOverview(false);
          setIsAdHocQuery(false);
          setSelectedDeal(null);
        }}
        onAdHocQuery={() => {
          setIsAdHocQuery(true);
          setShowOverview(false);
          setIsCreatingDeal(false);
          setSelectedDeal(null);
          setEvaluationResult(null);
        }}
        onDeleteDeal={deleteDeal}
      />
      
      <div className="pl-72 min-h-screen flex flex-col w-full">
        <Header />
        
        <main className="w-full pt-16 px-8 flex-1">
          <div className="flex flex-col w-full gap-6 py-6 pb-16">
            
            {showOverview ? (
              <ProjectOverview />
            ) : isCreatingDeal ? (
              <>
                <ExecutiveHero />
                <NewDealForm 
                  onSuccess={() => {
                    fetchDeals(); // Refresh sidebar deals
                    setIsCreatingDeal(false);
                    setShowOverview(true);
                  }} 
                  onCancel={() => {
                    setIsCreatingDeal(false);
                    setShowOverview(true);
                  }}
                />
              </>
            ) : (
              <>
                <ExecutiveHero />
                
                {isAdHocQuery ? (
                  <AdHocQueryForm onRun={runAdHocHandoff} isEvaluating={isEvaluating} />
                ) : (
                  <DealActionBanner deal={selectedDeal} onRun={runHandoff} isEvaluating={isEvaluating} />
                )}
                
                <PipelineFlowchart isEvaluating={isEvaluating} />
                
                {(isEvaluating || evaluationResult) && (
                  <CustomMessageBanner isEvaluating={isEvaluating} result={evaluationResult} />
                )}
                
                <DatabaseRecords records={records} onClear={clearRecords} />
              </>
            )}

          </div>
        </main>
      </div>
    </div>
  );
};

// --- COMPONENTS --- //

const ProjectOverview = () => {
  const [showArchitecture, setShowArchitecture] = useState(false);

  const copyToClipboard = (text) => {
    navigator.clipboard.writeText(text);
    alert("Copied to clipboard! Head over to the 'Manual AI Search' in the sidebar to test this prompt.");
  };

  return (
    <>
      <div className="flex flex-col gap-8 animate-in fade-in duration-500 w-full max-w-6xl mx-auto pb-10">
        
        {/* 1. HERO SECTION (Interactive & Modern) */}
        <section className="relative rounded-[2rem] p-10 lg:p-16 bg-slate-950 text-white overflow-hidden shadow-2xl border border-slate-800">
          {/* Animated Background Orbs */}
          <div className="absolute top-0 right-0 w-96 h-96 bg-cyan-500 rounded-full blur-[120px] opacity-20 animate-pulse -mr-20 -mt-20"></div>
          <div className="absolute bottom-0 left-10 w-80 h-80 bg-indigo-600 rounded-full blur-[120px] opacity-30 animate-pulse" style={{ animationDelay: '1s' }}></div>
          <div className="absolute top-1/2 left-1/2 w-[500px] h-[500px] bg-blue-500 rounded-full blur-[150px] opacity-10 transform -translate-x-1/2 -translate-y-1/2 pointer-events-none"></div>

          <div className="relative z-10 grid grid-cols-1 lg:grid-cols-12 gap-12 items-center">
            
            {/* Left Content */}
            <div className="lg:col-span-7 flex flex-col gap-6 items-start text-left">
              <div className="inline-flex items-center gap-2 px-3 py-1.5 bg-slate-900/80 border border-slate-700 backdrop-blur-md rounded-full shadow-lg group hover:border-cyan-500/50 transition-all cursor-pointer">
                <span className="relative flex h-2 w-2">
                  <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-cyan-400 opacity-75"></span>
                  <span className="relative inline-flex rounded-full h-2 w-2 bg-cyan-500"></span>
                </span>
                <span className="text-cyan-300 text-[11px] font-bold uppercase tracking-wider group-hover:text-cyan-200 transition-colors">Handoff AI • Enterprise Edition</span>
              </div>
              
              <h1 className="font-display-lg text-5xl lg:text-[4.2rem] font-extrabold tracking-tight leading-[1.05]">
                Autonomous <br/>
                <span className="text-transparent bg-clip-text bg-gradient-to-r from-cyan-400 via-blue-400 to-indigo-400">AI Gateway</span>
              </h1>
              
              <p className="text-lg lg:text-xl text-slate-400 leading-relaxed font-light mt-2 max-w-2xl">
                Eliminate contract slippage instantly. A dual-LLM autonomous pipeline that intercepts sales contracts, analyzes live engineering capacity, and guarantees delivery—<strong>before the deal is signed.</strong>
              </p>

              <div className="flex flex-wrap items-center gap-4 mt-4">
                <button onClick={() => window.scrollTo({ top: document.body.scrollHeight, behavior: 'smooth' })} className="flex items-center gap-2 px-6 py-3.5 bg-cyan-500 hover:bg-cyan-400 text-slate-950 font-bold rounded-xl shadow-[0_0_20px_rgba(6,182,212,0.4)] hover:shadow-[0_0_30px_rgba(6,182,212,0.6)] transition-all hover:-translate-y-1">
                  <span className="material-symbols-outlined text-[20px]">science</span>
                  Test The Engine
                </button>
                <button onClick={() => setShowArchitecture(true)} className="flex items-center gap-3 px-6 py-3.5 bg-slate-800/50 hover:bg-slate-800 border border-slate-700 hover:border-slate-600 backdrop-blur-sm text-white font-semibold rounded-xl transition-all cursor-pointer group hover:-translate-y-1">
                  <span className="material-symbols-outlined text-slate-400 group-hover:text-white transition-colors">play_circle</span>
                  View Architecture
                </button>
              </div>
            </div>

            {/* Right Visual (Interactive Glass Terminal) */}
            <div className="lg:col-span-5 relative group w-full mt-8 lg:mt-0">
              <div className="absolute inset-0 bg-gradient-to-tr from-cyan-500 to-indigo-500 rounded-2xl transform rotate-3 scale-[1.02] opacity-40 group-hover:rotate-6 group-hover:opacity-70 transition-all duration-700 blur-sm"></div>
              
              <div className="relative bg-[#0f172a]/90 backdrop-blur-xl border border-slate-700/50 p-6 rounded-2xl shadow-2xl transform transition-transform duration-700 group-hover:-translate-y-2">
                <div className="flex items-center justify-between border-b border-slate-800 pb-4 mb-4">
                  <div className="flex gap-2">
                    <div className="w-3 h-3 rounded-full bg-rose-500/80"></div>
                    <div className="w-3 h-3 rounded-full bg-amber-500/80"></div>
                    <div className="w-3 h-3 rounded-full bg-emerald-500/80"></div>
                  </div>
                  <span className="text-[10px] font-code-stream text-slate-500 uppercase tracking-widest flex items-center gap-1">
                    <span className="w-1.5 h-1.5 rounded-full bg-rose-500 animate-pulse"></span>
                    Live Agent Processing
                  </span>
                </div>
                
                <div className="flex flex-col gap-3 font-code-stream text-[13px]">
                  <div className="flex items-center gap-2 text-slate-400">
                    <span className="text-cyan-400">➜</span>
                    <span>Intercepting new deal: <span className="text-white font-semibold">Project Titan</span></span>
                  </div>
                  <div className="flex items-center gap-2 text-slate-400 mt-1">
                    <span className="text-amber-400 animate-spin">⟳</span>
                    <span>Agent 1: Extracting tech stack requirements...</span>
                  </div>
                  <div className="pl-6 text-indigo-300">Found: [React, Node.js, PostgreSQL]</div>
                  <div className="flex items-center gap-2 text-slate-400 mt-3">
                    <span className="text-cyan-400 animate-pulse">●</span>
                    <span>Agent 2: Querying live DB for engineers...</span>
                  </div>
                  <div className="pl-6 flex items-center gap-2">
                    <span className="w-2 h-2 rounded-full bg-rose-500 shadow-[0_0_8px_rgba(244,63,94,0.6)]"></span>
                    <span className="text-rose-300 line-through">Sarah (Booked)</span>
                  </div>
                  <div className="pl-6 flex items-center gap-2">
                    <span className="w-2 h-2 rounded-full bg-emerald-500 shadow-[0_0_8px_rgba(16,185,129,0.6)]"></span>
                    <span className="text-emerald-300 font-bold">David (Available)</span>
                  </div>
                  <div className="mt-5 p-3 bg-emerald-500/10 border border-emerald-500/30 rounded-lg text-emerald-400 font-bold flex items-center gap-2 shadow-[0_0_15px_rgba(16,185,129,0.15)]">
                    <span className="material-symbols-outlined text-[18px]">verified</span>
                    VERDICT: LOW RISK - APPROVED
                  </div>
                </div>
              </div>
            </div>
            
          </div>
        </section>

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
          {/* 2. THE PROBLEM */}
          <section className="rounded-2xl bg-white border border-rose-100 shadow-sm p-8 flex flex-col relative overflow-hidden">
            <div className="absolute top-0 right-0 w-32 h-32 bg-rose-50 rounded-full blur-[50px] -mr-10 -mt-10"></div>
            <div className="flex items-center gap-3 mb-5">
              <div className="w-10 h-10 rounded-full bg-rose-100 flex items-center justify-center text-rose-600">
                <span className="material-symbols-outlined text-[20px]">warning</span>
              </div>
              <h2 className="font-headline-md text-2xl font-bold text-slate-900">The Core Problem</h2>
            </div>
            <p className="text-slate-600 leading-relaxed mb-6">
              In modern IT agencies, there is a massive disconnect between Sales (who want to close deals fast) and Delivery (who actually build the product). This gap causes critical business failures:
            </p>
            <ul className="flex flex-col gap-4 text-slate-700">
              <li className="flex items-start gap-3">
                <span className="material-symbols-outlined text-rose-500 mt-0.5 text-[20px]">cancel</span>
                <span><strong>Unrealistic Scopes:</strong> Sales commits to massive features within impossible 2-week timelines to win the contract.</span>
              </li>
              <li className="flex items-start gap-3">
                <span className="material-symbols-outlined text-rose-500 mt-0.5 text-[20px]">cancel</span>
                <span><strong>Missing Requirements:</strong> Deals are thrown "over the wall" without critical technical constraints or budgets defined.</span>
              </li>
              <li className="flex items-start gap-3">
                <span className="material-symbols-outlined text-rose-500 mt-0.5 text-[20px]">cancel</span>
                <span><strong>Resource Blindness:</strong> Selling an iOS App project when all iOS developers are already booked for the next 6 months.</span>
              </li>
              <li className="flex items-start gap-3">
                <span className="material-symbols-outlined text-rose-500 mt-0.5 text-[20px]">cancel</span>
                <span><strong>Ruined Reputation:</strong> Having to cancel a deal or delay a project immediately after signing it makes the company look unprofessional to the client.</span>
              </li>
              <li className="flex items-start gap-3">
                <span className="material-symbols-outlined text-rose-500 mt-0.5 text-[20px]">cancel</span>
                <span><strong>Wasted Tech Time:</strong> Senior engineers waste hours every week trying to decipher messy, unstructured sales notes instead of actually building software.</span>
              </li>
            </ul>
          </section>

          {/* 3. THE SOLUTION */}
          <section className="rounded-2xl bg-white border border-emerald-100 shadow-sm p-8 flex flex-col relative overflow-hidden">
            <div className="absolute top-0 right-0 w-32 h-32 bg-emerald-50 rounded-full blur-[50px] -mr-10 -mt-10"></div>
            <div className="flex items-center gap-3 mb-5">
              <div className="w-10 h-10 rounded-full bg-emerald-100 flex items-center justify-center text-emerald-600">
                <span className="material-symbols-outlined text-[20px]">psychology</span>
              </div>
              <h2 className="font-headline-md text-2xl font-bold text-slate-900">The Handoff AI Solution</h2>
            </div>
            <p className="text-slate-600 leading-relaxed mb-6">
              We intercept the handoff process using a <strong>Multi-Agent LLM Pipeline</strong> connected to a real-time SQLite database, evaluating deals deterministically before they reach human managers.
            </p>
            <ul className="flex flex-col gap-4 text-slate-700">
              <li className="flex items-start gap-3">
                <span className="material-symbols-outlined text-emerald-500 mt-0.5 text-[20px]">check_circle</span>
                <span><strong>Agent 1 (Intake Check):</strong> Analyzes the raw, messy contract notes from the salesperson to ensure no mandatory fields (budget, users, timeline) are missing.</span>
              </li>
              <li className="flex items-start gap-3">
                <span className="material-symbols-outlined text-emerald-500 mt-0.5 text-[20px]">check_circle</span>
                <span><strong>Agent 2 (Capacity Match):</strong> Dynamically searches the SQLite database to check if the specific engineers required for the tech stack are actually available.</span>
              </li>
              <li className="flex items-start gap-3">
                <span className="material-symbols-outlined text-emerald-500 mt-0.5 text-[20px]">check_circle</span>
                <span><strong>Autonomous Escalation:</strong> Automatically flags high-risk deals and blocks the handoff, saving the company from a disastrous contract.</span>
              </li>
            </ul>
          </section>
        </div>

        {/* 4. COMPANY BENEFITS (ROI) */}
        <section className="rounded-2xl bg-gradient-to-br from-indigo-50 to-white border border-indigo-100 shadow-sm p-8 lg:p-10">
          <div className="text-center mb-10">
            <h2 className="font-headline-md text-3xl font-extrabold text-slate-900">Business Value & ROI</h2>
            <p className="text-slate-600 mt-2 text-lg">Why adopting this architecture provides a massive competitive advantage.</p>
          </div>
          
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            <div className="bg-white p-6 rounded-xl border border-slate-200 shadow-sm flex flex-col items-center text-center">
              <div className="w-14 h-14 rounded-full bg-blue-50 text-blue-600 flex items-center justify-center mb-4">
                <span className="material-symbols-outlined text-[28px]">trending_up</span>
              </div>
              <h3 className="font-bold text-lg text-slate-900 mb-2">Zero Contract Slippage</h3>
              <p className="text-slate-600 text-sm">By preventing impossible scopes from being signed, the company eliminates client churn, refunds, and reputational damage.</p>
            </div>
            
            <div className="bg-white p-6 rounded-xl border border-slate-200 shadow-sm flex flex-col items-center text-center">
              <div className="w-14 h-14 rounded-full bg-purple-50 text-purple-600 flex items-center justify-center mb-4">
                <span className="material-symbols-outlined text-[28px]">groups</span>
              </div>
              <h3 className="font-bold text-lg text-slate-900 mb-2">100% Resource Optimization</h3>
              <p className="text-slate-600 text-sm">Real-time database integration ensures that Sales only sells what the Delivery team actually has the manpower to build.</p>
            </div>

            <div className="bg-white p-6 rounded-xl border border-slate-200 shadow-sm flex flex-col items-center text-center">
              <div className="w-14 h-14 rounded-full bg-cyan-50 text-cyan-600 flex items-center justify-center mb-4">
                <span className="material-symbols-outlined text-[28px]">timer</span>
              </div>
              <h3 className="font-bold text-lg text-slate-900 mb-2">Automated Management</h3>
              <p className="text-slate-600 text-sm">Tech Leads no longer waste hours reviewing messy contracts. The AI instantly parses the text and delivers a clean Risk Assessment.</p>
            </div>
          </div>
        </section>

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
          {/* 5. LIVE DATABASE STATE */}
          <section className="rounded-2xl bg-white border border-slate-200 shadow-sm p-8">
            <div className="flex items-center gap-3 mb-6">
              <span className="material-symbols-outlined text-[24px] text-slate-700">database</span>
              <h2 className="font-headline-md text-xl font-bold text-slate-900">Current Database State</h2>
            </div>
            <p className="text-sm text-slate-500 mb-6">The AI queries this exact list to determine if an engineer is available for a requested project integration.</p>
            
            <div className="flex flex-col gap-3">
              <div className="flex items-center justify-between p-3.5 rounded-lg bg-emerald-50 border border-emerald-100">
                <div className="flex items-center gap-3"><span className="w-2.5 h-2.5 rounded-full bg-emerald-500"></span><span className="font-bold text-slate-800">Amit Kumar</span></div>
                <span className="text-xs font-semibold text-emerald-700 bg-emerald-100 px-2 py-1 rounded">AI Engineer</span>
              </div>
              <div className="flex items-center justify-between p-3.5 rounded-lg bg-emerald-50 border border-emerald-100">
                <div className="flex items-center gap-3"><span className="w-2.5 h-2.5 rounded-full bg-emerald-500"></span><span className="font-bold text-slate-800">Neha Singh</span></div>
                <span className="text-xs font-semibold text-emerald-700 bg-emerald-100 px-2 py-1 rounded">Backend Engineer</span>
              </div>
              <div className="flex items-center justify-between p-3.5 rounded-lg bg-amber-50 border border-amber-100">
                <div className="flex items-center gap-3"><span className="w-2.5 h-2.5 rounded-full bg-amber-500"></span><span className="font-bold text-slate-800">Raj Patel</span></div>
                <span className="text-xs font-semibold text-amber-700 bg-amber-100 px-2 py-1 rounded">Frontend (Limited)</span>
              </div>
              <div className="flex items-center justify-between p-3.5 rounded-lg bg-rose-50 border border-rose-100">
                <div className="flex items-center gap-3"><span className="w-2.5 h-2.5 rounded-full bg-rose-500"></span><span className="font-bold text-slate-800">Priya Nair</span></div>
                <span className="text-xs font-semibold text-rose-700 bg-rose-100 px-2 py-1 rounded">Salesforce (Unavailable)</span>
              </div>
              <div className="flex items-center justify-between p-3.5 rounded-lg bg-rose-50 border border-rose-100">
                <div className="flex items-center gap-3"><span className="w-2.5 h-2.5 rounded-full bg-rose-500"></span><span className="font-bold text-slate-800">Anjali Desai</span></div>
                <span className="text-xs font-semibold text-rose-700 bg-rose-100 px-2 py-1 rounded">iOS Developer (Unavailable)</span>
              </div>
            </div>
          </section>

          {/* 6. INTERACTIVE TESTING PROMPTS */}
          <section className="rounded-2xl bg-slate-900 border border-slate-800 shadow-sm p-8 text-white relative overflow-hidden">
            <div className="absolute top-0 right-0 w-32 h-32 bg-indigo-500 rounded-full blur-[70px] opacity-20 -mr-10 -mt-10"></div>
            <div className="flex items-center gap-3 mb-6 relative z-10">
              <span className="material-symbols-outlined text-[24px] text-cyan-400">science</span>
              <h2 className="font-headline-md text-xl font-bold text-white">Interactive Test Prompts</h2>
            </div>
            <p className="text-sm text-slate-400 mb-6 relative z-10">Click any prompt below to copy it. Then, paste it into the <strong>Manual AI Search</strong> in the sidebar to watch the AI evaluate the text against the database.</p>
            
            <div className="flex flex-col gap-4 relative z-10">
              
              <div className="border border-emerald-500/30 bg-emerald-950/30 rounded-xl p-4 hover:bg-emerald-900/40 transition-colors cursor-pointer group" onClick={() => copyToClipboard("TechCorp signed a 12-week contract for a Backend Data Processing API using Python. Budget is 15 Lakhs. Expected users: 1000. Technical contact: Priya Sharma.")}>
                <div className="flex justify-between items-start mb-1.5">
                  <span className="font-bold text-emerald-400 text-sm">1. The "Perfect" Deal 🟢</span>
                  <span className="material-symbols-outlined text-emerald-400 text-[16px] opacity-0 group-hover:opacity-100 transition-opacity">content_copy</span>
                </div>
                <p className="text-xs text-slate-300 italic">"TechCorp signed a 12-week contract for a Backend Data Processing API... Technical contact: Priya Sharma."</p>
              </div>

              <div className="border border-rose-500/30 bg-rose-950/30 rounded-xl p-4 hover:bg-rose-900/40 transition-colors cursor-pointer group" onClick={() => copyToClipboard("RetailCo India wants an E-commerce Recommendation Engine. The timeline is 8 weeks. No technical contact provided.")}>
                <div className="flex justify-between items-start mb-1.5">
                  <span className="font-bold text-rose-400 text-sm">2. Missing Info / Incomplete 🔴</span>
                  <span className="material-symbols-outlined text-rose-400 text-[16px] opacity-0 group-hover:opacity-100 transition-opacity">content_copy</span>
                </div>
                <p className="text-xs text-slate-300 italic">"RetailCo India wants an E-commerce Recommendation Engine... No technical contact provided."</p>
              </div>

              <div className="border border-rose-500/30 bg-rose-950/30 rounded-xl p-4 hover:bg-rose-900/40 transition-colors cursor-pointer group" onClick={() => copyToClipboard("ABC Manufacturing needs an AI Customer Support Automation system for 12 Lakhs. Timeline is 6 weeks. It absolutely must integrate with Salesforce.")}>
                <div className="flex justify-between items-start mb-1.5">
                  <span className="font-bold text-rose-400 text-sm">3. Unavailable Engineer (High Risk) 🔴</span>
                  <span className="material-symbols-outlined text-rose-400 text-[16px] opacity-0 group-hover:opacity-100 transition-opacity">content_copy</span>
                </div>
                <p className="text-xs text-slate-300 italic">"ABC Manufacturing needs... an Automation system... It absolutely must integrate with Salesforce." (Our Salesforce engineer is unavailable).</p>
              </div>

              <div className="border border-amber-500/30 bg-amber-950/30 rounded-xl p-4 hover:bg-amber-900/40 transition-colors cursor-pointer group" onClick={() => copyToClipboard("SpaceX just signed a 2-week contract for an iOS app. Do we have developers?")}>
                <div className="flex justify-between items-start mb-1.5">
                  <span className="font-bold text-amber-400 text-sm">4. Fake Client (Not in CRM) 🟡</span>
                  <span className="material-symbols-outlined text-amber-400 text-[16px] opacity-0 group-hover:opacity-100 transition-opacity">content_copy</span>
                </div>
                <p className="text-xs text-slate-300 italic">"SpaceX just signed a 2-week contract for an iOS app. Do we have developers?"</p>
              </div>

            </div>
          </section>
        </div>

      </div>

      {showArchitecture && (
        <div className="fixed inset-0 z-[100] flex items-center justify-center p-4 sm:p-6 animate-in fade-in duration-300">
          <div className="absolute inset-0 bg-slate-900/80 backdrop-blur-md" onClick={() => setShowArchitecture(false)}></div>
          
          <div className="relative w-full max-w-5xl max-h-[90vh] overflow-y-auto bg-slate-950 border border-slate-700 rounded-3xl shadow-2xl p-8 lg:p-12 animate-in zoom-in-95 duration-300">
            <button onClick={() => setShowArchitecture(false)} className="absolute top-6 right-6 text-slate-400 hover:text-white bg-slate-800 hover:bg-slate-700 rounded-full p-2 transition-all">
              <span className="material-symbols-outlined text-[24px]">close</span>
            </button>
            
            <div className="flex flex-col gap-8">
              <div className="text-center max-w-2xl mx-auto">
                <span className="px-3 py-1 bg-indigo-500/10 border border-indigo-400/30 rounded-full text-indigo-300 text-xs font-bold uppercase tracking-wider">System Architecture</span>
                <h2 className="font-display-lg text-3xl lg:text-4xl font-extrabold text-white mt-4 tracking-tight">How Handoff AI Works Under The Hood</h2>
                <p className="text-slate-400 mt-4 leading-relaxed">A modern, fully decoupled architecture leveraging Python's AI ecosystem on the backend and React's reactive UI on the frontend.</p>
              </div>

              {/* Visual Flow Diagram */}
              <div className="grid grid-cols-1 md:grid-cols-4 gap-4 items-center relative mt-4">
                {/* Connecting Lines for Desktop */}
                <div className="hidden md:block absolute top-1/2 left-[10%] right-[10%] h-0.5 bg-gradient-to-r from-cyan-500/20 via-indigo-500/50 to-blue-500/20 -translate-y-1/2 z-0"></div>

                {/* Node 1: Frontend */}
                <div className="relative z-10 bg-slate-900 border border-cyan-500/30 rounded-2xl p-6 flex flex-col items-center text-center shadow-[0_0_30px_rgba(6,182,212,0.1)]">
                  <div className="w-16 h-16 rounded-2xl bg-cyan-500/20 text-cyan-400 flex items-center justify-center mb-4 border border-cyan-500/50">
                    <span className="material-symbols-outlined text-[32px]">desktop_windows</span>
                  </div>
                  <h3 className="text-white font-bold text-lg">React Frontend</h3>
                  <p className="text-slate-400 text-xs mt-2">Vite + Tailwind CSS. Completely decoupled client interface providing instant state updates.</p>
                </div>

                {/* Node 2: Backend */}
                <div className="relative z-10 bg-slate-900 border border-indigo-500/30 rounded-2xl p-6 flex flex-col items-center text-center shadow-[0_0_30px_rgba(99,102,241,0.1)]">
                  <div className="w-16 h-16 rounded-2xl bg-indigo-500/20 text-indigo-400 flex items-center justify-center mb-4 border border-indigo-500/50">
                    <span className="material-symbols-outlined text-[32px]">api</span>
                  </div>
                  <h3 className="text-white font-bold text-lg">FastAPI Backend</h3>
                  <p className="text-slate-400 text-xs mt-2">High-performance Python API server routing requests, parsing AI output, and managing DB connections.</p>
                </div>

                {/* Node 3: AI Engine */}
                <div className="relative z-10 bg-slate-900 border border-purple-500/30 rounded-2xl p-6 flex flex-col items-center text-center shadow-[0_0_30px_rgba(168,85,247,0.1)]">
                  <div className="w-16 h-16 rounded-2xl bg-purple-500/20 text-purple-400 flex items-center justify-center mb-4 border border-purple-500/50">
                    <span className="material-symbols-outlined text-[32px]">smart_toy</span>
                  </div>
                  <h3 className="text-white font-bold text-lg">CrewAI Engine</h3>
                  <p className="text-slate-400 text-xs mt-2">Dual-LLM (Intake & Delivery agents) pipeline executing deterministic tool calls to evaluate risk.</p>
                </div>

                {/* Node 4: Database */}
                <div className="relative z-10 bg-slate-900 border border-emerald-500/30 rounded-2xl p-6 flex flex-col items-center text-center shadow-[0_0_30px_rgba(16,185,129,0.1)]">
                  <div className="w-16 h-16 rounded-2xl bg-emerald-500/20 text-emerald-400 flex items-center justify-center mb-4 border border-emerald-500/50">
                    <span className="material-symbols-outlined text-[32px]">database</span>
                  </div>
                  <h3 className="text-white font-bold text-lg">SQLite DB</h3>
                  <p className="text-slate-400 text-xs mt-2">Live persistent storage holding the dynamic engineer availability status and deal history.</p>
                </div>
              </div>

              {/* Full Pipeline Flowchart */}
              <div className="mt-8 pt-8 border-t border-slate-800">
                <h3 className="text-white font-bold mb-6 text-center text-xl">Autonomous Pipeline Execution Flow</h3>
                <div className="flex flex-col items-center w-full max-w-3xl mx-auto space-y-2">
                  
                  {/* Step 1 */}
                  <div className="w-full bg-slate-900 border border-slate-700 rounded-xl p-4 flex items-center gap-4 relative z-10 shadow-lg">
                    <div className="w-12 h-12 rounded-full bg-cyan-500/20 text-cyan-400 flex items-center justify-center shrink-0 border border-cyan-500/30">
                      <span className="material-symbols-outlined">login</span>
                    </div>
                    <div>
                      <h4 className="text-white font-bold">1. Deal Intercept (Sales Input)</h4>
                      <p className="text-slate-400 text-sm">New contract details are submitted via the React UI and routed to the FastAPI backend.</p>
                    </div>
                  </div>

                  {/* Arrow Down */}
                  <div className="w-0.5 h-6 bg-gradient-to-b from-cyan-500/50 to-purple-500/50"></div>

                  {/* Step 2 */}
                  <div className="w-full bg-slate-900 border border-purple-500/30 rounded-xl p-4 flex items-center gap-4 relative z-10 shadow-[0_0_20px_rgba(168,85,247,0.1)]">
                    <div className="w-12 h-12 rounded-full bg-purple-500/20 text-purple-400 flex items-center justify-center shrink-0 border border-purple-500/30">
                      <span className="material-symbols-outlined">rule</span>
                    </div>
                    <div className="flex-1">
                      <h4 className="text-white font-bold">2. Intake Agent Validation</h4>
                      <p className="text-slate-400 text-sm">Agent scans the SQLite database for missing info (budget, timeline, tech stack).</p>
                    </div>
                    <div className="text-right pl-4 border-l border-slate-700 flex flex-col justify-center bg-rose-500/10 p-2 rounded-lg border border-rose-500/20">
                      <span className="text-[10px] text-rose-400 font-bold uppercase tracking-wide">If Missing Info:</span>
                      <span className="text-xs text-rose-300 font-semibold">Deal Cancelled</span>
                    </div>
                  </div>

                  {/* Arrow Down */}
                  <div className="w-0.5 h-6 bg-gradient-to-b from-purple-500/50 to-indigo-500/50"></div>

                  {/* Step 3 */}
                  <div className="w-full bg-slate-900 border border-indigo-500/30 rounded-xl p-4 flex items-center gap-4 relative z-10 shadow-[0_0_20px_rgba(99,102,241,0.1)]">
                    <div className="w-12 h-12 rounded-full bg-indigo-500/20 text-indigo-400 flex items-center justify-center shrink-0 border border-indigo-500/30">
                      <span className="material-symbols-outlined">group</span>
                    </div>
                    <div className="flex-1">
                      <h4 className="text-white font-bold">3. Delivery Agent Capacity Check</h4>
                      <p className="text-slate-400 text-sm">Agent cross-references the required skills against live engineering capacity in SQLite.</p>
                    </div>
                    <div className="text-right pl-4 border-l border-slate-700 flex flex-col justify-center bg-rose-500/10 p-2 rounded-lg border border-rose-500/20">
                      <span className="text-[10px] text-rose-400 font-bold uppercase tracking-wide">If Unavailable:</span>
                      <span className="text-xs text-rose-300 font-semibold">Expert Not Available</span>
                    </div>
                  </div>

                  {/* Arrow Down */}
                  <div className="w-0.5 h-6 bg-gradient-to-b from-indigo-500/50 to-emerald-500/50"></div>

                  {/* Step 4 */}
                  <div className="w-full bg-emerald-950/30 border border-emerald-500/30 rounded-xl p-4 flex items-center gap-4 relative z-10 shadow-[0_0_20px_rgba(16,185,129,0.1)]">
                    <div className="w-12 h-12 rounded-full bg-emerald-500/20 text-emerald-400 flex items-center justify-center shrink-0 border border-emerald-500/30">
                      <span className="material-symbols-outlined">verified</span>
                    </div>
                    <div>
                      <h4 className="text-emerald-400 font-bold">4. Final Verdict: Approved</h4>
                      <p className="text-emerald-200/80 text-sm">Deal is safe to sign. Handoff record is generated and UI updates dynamically.</p>
                    </div>
                  </div>

                </div>
              </div>

              {/* Technologies Used Grid */}
              <div className="mt-6 pt-8 border-t border-slate-800">
                <h3 className="text-white font-bold mb-4 text-center text-lg">Core Technology Stack</h3>
                <div className="flex flex-wrap gap-4 justify-center">
                  <span className="px-4 py-2 bg-slate-800 border border-slate-700 rounded-lg text-slate-300 text-sm font-semibold flex items-center gap-2"><span className="w-2.5 h-2.5 rounded-full bg-cyan-400"></span>React (JSX)</span>
                  <span className="px-4 py-2 bg-slate-800 border border-slate-700 rounded-lg text-slate-300 text-sm font-semibold flex items-center gap-2"><span className="w-2.5 h-2.5 rounded-full bg-blue-400"></span>Tailwind CSS</span>
                  <span className="px-4 py-2 bg-slate-800 border border-slate-700 rounded-lg text-slate-300 text-sm font-semibold flex items-center gap-2"><span className="w-2.5 h-2.5 rounded-full bg-indigo-400"></span>FastAPI</span>
                  <span className="px-4 py-2 bg-slate-800 border border-slate-700 rounded-lg text-slate-300 text-sm font-semibold flex items-center gap-2"><span className="w-2.5 h-2.5 rounded-full bg-yellow-400"></span>Python</span>
                  <span className="px-4 py-2 bg-slate-800 border border-slate-700 rounded-lg text-slate-300 text-sm font-semibold flex items-center gap-2"><span className="w-2.5 h-2.5 rounded-full bg-purple-400"></span>CrewAI</span>
                  <span className="px-4 py-2 bg-slate-800 border border-slate-700 rounded-lg text-slate-300 text-sm font-semibold flex items-center gap-2"><span className="w-2.5 h-2.5 rounded-full bg-emerald-400"></span>SQLite</span>
                </div>
              </div>

            </div>
          </div>
        </div>
      )}
    </>
  );
};

const Sidebar = ({ deals, selectedDeal, isAdHocQuery, showOverview, onSelectOverview, onSelectDeal, onCreateNew, onAdHocQuery, onDeleteDeal }) => (
  <aside className="fixed left-0 top-0 h-full w-72 bg-white border-r border-slate-200 z-50 flex flex-col shadow-sm">
    <div className="h-16 px-6 flex items-center justify-between border-b border-slate-100">
      <div className="flex items-center gap-2.5">
        <div className="w-8 h-8 rounded-lg bg-gradient-to-tr from-cyan-600 to-indigo-600 text-white flex items-center justify-center">
          <span className="material-symbols-outlined text-[19px]">hub</span>
        </div>
        <div className="flex flex-col">
          <span className="font-headline-sm text-[16.5px] font-bold text-slate-900 leading-none">
            Handoff<span className="text-cyan-600">AI</span>
          </span>
        </div>
      </div>
      <span className="font-badge-label px-2 py-0.5 rounded-full bg-cyan-50 border border-cyan-200 text-cyan-700 text-[10px] font-bold">REACT</span>
    </div>

    <div className="p-3 border-b border-slate-100">
      <button 
        onClick={onSelectOverview}
        className={`w-full flex items-center gap-2.5 px-4 py-2.5 rounded-lg font-semibold text-sm transition-all ${
          showOverview 
            ? 'bg-slate-900 text-white shadow-md' 
            : 'bg-white text-slate-700 hover:bg-slate-50 border border-slate-200'
        }`}
      >
        <span className="material-symbols-outlined text-[18px]">info</span>
        Pitch Deck / Overview
      </button>
    </div>

    <div className="mt-4 px-5 py-1 flex items-center justify-between">
      <span className="font-badge-label uppercase text-slate-400 text-[11px] font-semibold">Test Scenarios</span>
      <span className="font-label-code text-cyan-700 font-semibold text-[11px] bg-cyan-50 px-2 py-0.5 rounded border border-cyan-200/50">{deals.length} LIVE</span>
    </div>

    <div className="flex flex-col gap-1 px-3 mt-1.5 overflow-y-auto">
      {deals.map(deal => {
        const isSelected = selectedDeal && selectedDeal.id === deal.id;
        return (
          <div 
            key={deal.id}
            className={`flex items-center justify-between px-3 py-2 rounded-lg border transition-all ${
              isSelected 
                ? 'bg-cyan-50 border-cyan-200 shadow-sm' 
                : 'border-transparent text-slate-600 hover:bg-slate-50 hover:border-slate-200'
            }`}
          >
            <div className="flex items-center gap-2.5 cursor-pointer flex-1" onClick={() => onSelectDeal(deal)}>
              <span className={`w-2 h-2 rounded-full ${isSelected ? 'bg-cyan-600 animate-pulse' : 'bg-slate-300'}`}></span>
              <span className={`font-body-sm text-[13px] ${isSelected ? 'font-semibold text-cyan-950' : 'text-slate-700 truncate max-w-[160px]'}`}>
                {deal.client_name}
              </span>
            </div>
            <button 
              onClick={(e) => { e.stopPropagation(); onDeleteDeal(deal.id); }}
              className="text-slate-400 hover:text-rose-500 transition-colors p-1"
              title="Delete Deal"
            >
              <span className="material-symbols-outlined text-[14px]">delete</span>
            </button>
          </div>
        );
      })}
    </div>

    <div className="mt-auto p-4 border-t border-slate-100 flex flex-col gap-2">
      <button 
        onClick={onAdHocQuery}
        className={`w-full flex items-center justify-center gap-2 px-4 py-2 rounded-lg border font-semibold text-sm transition-all ${
          isAdHocQuery 
            ? 'bg-emerald-50 border-emerald-200 text-emerald-700' 
            : 'bg-white border-slate-200 text-slate-700 hover:bg-slate-50'
        }`}
      >
        <span className="material-symbols-outlined text-[18px]">manage_search</span>
        Manual AI Search
      </button>
      <button 
        onClick={onCreateNew}
        className="w-full flex items-center justify-center gap-2 px-4 py-2 rounded-lg bg-indigo-50 border border-indigo-200 text-indigo-700 hover:bg-indigo-100 font-semibold text-sm transition-all"
      >
        <span className="material-symbols-outlined text-[18px]">add_box</span>
        Manual Sales Entry
      </button>
    </div>
  </aside>
);

const Header = () => (
  <header className="fixed top-0 left-72 right-0 h-16 bg-white/95 backdrop-blur-md z-40 border-b border-slate-200 px-8 flex items-center justify-between">
    <div className="flex items-center gap-3">
      <div className="flex items-center gap-2 px-3 py-1.5 rounded-lg bg-emerald-50 border border-emerald-200">
        <span className="relative flex h-2 w-2">
          <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-emerald-400 opacity-75"></span>
          <span className="relative inline-flex rounded-full h-2 w-2 bg-emerald-500"></span>
        </span>
        <span className="font-label-code text-[11px] text-emerald-800 font-bold uppercase tracking-wider">FastAPI + CrewAI Connected</span>
      </div>
    </div>
  </header>
);

const ExecutiveHero = () => (
  <section className="relative rounded-2xl p-6 lg:p-7 bg-gradient-to-r from-slate-900 via-slate-800 to-indigo-950 text-white overflow-hidden shadow-xl">
    <div className="relative z-10 flex flex-col gap-2">
      <h2 className="font-display-lg text-[26px] font-extrabold tracking-tight mt-1">CrewAI Multi-Agent Autonomous Handoff Engine</h2>
      <p className="text-sm text-slate-300 max-w-3xl leading-relaxed">
        Autonomous dual-LLM pipeline that intercepts high-risk deal scopes, performs deterministic skill matching, and prevents costly contract slippage.
      </p>
    </div>
  </section>
);

const AdHocQueryForm = ({ onRun, isEvaluating }) => {
  const [prompt, setPrompt] = useState("");
  return (
    <section className="relative rounded-xl p-6 bg-white border border-slate-200 shadow-sm overflow-hidden">
      <div className="relative z-10 flex flex-col gap-4">
        <div className="flex items-center gap-2">
          <span className="material-symbols-outlined text-[24px] text-emerald-600">manage_search</span>
          <h1 className="font-display-lg text-[24px] text-slate-900 font-bold tracking-tight">Manual AI Search</h1>
        </div>
        <p className="text-sm text-slate-500">
          Paste any raw contract text or ask the AI to check the availability of specific resources directly. (e.g. "SpaceX just signed a 2-week contract for an iOS app. Do we have developers?")
        </p>
        
        <textarea 
          value={prompt} 
          onChange={(e) => setPrompt(e.target.value)}
          rows="4"
          className="w-full border border-slate-300 rounded-lg p-3 text-sm focus:border-emerald-500 focus:ring-1 focus:ring-emerald-500 outline-none transition-all resize-none font-code-stream" 
          placeholder="Paste deal details or type query here..."
        ></textarea>
        
        <button 
          onClick={() => onRun(prompt)}
          disabled={isEvaluating || !prompt.trim()}
          className={`self-start flex items-center justify-center gap-2.5 px-6 py-2.5 rounded-lg text-white font-semibold text-sm shadow-md transition-all ${isEvaluating || !prompt.trim() ? 'bg-slate-400 cursor-not-allowed' : 'bg-gradient-to-r from-emerald-600 to-emerald-500 hover:from-emerald-500 hover:to-emerald-600'}`}
        >
          {isEvaluating ? (
            <span className="material-symbols-outlined text-[18px] animate-spin">sync</span>
          ) : (
            <span className="material-symbols-outlined text-[18px]">psychology</span>
          )}
          <span>{isEvaluating ? 'Running AI Engine...' : 'Run Autonomous Analysis'}</span>
        </button>
      </div>
    </section>
  );
};

const NewDealForm = ({ onSuccess, onCancel }) => {
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [formData, setFormData] = useState({
    client_name: "", project_type: "", timeline: "", budget: "",
    requirements: "", integrations: "None", technical_contact: "", expected_users: 100
  });

  const handleChange = (e) => setFormData({ ...formData, [e.target.name]: e.target.value });

  const handleSubmit = async (e) => {
    e.preventDefault();
    setIsSubmitting(true);
    try {
      const res = await fetch("/api/deals", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ ...formData, expected_users: parseInt(formData.expected_users) || 0 })
      });
      if (res.ok) {
        onSuccess();
      } else {
        const error = await res.json();
        alert("Error saving deal: " + JSON.stringify(error));
      }
    } catch (err) {
      alert("Error: " + err.message);
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <section className="relative rounded-xl p-6 bg-white border border-slate-200 shadow-sm overflow-hidden">
      <div className="flex items-center gap-2 mb-6">
        <span className="material-symbols-outlined text-[24px] text-indigo-600">edit_document</span>
        <h2 className="font-display-lg text-xl text-slate-900 font-bold tracking-tight">Manual Sales Entry</h2>
      </div>
      
      <form onSubmit={handleSubmit} className="flex flex-col gap-4">
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <label className="flex flex-col gap-1">
            <span className="font-label-code text-xs font-semibold text-slate-500 uppercase">Client Name</span>
            <input required name="client_name" onChange={handleChange} className="border border-slate-300 rounded-lg p-2 text-sm focus:border-indigo-500 focus:ring-1 focus:ring-indigo-500 outline-none transition-all" placeholder="e.g. Netflix" />
          </label>
          <label className="flex flex-col gap-1">
            <span className="font-label-code text-xs font-semibold text-slate-500 uppercase">Project Type</span>
            <input required name="project_type" onChange={handleChange} className="border border-slate-300 rounded-lg p-2 text-sm focus:border-indigo-500 focus:ring-1 focus:ring-indigo-500 outline-none transition-all" placeholder="e.g. Video Streaming App" />
          </label>
          <label className="flex flex-col gap-1">
            <span className="font-label-code text-xs font-semibold text-slate-500 uppercase">Budget</span>
            <input required name="budget" onChange={handleChange} className="border border-slate-300 rounded-lg p-2 text-sm focus:border-indigo-500 focus:ring-1 focus:ring-indigo-500 outline-none transition-all" placeholder="e.g. $120,000" />
          </label>
          <label className="flex flex-col gap-1">
            <span className="font-label-code text-xs font-semibold text-slate-500 uppercase">Timeline</span>
            <input required name="timeline" onChange={handleChange} className="border border-slate-300 rounded-lg p-2 text-sm focus:border-indigo-500 focus:ring-1 focus:ring-indigo-500 outline-none transition-all" placeholder="e.g. 6 Months" />
          </label>
        </div>

        <label className="flex flex-col gap-1 mt-2">
          <span className="font-label-code text-xs font-semibold text-slate-500 uppercase">Requirements / Scope (The tricky part)</span>
          <textarea required name="requirements" onChange={handleChange} rows="3" className="border border-slate-300 rounded-lg p-2 text-sm focus:border-indigo-500 focus:ring-1 focus:ring-indigo-500 outline-none transition-all" placeholder="Write the messy notes or exact deliverables here..."></textarea>
        </label>
        
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <label className="flex flex-col gap-1">
            <span className="font-label-code text-xs font-semibold text-slate-500 uppercase">Integrations</span>
            <input name="integrations" value={formData.integrations} onChange={handleChange} className="border border-slate-300 rounded-lg p-2 text-sm focus:border-indigo-500 focus:ring-1 focus:ring-indigo-500 outline-none transition-all" />
          </label>
          <label className="flex flex-col gap-1">
            <span className="font-label-code text-xs font-semibold text-slate-500 uppercase">Technical Contact</span>
            <input required name="technical_contact" onChange={handleChange} className="border border-slate-300 rounded-lg p-2 text-sm focus:border-indigo-500 focus:ring-1 focus:ring-indigo-500 outline-none transition-all" placeholder="e.g. John Doe" />
          </label>
          <label className="flex flex-col gap-1">
            <span className="font-label-code text-xs font-semibold text-slate-500 uppercase">Expected Users</span>
            <input required type="number" name="expected_users" value={formData.expected_users} onChange={handleChange} className="border border-slate-300 rounded-lg p-2 text-sm focus:border-indigo-500 focus:ring-1 focus:ring-indigo-500 outline-none transition-all" placeholder="e.g. 1000" />
          </label>
        </div>

        <div className="flex gap-3 mt-4">
          <button type="submit" disabled={isSubmitting} className="px-5 py-2.5 rounded-lg bg-indigo-600 hover:bg-indigo-700 text-white font-semibold text-sm shadow-md transition-all">
            {isSubmitting ? "Saving..." : "Save to Database"}
          </button>
          <button type="button" onClick={onCancel} className="px-5 py-2.5 rounded-lg bg-slate-100 hover:bg-slate-200 text-slate-700 font-semibold text-sm transition-all">
            Cancel
          </button>
        </div>
      </form>
    </section>
  );
};

const DealActionBanner = ({ deal, onRun, isEvaluating }) => {
  if (!deal) return null;
  return (
    <section className="relative rounded-xl p-6 bg-white border border-slate-200 shadow-sm overflow-hidden">
      <div className="relative z-10 flex flex-col xl:flex-row xl:items-center justify-between gap-6">
        <div className="flex flex-col gap-2">
          <div className="flex items-baseline gap-3">
            <h1 className="font-display-lg text-[28px] text-slate-900 font-bold tracking-tight">{deal.client_name}</h1>
            <span className="font-headline-sm text-base text-slate-500 font-normal">{deal.project_type}</span>
          </div>
          <div className="flex items-center gap-2 flex-wrap pt-1.5">
            <div className="flex items-center gap-1.5 px-3 py-1 rounded-md bg-slate-50 border border-slate-200 text-slate-700">
              <span className="material-symbols-outlined text-[15px] text-emerald-600">payments</span>
              <span className="font-label-code text-[11px]">BUDGET: {deal.budget}</span>
            </div>
            <div className="flex items-center gap-1.5 px-3 py-1 rounded-md bg-slate-50 border border-slate-200 text-slate-700">
              <span className="material-symbols-outlined text-[15px] text-indigo-600">schedule</span>
              <span className="font-label-code text-[11px]">TIMELINE: {deal.timeline}</span>
            </div>
          </div>
        </div>
        
        <button 
          onClick={onRun}
          disabled={isEvaluating}
          className={`flex items-center justify-center gap-2.5 px-5 py-2.5 rounded-lg text-white font-semibold text-sm shadow-md transition-all ${isEvaluating ? 'bg-slate-400 cursor-not-allowed' : 'bg-gradient-to-r from-cyan-600 to-cyan-500 hover:from-cyan-500 hover:to-cyan-600'}`}
        >
          {isEvaluating ? (
            <span className="material-symbols-outlined text-[18px] animate-spin">sync</span>
          ) : (
            <span className="material-symbols-outlined text-[18px]">bolt</span>
          )}
          <span>{isEvaluating ? 'Analyzing...' : 'Analyze & Start Handoff'}</span>
        </button>
      </div>
    </section>
  );
};

const PipelineFlowchart = ({ isEvaluating }) => (
  <section className="rounded-xl p-5 bg-white border border-slate-200 shadow-sm">
    <h3 className="font-headline-sm text-sm font-bold text-slate-900 mb-4">Autonomous CrewAI Agent Pipeline Architecture</h3>
    <div className="grid grid-cols-1 md:grid-cols-4 gap-3 relative">
      <div className={`p-3.5 rounded-xl border ${isEvaluating ? 'border-cyan-300 bg-cyan-50' : 'border-slate-200 bg-slate-50'}`}>
        <span className="font-label-code text-[10px] text-cyan-700 font-bold">Node 01 • Agent 1</span>
        <div className="font-bold text-[13px] text-slate-900 mt-1">Intake Agent</div>
        <div className="text-[11px] text-slate-600">Extracts scopes & checks docs</div>
      </div>
      <div className={`p-3.5 rounded-xl border ${isEvaluating ? 'border-indigo-300 bg-indigo-50' : 'border-slate-200 bg-slate-50'}`}>
        <span className="font-label-code text-[10px] text-indigo-700 font-bold">Node 02 • Agent 2</span>
        <div className="font-bold text-[13px] text-slate-900 mt-1">Delivery Agent</div>
        <div className="text-[11px] text-slate-600">Checks capacity & computes risk</div>
      </div>
      <div className="p-3.5 rounded-xl border border-slate-200 bg-slate-50">
        <span className="font-label-code text-[10px] text-emerald-700 font-bold">Node 03 • Database</span>
        <div className="font-bold text-[13px] text-slate-900 mt-1">Handoff Approval</div>
        <div className="text-[11px] text-slate-600">Saves project if LOW risk</div>
      </div>
      <div className="p-3.5 rounded-xl border border-slate-200 bg-slate-50">
        <span className="font-label-code text-[10px] text-rose-700 font-bold">Node 04 • Escalation</span>
        <div className="font-bold text-[13px] text-slate-900 mt-1">Escalation Trigger</div>
        <div className="text-[11px] text-slate-600">Halts handoff if HIGH risk</div>
      </div>
    </div>
  </section>
);

const DatabaseRecords = ({ records, onClear }) => (
  <section className="flex flex-col gap-4 mt-4">
    <div className="flex items-center justify-between">
      <h2 className="font-headline-md text-base font-bold text-slate-900">Permanent SQLite System Records</h2>
      <button onClick={onClear} className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg border border-rose-200 text-rose-600 hover:bg-rose-50 text-[11px] font-bold uppercase transition-all">
        <span className="material-symbols-outlined text-[14px]">delete_sweep</span>
        Clear History
      </button>
    </div>
    <div className="grid grid-cols-1 xl:grid-cols-2 gap-6">
      
      <div className="flex flex-col rounded-xl bg-white border border-slate-200 p-5 shadow-sm">
        <h3 className="font-headline-sm text-sm font-bold text-slate-900 mb-3">Recent Handoffs</h3>
        <table className="w-full text-left">
          <thead>
            <tr className="bg-slate-50 text-slate-500 text-[11px]">
              <th className="py-2 px-3">PROJECT ID</th>
              <th className="py-2 px-3">CLIENT</th>
              <th className="py-2 px-3">RISK</th>
              <th className="py-2 px-3">STATUS</th>
            </tr>
          </thead>
          <tbody className="text-xs text-slate-800">
            {records.handoffs.length === 0 && (
              <tr><td colSpan="4" className="py-3 px-3 text-slate-500">No handoffs yet.</td></tr>
            )}
            {records.handoffs.map((h, i) => (
              <tr key={i} className="border-t border-slate-100">
                <td className="py-2.5 px-3 font-code-stream font-semibold text-cyan-700">{h.project_id}</td>
                <td className="py-2.5 px-3">{h.client_name}</td>
                <td className="py-2.5 px-3 font-bold">{h.risk_level}</td>
                <td className="py-2.5 px-3">{h.handoff_status}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      <div className="flex flex-col rounded-xl bg-white border border-slate-200 p-5 shadow-sm">
        <h3 className="font-headline-sm text-sm font-bold text-slate-900 mb-3">Recent Escalations</h3>
        <table className="w-full text-left">
          <thead>
            <tr className="bg-slate-50 text-slate-500 text-[11px]">
              <th className="py-2 px-3">ESC ID</th>
              <th className="py-2 px-3">PROJECT</th>
              <th className="py-2 px-3">REASON</th>
            </tr>
          </thead>
          <tbody className="text-xs text-slate-800">
            {records.escalations.length === 0 && (
              <tr><td colSpan="3" className="py-3 px-3 text-slate-500">No escalations yet.</td></tr>
            )}
            {records.escalations.map((e, i) => (
              <tr key={i} className="border-t border-slate-100">
                <td className="py-2.5 px-3 font-code-stream font-semibold text-rose-700">ESC-{e.esc_id}</td>
                <td className="py-2.5 px-3 font-code-stream">{e.project_id}</td>
                <td className="py-2.5 px-3">{e.reason}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

    </div>
  </section>
);

const CustomMessageBanner = ({ isEvaluating, result }) => {
  if (isEvaluating) {
    return (
      <section className="rounded-xl p-6 bg-slate-50 border border-slate-200 shadow-sm flex items-center justify-center gap-3">
        <span className="material-symbols-outlined text-[24px] animate-spin text-slate-400">sync</span>
        <span className="font-headline-sm text-slate-600 font-medium">Running CrewAI analysis...</span>
      </section>
    );
  }
  
  if (!result || !result.custom_message) return null;
  
  const color = result.custom_color || "slate";
  const icon = color === "emerald" ? "check_circle" : color === "amber" ? "search_off" : "gpp_bad";
  
  const bgColors = { emerald: "bg-emerald-50", amber: "bg-amber-50", rose: "bg-rose-50", slate: "bg-slate-50" };
  const borderColors = { emerald: "border-emerald-200", amber: "border-amber-200", rose: "border-rose-200", slate: "border-slate-200" };
  const textColors = { emerald: "text-emerald-900", amber: "text-amber-900", rose: "text-rose-900", slate: "text-slate-900" };
  const iconColors = { emerald: "text-emerald-600", amber: "text-amber-600", rose: "text-rose-600", slate: "text-slate-600" };
  const subTextColors = { emerald: "text-emerald-800", amber: "text-amber-800", rose: "text-rose-800", slate: "text-slate-800" };

  return (
    <section className={`rounded-xl p-6 ${bgColors[color]} border ${borderColors[color]} shadow-sm flex items-start gap-4`}>
      <span className={`material-symbols-outlined text-[28px] ${iconColors[color]} mt-0.5`}>{icon}</span>
      <div className="flex flex-col gap-1">
        <h3 className={`font-headline-sm text-lg ${textColors[color]} font-bold`}>AI Analysis Verdict</h3>
        <p className={`font-code-stream text-sm ${subTextColors[color]} font-medium`}>{result.custom_message}</p>
      </div>
    </section>
  );
};

ReactDOM.createRoot(document.getElementById("root")).render(<App />);
