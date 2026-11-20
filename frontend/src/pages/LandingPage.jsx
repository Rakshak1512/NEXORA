import React from 'react';
import { Link } from 'react-router-dom';
import { 
  ShieldCheck, ArrowRight, Lock, Server, Cpu, 
  BrainCircuit, Sparkles, CheckCircle2, Zap, 
  Terminal, EyeOff, FileText, ChevronRight, Activity, 
  Layers, Database, BarChart4, AlertTriangle, KeyRound
} from 'lucide-react';
import Button from '../components/common/Button';

const LandingPage = () => {
  return (
    <div className="min-h-screen bg-[#070C14] text-slate-100 selection:bg-cyan-500 selection:text-black">
      {/* 1. TOP NAVIGATION */}
      <header className="sticky top-0 z-50 glass-panel border-b border-[#1A2740] px-6 lg:px-12 h-20 flex items-center justify-between">
        <div className="flex items-center gap-3">
          <div className="w-9 h-9 rounded-xl bg-gradient-to-tr from-cyan-500 to-teal-400 flex items-center justify-center shadow-lg shadow-cyan-500/20">
            <ShieldCheck className="w-5 h-5 text-slate-950 font-bold" />
          </div>
          <div>
            <span className="font-extrabold text-lg tracking-wider text-slate-100 flex items-center gap-1.5">
              CICADA <span className="text-cyan-400 font-mono text-xs px-1.5 py-0.5 rounded bg-cyan-500/10 border border-cyan-500/20">OBSERVE</span>
            </span>
          </div>
        </div>

        <nav className="hidden md:flex items-center gap-8 text-sm font-medium text-slate-300">
          <a href="#features" className="hover:text-cyan-400 transition">Features</a>
          <a href="#architecture" className="hover:text-cyan-400 transition">Architecture</a>
          <a href="#security" className="hover:text-cyan-400 transition">Security</a>
          <a href="#aiops" className="hover:text-cyan-400 transition">AIOps</a>
          <a href="#roadmap" className="hover:text-cyan-400 transition">Roadmap</a>
        </nav>

        <div className="flex items-center gap-3">
          <Link to="/login">
            <Button variant="ghost" size="sm">Log In</Button>
          </Link>
          <Link to="/register">
            <Button variant="primary" size="sm">Get Started</Button>
          </Link>
        </div>
      </header>

      {/* 2. SECTION 1: ANIMATED HERO */}
      <section className="relative pt-20 pb-28 px-6 lg:px-12 overflow-hidden text-center max-w-5xl mx-auto">
        <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[600px] h-[350px] bg-cyan-500/10 blur-[130px] rounded-full pointer-events-none" />

        <div className="inline-flex items-center gap-2 px-3.5 py-1.5 rounded-full bg-cyan-500/10 border border-cyan-500/20 text-xs text-cyan-300 font-mono mb-8">
          <Sparkles className="w-3.5 h-3.5" />
          <span>CICADA 2026 OFFICIAL HACKATHON WINNING PLATFORM</span>
        </div>

        <h1 className="text-4xl sm:text-6xl lg:text-7xl font-extrabold tracking-tight text-slate-100 leading-[1.1] mb-6">
          Intelligent Observability.<br />
          <span className="text-transparent bg-clip-text bg-gradient-to-r from-cyan-400 via-teal-300 to-cyan-500">
            Absolute Data Control.
          </span>
        </h1>

        <p className="text-lg sm:text-xl text-slate-400 max-w-3xl mx-auto leading-relaxed mb-10">
          Monitor your enterprise infrastructure, detect anomalies and understand incidents through AI-powered intelligence while keeping sensitive operational data inside your environment.
        </p>

        <div className="flex flex-col sm:flex-row items-center justify-center gap-4">
          <Link to="/dashboard">
            <Button variant="primary" size="lg" icon={ArrowRight}>
              Explore Platform
            </Button>
          </Link>
          <a href="#architecture">
            <Button variant="secondary" size="lg">
              View Architecture
            </Button>
          </a>
        </div>
      </section>

      {/* 3. SECTION 2: PRODUCT DASHBOARD PREVIEW */}
      <section className="px-6 lg:px-12 pb-24 max-w-6xl mx-auto">
        <div className="glass-panel rounded-2xl border border-cyan-500/30 p-2 shadow-2xl shadow-cyan-500/10 relative group">
          <div className="bg-[#0A1220] rounded-xl p-4 sm:p-6 border border-[#1A2740]">
            {/* Window chrome */}
            <div className="flex items-center justify-between pb-4 border-b border-[#1A2740] mb-6">
              <div className="flex items-center gap-2">
                <span className="w-3 h-3 rounded-full bg-rose-500" />
                <span className="w-3 h-3 rounded-full bg-amber-500" />
                <span className="w-3 h-3 rounded-full bg-emerald-500" />
                <span className="text-xs font-mono text-slate-500 ml-3">cicada-observe.enterprise.io/dashboard</span>
              </div>
              <span className="text-xs font-mono text-emerald-400 flex items-center gap-1.5">
                <span className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse" />
                EGRESS VERIFIED (ZERO SECRETS LEAKED)
              </span>
            </div>

            {/* Dashboard Mock Grid */}
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 mb-6">
              <div className="p-4 rounded-xl bg-[#0D1524] border border-[#1A2740]">
                <span className="text-xs text-slate-400">Total Monitored Nodes</span>
                <div className="text-2xl font-bold text-slate-100 mt-1">4 Clusters</div>
                <span className="text-xs text-emerald-400 font-mono mt-2 block">100% Online Heartbeat</span>
              </div>
              <div className="p-4 rounded-xl bg-[#0D1524] border border-[#1A2740]">
                <span className="text-xs text-slate-400">System Health State</span>
                <div className="text-2xl font-bold text-cyan-400 mt-1">EXCELLENT</div>
                <span className="text-xs text-slate-400 font-mono mt-2 block">Nominal baselines</span>
              </div>
              <div className="p-4 rounded-xl bg-[#0D1524] border border-[#1A2740]">
                <span className="text-xs text-slate-400">P95 Delivery Latency</span>
                <div className="text-2xl font-bold text-teal-300 mt-1">24.8 ms</div>
                <span className="text-xs text-cyan-400 font-mono mt-2 block">Hackathon Target: &lt;10s</span>
              </div>
              <div className="p-4 rounded-xl bg-[#0D1524] border border-[#1A2740]">
                <span className="text-xs text-slate-400">Local Queue Depth</span>
                <div className="text-2xl font-bold text-slate-100 mt-1">0 Records</div>
                <span className="text-xs text-emerald-400 font-mono mt-2 block">Zero loss / zero dupes</span>
              </div>
            </div>

            <div className="p-4 rounded-xl bg-[#070C14]/80 border border-cyan-500/20 flex flex-col md:flex-row items-center justify-between gap-4">
              <div className="flex items-center gap-3">
                <div className="p-2 rounded-lg bg-cyan-500/10 text-cyan-400">
                  <BrainCircuit className="w-5 h-5" />
                </div>
                <div>
                  <div className="text-sm font-semibold text-slate-200">Explainable AIOps Anomaly Engine Active</div>
                  <div className="text-xs text-slate-400">Isolation Forest + Temporal Causal Graph running on metadata summaries</div>
                </div>
              </div>
              <Link to="/dashboard">
                <Button variant="primary" size="sm">Launch Live Console</Button>
              </Link>
            </div>
          </div>
        </div>
      </section>

      {/* 4. SECTION 3: PROBLEM AND SOLUTION */}
      <section id="features" className="py-20 px-6 lg:px-12 max-w-6xl mx-auto border-t border-[#1A2740]">
        <div className="text-center max-w-3xl mx-auto mb-16">
          <h2 className="text-xs font-mono uppercase tracking-widest text-cyan-400 mb-2">The Observability Paradox</h2>
          <h3 className="text-3xl sm:text-4xl font-bold text-slate-100">Why Legacy SaaS APM Violates Enterprise Privacy</h3>
          <p className="text-slate-400 mt-3 text-sm sm:text-base">
            Modern SaaS observability vendors demand raw logs, database queries, and environment dumps—exposing sensitive credentials, API keys, and customer PII to cloud breaches.
          </p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
          <div className="p-8 rounded-2xl bg-rose-950/10 border border-rose-500/30">
            <div className="flex items-center gap-3 mb-4 text-rose-400">
              <AlertTriangle className="w-6 h-6" />
              <h4 className="text-lg font-bold">The Problem: Raw Log Ingestion</h4>
            </div>
            <ul className="space-y-3 text-sm text-slate-300">
              <li className="flex items-start gap-2">
                <span className="text-rose-400 font-bold">✕</span>
                <span>Plaintext passwords, connection strings, and JWTs shipped to 3rd party SaaS.</span>
              </li>
              <li className="flex items-start gap-2">
                <span className="text-rose-400 font-bold">✕</span>
                <span>Unpredictable network egress costs shipping terabytes of raw debug garbage.</span>
              </li>
              <li className="flex items-start gap-2">
                <span className="text-rose-400 font-bold">✕</span>
                <span>Massive compliance liabilities across GDPR, HIPAA, and SOC-2 data residency rules.</span>
              </li>
            </ul>
          </div>

          <div className="p-8 rounded-2xl bg-cyan-950/10 border border-cyan-500/30">
            <div className="flex items-center gap-3 mb-4 text-cyan-400">
              <ShieldCheck className="w-6 h-6" />
              <h4 className="text-lg font-bold">The Solution: Two-Tier Local-First AIOps</h4>
            </div>
            <ul className="space-y-3 text-sm text-slate-300">
              <li className="flex items-start gap-2">
                <CheckCircle2 className="w-5 h-5 text-cyan-400 shrink-0" />
                <span>Local perimeter collector scrubs and redacts 100% of raw secrets before egress.</span>
              </li>
              <li className="flex items-start gap-2">
                <CheckCircle2 className="w-5 h-5 text-cyan-400 shrink-0" />
                <span>Strict metadata allowlist validation guarantees only approved health signals leave.</span>
              </li>
              <li className="flex items-start gap-2">
                <CheckCircle2 className="w-5 h-5 text-cyan-400 shrink-0" />
                <span>Auditable Egress Proof Center provides cryptographic SHA-256 evidence of every payload.</span>
              </li>
            </ul>
          </div>
        </div>
      </section>

      {/* 5. SECTION 4: TWO-TIER ARCHITECTURE */}
      <section id="architecture" className="py-20 px-6 lg:px-12 max-w-6xl mx-auto border-t border-[#1A2740]">
        <div className="text-center max-w-3xl mx-auto mb-16">
          <h2 className="text-xs font-mono uppercase tracking-widest text-teal-400 mb-2">Architectural Guarantee</h2>
          <h3 className="text-3xl sm:text-4xl font-bold text-slate-100">Two-Tier System Topology</h3>
          <p className="text-slate-400 mt-3 text-sm sm:text-base">
            Clean architectural separation ensures cloud operators never possess raw logs or production secrets.
          </p>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-8 items-stretch">
          {/* Tier 1 */}
          <div className="glass-panel p-8 rounded-2xl border border-cyan-500/30 flex flex-col justify-between">
            <div>
              <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-cyan-500/10 text-cyan-400 text-xs font-mono mb-4">
                <Lock className="w-3.5 h-3.5" /> TIER 1: CUSTOMER ON-PREMISES / VPC
              </div>
              <h4 className="text-xl font-bold text-slate-100 mb-2">Independent Python Local Collector</h4>
              <p className="text-slate-400 text-sm mb-6">
                Runs as an isolated background daemon on your Kubernetes node or Linux VM. Uses psutil, regex pattern redactors, and an SQLite persistent queue.
              </p>
              <div className="space-y-3 font-mono text-xs">
                <div className="p-3 rounded-lg bg-[#070C14] border border-[#1A2740] flex items-center justify-between">
                  <span className="text-slate-400">Raw Logs & Credentials:</span>
                  <span className="text-rose-400 font-semibold">KEPT LOCAL ONLY</span>
                </div>
                <div className="p-3 rounded-lg bg-[#070C14] border border-[#1A2740] flex items-center justify-between">
                  <span className="text-slate-400">Persistent Disk Queue:</span>
                  <span className="text-emerald-400 font-semibold">SQLite buffer.db</span>
                </div>
                <div className="p-3 rounded-lg bg-[#070C14] border border-[#1A2740] flex items-center justify-between">
                  <span className="text-slate-400">Allowlist Strictness:</span>
                  <span className="text-cyan-400 font-semibold">HARD ENFORCED</span>
                </div>
              </div>
            </div>
            <div className="mt-8 pt-4 border-t border-[#1A2740] text-xs text-slate-500">
              Zero dependencies on browser or SaaS availability.
            </div>
          </div>

          {/* Tier 2 */}
          <div className="glass-panel p-8 rounded-2xl border border-teal-500/30 flex flex-col justify-between">
            <div>
              <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-teal-500/10 text-teal-300 text-xs font-mono mb-4">
                <Server className="w-3.5 h-3.5" /> TIER 2: CENTRAL SAAS OBSERVABILITY PLATFORM
              </div>
              <h4 className="text-xl font-bold text-slate-100 mb-2">FastAPI + Supabase PostgreSQL Engine</h4>
              <p className="text-slate-400 text-sm mb-6">
                Ingests approved numerical metrics and high-level security summaries. Executes Isolation Forest anomaly detection and deterministic causal correlation.
              </p>
              <div className="space-y-3 font-mono text-xs">
                <div className="p-3 rounded-lg bg-[#070C14] border border-[#1A2740] flex items-center justify-between">
                  <span className="text-slate-400">Ingested Payload:</span>
                  <span className="text-emerald-400 font-semibold">Approved Metadata Only</span>
                </div>
                <div className="p-3 rounded-lg bg-[#070C14] border border-[#1A2740] flex items-center justify-between">
                  <span className="text-slate-400">Data Isolation:</span>
                  <span className="text-cyan-400 font-semibold">Row-Level Security (RLS)</span>
                </div>
                <div className="p-3 rounded-lg bg-[#070C14] border border-[#1A2740] flex items-center justify-between">
                  <span className="text-slate-400">AI Intelligence:</span>
                  <span className="text-teal-300 font-semibold">Explainable Anomaly Engine</span>
                </div>
              </div>
            </div>
            <div className="mt-8 pt-4 border-t border-[#1A2740] text-xs text-slate-500">
              Zero access to raw customer logs by design.
            </div>
          </div>
        </div>
      </section>

      {/* 6. SECTION 5: LOCAL-FIRST PRIVACY & EGRESS PROOF */}
      <section id="security" className="py-20 px-6 lg:px-12 max-w-6xl mx-auto border-t border-[#1A2740]">
        <div className="text-center max-w-3xl mx-auto mb-16">
          <h2 className="text-xs font-mono uppercase tracking-widest text-cyan-400 mb-2">Zero Blind Trust</h2>
          <h3 className="text-3xl sm:text-4xl font-bold text-slate-100">Egress Proof Center</h3>
          <p className="text-slate-400 mt-3 text-sm sm:text-base">
            Don't trust our words—inspect cryptographic proof of every outgoing payload before and after redaction.
          </p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          <div className="p-6 rounded-xl bg-[#0D1524] border border-[#1A2740]">
            <KeyRound className="w-8 h-8 text-cyan-400 mb-3" />
            <h4 className="font-bold text-slate-200 text-base mb-1">Local Redaction Engine</h4>
            <p className="text-slate-400 text-xs leading-relaxed">
              Regex pattern detectors identify AWS keys, bearer tokens, passwords, and connection strings locally, neutralizing them before payload generation.
            </p>
          </div>
          <div className="p-6 rounded-xl bg-[#0D1524] border border-[#1A2740]">
            <FileText className="w-8 h-8 text-teal-300 mb-3" />
            <h4 className="font-bold text-slate-200 text-base mb-1">Strict Allowlist Filter</h4>
            <p className="text-slate-400 text-xs leading-relaxed">
              Only pre-approved numerical and categorical fields are admitted. Unlisted or unknown properties are unconditionally dropped at the perimeter.
            </p>
          </div>
          <div className="p-6 rounded-xl bg-[#0D1524] border border-[#1A2740]">
            <CheckCircle2 className="w-8 h-8 text-emerald-400 mb-3" />
            <h4 className="font-bold text-slate-200 text-base mb-1">SHA-256 Egress Hash</h4>
            <p className="text-slate-400 text-xs leading-relaxed">
              Every delivered payload has its cryptographic fingerprint recorded in both the local buffer and SaaS audit ledger to guarantee absolute integrity.
            </p>
          </div>
        </div>
      </section>

      {/* 7. SECTION 6 & 7: AIOPS & EXPLAINABLE RECOMMENDATIONS */}
      <section id="aiops" className="py-20 px-6 lg:px-12 max-w-6xl mx-auto border-t border-[#1A2740]">
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-12 items-center">
          <div>
            <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-cyan-500/10 text-cyan-400 text-xs font-mono mb-4">
              <BrainCircuit className="w-3.5 h-3.5" /> MULTIVARIATE AIOPS
            </div>
            <h3 className="text-3xl sm:text-4xl font-bold text-slate-100 mb-4 leading-tight">
              Explainable Anomaly Detection, Not Black-Box Magic.
            </h3>
            <p className="text-slate-400 text-sm sm:text-base leading-relaxed mb-6">
              Our AIOps engine correlates signals across compute, memory, storage, and networking within temporal sliding windows. Every alert includes baseline sigma deviations, causal hypotheses, and verified rollback plans.
            </p>
            <div className="space-y-3">
              <div className="flex items-center gap-3 text-sm text-slate-300">
                <CheckCircle2 className="w-4 h-4 text-cyan-400" />
                <span>Scikit-learn Isolation Forest on multi-dimensional telemetry vectors.</span>
              </div>
              <div className="flex items-center gap-3 text-sm text-slate-300">
                <CheckCircle2 className="w-4 h-4 text-cyan-400" />
                <span>Noise reduction grouping correlated alerts into one unified incident.</span>
              </div>
              <div className="flex items-center gap-3 text-sm text-slate-300">
                <CheckCircle2 className="w-4 h-4 text-cyan-400" />
                <span>Deterministic fallback mode functions 100% offline without external LLMs.</span>
              </div>
            </div>
          </div>

          <div className="glass-panel rounded-2xl border border-cyan-500/30 p-6">
            <div className="text-xs font-mono text-cyan-400 uppercase tracking-wider mb-2">Live AIOps Correlation Sample</div>
            <div className="p-4 rounded-xl bg-[#070C14] border border-[#1A2740] font-mono text-xs space-y-2">
              <div className="text-slate-400">Incident: <span className="text-slate-200">INC-2026-0042</span></div>
              <div className="text-slate-400">Anomaly: <span className="text-amber-400">Worker Pool Memory Exhaustion</span></div>
              <div className="text-slate-400">Baseline Deviation: <span className="text-cyan-400">+8.5σ from 7-day median</span></div>
              <div className="text-slate-400">Root Cause Hypothesis: <span className="text-slate-200">Connection leak in worker thread pool</span></div>
              <div className="p-3 rounded-lg bg-cyan-950/30 border border-cyan-500/30 text-cyan-300 mt-2">
                Action: Staged rolling recycle of 4 worker pods + cache flush.
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* 8. SECTION 8 & 9: AUTONOMOUS OPERATIONS ROADMAP */}
      <section id="roadmap" className="py-20 px-6 lg:px-12 max-w-6xl mx-auto border-t border-[#1A2740]">
        <div className="text-center max-w-3xl mx-auto mb-16">
          <h2 className="text-xs font-mono uppercase tracking-widest text-teal-400 mb-2">Future of Infrastructure</h2>
          <h3 className="text-3xl sm:text-4xl font-bold text-slate-100">Autonomous Operations with Policy Guardrails</h3>
          <p className="text-slate-400 mt-3 text-sm sm:text-base">
            Transition safely from manual ticket firefighting to policy-governed autonomous self-healing.
          </p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          <div className="p-5 rounded-xl bg-[#0D1524] border border-cyan-500/40">
            <span className="text-xs font-mono text-cyan-400">PHASE 1 (LIVE)</span>
            <h5 className="font-bold text-slate-100 mt-1">Operator Approval</h5>
            <p className="text-xs text-slate-400 mt-2">
              AI suggests remediation; human operator verifies policy check and executes with 1-click.
            </p>
          </div>
          <div className="p-5 rounded-xl bg-[#0D1524] border border-[#1A2740]">
            <span className="text-xs font-mono text-slate-400">PHASE 2</span>
            <h5 className="font-bold text-slate-100 mt-1">Policy-Bounded Auto-Heal</h5>
            <p className="text-xs text-slate-400 mt-2">
              Low-risk actions (pod recycles, cache purge) execute automatically during off-peak windows.
            </p>
          </div>
          <div className="p-5 rounded-xl bg-[#0D1524] border border-[#1A2740]">
            <span className="text-xs font-mono text-slate-400">PHASE 3</span>
            <h5 className="font-bold text-slate-100 mt-1">Cross-Region Traffic Steer</h5>
            <p className="text-xs text-slate-400 mt-2">
              Autonomous rerouting of global tenant requests away from degrading edge gateways.
            </p>
          </div>
          <div className="p-5 rounded-xl bg-[#0D1524] border border-[#1A2740]">
            <span className="text-xs font-mono text-slate-400">PHASE 4</span>
            <h5 className="font-bold text-slate-100 mt-1">Predictive Capacity Balancing</h5>
            <p className="text-xs text-slate-400 mt-2">
              Pre-allocating cluster nodes based on seasonal ARIMA and neural time-series forecasts.
            </p>
          </div>
        </div>
      </section>

      {/* 9. FOOTER */}
      <footer className="py-12 px-6 lg:px-12 border-t border-[#1A2740] bg-[#05080E] text-slate-400 text-xs">
        <div className="max-w-6xl mx-auto flex flex-col md:flex-row items-center justify-between gap-6">
          <div className="flex items-center gap-3">
            <div className="w-7 h-7 rounded-lg bg-cyan-500/10 border border-cyan-500/20 flex items-center justify-center text-cyan-400 font-bold">
              C
            </div>
            <div>
              <span className="font-bold text-slate-200">CICADA OBSERVE</span> — Official Hackathon 2026 Production Platform
            </div>
          </div>
          <div className="flex items-center gap-6">
            <Link to="/dashboard" className="hover:text-cyan-400 transition">Console</Link>
            <Link to="/egress-proof" className="hover:text-cyan-400 transition">Egress Center</Link>
            <Link to="/login" className="hover:text-cyan-400 transition">Operator Login</Link>
          </div>
          <div>
            Built with React, FastAPI, Supabase, psutil & Scikit-Learn.
          </div>
        </div>
      </footer>
    </div>
  );
};

export default LandingPage;

