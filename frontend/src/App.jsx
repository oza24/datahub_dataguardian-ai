import React, { useState, useRef, useEffect, useCallback } from "react";
import {
  Bot,
  Send,
  Database,
  GitFork,
  AlertTriangle,
  Code2,
  ShieldAlert,
  Terminal,
  Sparkles,
  ExternalLink,
  Copy,
  Check,
  RefreshCw,
  ChevronRight,
  Zap,
  XCircle,
  Workflow,
} from "lucide-react";

// Environment variables with fallbacks
const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || "http://localhost:8000";
const DATAHUB_URL = import.meta.env.VITE_DATAHUB_URL || "http://localhost:9002";

const QUICK_PROMPTS = [
  {
    title: "Blast Radius Impact Analysis",
    prompt: "What is the impact if I remove customer_age column?",
    desc: "Traverses 3-tier DataHub lineage to calculate change risk score.",
    icon: AlertTriangle,
    iconColor: "text-rose-400",
  },
  {
    title: "Zero-Hallucination dbt CodeGen",
    prompt: "Generate a dbt model for orders",
    desc: "Pulls verified DataHub schema metadata to generate SQL models.",
    icon: Code2,
    iconColor: "text-emerald-400",
  },
  {
    title: "Catalog Schema Inspection",
    prompt: "Inspect schema for dim_customers",
    desc: "Retrieves field types, nullability, and primary keys from GMS.",
    icon: Database,
    iconColor: "text-sky-400",
  },
];

const AGENT_CONFIG = {
  schema_agent: {
    label: "Schema Agent",
    color: "bg-blue-500/10 text-blue-400 border-blue-500/30",
    icon: Database,
  },
  lineage_agent: {
    label: "Lineage Agent",
    color: "bg-violet-500/10 text-violet-400 border-violet-500/30",
    icon: GitFork,
  },
  impact_agent: {
    label: "Impact Agent",
    color: "bg-amber-500/10 text-amber-400 border-amber-500/30",
    icon: AlertTriangle,
  },
  codegen_agent: {
    label: "CodeGen Agent",
    color: "bg-emerald-500/10 text-emerald-400 border-emerald-500/30",
    icon: Code2,
  },
  action_agent: {
    label: "Action Agent",
    color: "bg-sky-500/10 text-sky-400 border-sky-500/30",
    icon: Zap,
  },
  recommendation_agent: {
    label: "Remediation Agent",
    color: "bg-rose-500/10 text-rose-400 border-rose-500/30",
    icon: ShieldAlert,
  },
};

const getAgentConfig = (agentName) => {
  return (
    AGENT_CONFIG[agentName] || {
      label: "Supervisor Router",
      color: "bg-slate-500/10 text-slate-400 border-slate-500/30",
      icon: Bot,
    }
  );
};

function RiskScoreBadge({ score }) {
  if (score === undefined || score === null) return null;
  const isHigh = score >= 70;
  const isMedium = score >= 40 && score < 70;
  return (
    <span
      className={`inline-flex items-center gap-1 px-2.5 py-1 rounded-md text-[11px] font-bold border ${
        isHigh
          ? "bg-rose-500/15 text-rose-400 border-rose-500/30"
          : isMedium
          ? "bg-amber-500/15 text-amber-400 border-amber-500/30"
          : "bg-emerald-500/15 text-emerald-400 border-emerald-500/30"
      }`}
    >
      <AlertTriangle className="w-3 h-3" />
      Risk: {score}/100 {isHigh ? "HIGH" : isMedium ? "MED" : "LOW"}
    </span>
  );
}

function CodeBlock({ code }) {
  const [copied, setCopied] = useState(false);

  const handleCopy = () => {
    navigator.clipboard.writeText(code);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  return (
    <div className="relative rounded-xl overflow-hidden border border-slate-800 bg-slate-950 my-3">
      <div className="flex items-center justify-between px-4 py-2 border-b border-slate-800 bg-slate-900/60">
        <span className="flex items-center gap-1.5 text-[11px] text-emerald-400 font-mono font-medium">
          <Code2 className="w-3.5 h-3.5" />
          Generated SQL / dbt Model
        </span>
        <button
          onClick={handleCopy}
          className="flex items-center gap-1 bg-slate-800 hover:bg-slate-700 text-slate-300 px-2.5 py-1 rounded-md text-[11px] font-mono transition cursor-pointer"
        >
          {copied ? (
            <>
              <Check className="w-3 h-3 text-emerald-400" />
              <span className="text-emerald-400">Copied!</span>
            </>
          ) : (
            <>
              <Copy className="w-3 h-3" />
              Copy
            </>
          )}
        </button>
      </div>
      <pre className="p-4 text-[12px] font-mono text-emerald-300 overflow-x-auto leading-relaxed m-0">
        <code>{code.trim()}</code>
      </pre>
    </div>
  );
}

function renderContentWithCode(content) {
  if (!content || typeof content !== "string") return null;

  if (content.includes("```")) {
    const parts = content.split(/```[a-zA-Z]*\n?/);
    return (
      <div className="space-y-2">
        {parts.map((part, pIdx) => {
          if (pIdx % 2 === 1) {
            return <CodeBlock key={pIdx} code={part} />;
          }
          if (!part.trim()) return null;
          return (
            <div key={pIdx} className="whitespace-pre-wrap leading-relaxed">
              {part}
            </div>
          );
        })}
      </div>
    );
  }

  return <div className="whitespace-pre-wrap leading-relaxed">{content}</div>;
}

function AgentStepCard({ step, stepIdx }) {
  const config = getAgentConfig(step.agent);
  const Icon = config.icon;

  return (
    <div className="border-l-2 border-slate-800 pl-4 space-y-2.5">
      <div className="flex items-center gap-2 flex-wrap">
        <span
          className={`inline-flex items-center gap-1.5 px-3 py-1 rounded-lg text-[11px] font-bold border ${config.color}`}
        >
          <Icon className="w-3.5 h-3.5" />
          {config.label}
        </span>

        <RiskScoreBadge score={step.state?.risk_score} />

        {step.state?.has_code && (
          <span className="inline-flex items-center gap-1 px-2 py-1 rounded-md text-[10px] font-mono font-medium bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">
            <Code2 className="w-3 h-3" />
            CODE GENERATED
          </span>
        )}

        <span className="text-[10px] text-slate-600 font-mono ml-auto">
          step {stepIdx + 1}
        </span>
      </div>

      <div className="text-xs text-slate-300 font-mono bg-slate-950 p-4 rounded-xl border border-slate-800/80 shadow-inner">
        {renderContentWithCode(step.content)}
      </div>
    </div>
  );
}

function ExecutionTrace({ message }) {
  return (
    <div className="space-y-4 border border-slate-800 bg-slate-900/40 p-5 rounded-2xl glass-card shadow-xl">
      <div className="flex items-center justify-between border-b border-slate-800 pb-3">
        <div className="flex items-center gap-2 text-[11px] font-bold text-sky-400 uppercase tracking-wider">
          <Workflow className="w-4 h-4" />
          LangGraph Execution Trace
        </div>
        <span className="text-[10px] text-slate-500 font-mono">
          {message.trace?.length || 0} agent steps
        </span>
      </div>

      <div className="space-y-4">
        {message.trace?.map((step, sIdx) => (
          <AgentStepCard key={sIdx} step={step} stepIdx={sIdx} />
        ))}
      </div>
    </div>
  );
}

function Sidebar({ onSend, loading }) {
  return (
    <aside className="w-80 border-r border-slate-800/80 bg-slate-900/60 flex flex-col justify-between glass-panel flex-shrink-0 h-screen">
      <div className="p-5 space-y-6 overflow-y-auto">
        <div className="flex items-center gap-3">
          <div className="p-2.5 bg-sky-500/10 border border-sky-500/30 rounded-xl">
            <ShieldAlert className="w-6 h-6 text-sky-400" />
          </div>
          <div>
            <h1 className="font-bold text-[15px] text-slate-100 tracking-wide">
              DataGuardian AI
            </h1>
            <p className="text-[11px] text-sky-400 font-medium">
              DataHub Autonomous Copilot
            </p>
          </div>
        </div>

        <div className="space-y-2.5">
          <div className="flex items-center gap-1.5 text-[10px] font-bold uppercase tracking-widest text-slate-400">
            <Sparkles className="w-3 h-3 text-sky-400" />
            Quick Demo Triggers
          </div>

          {QUICK_PROMPTS.map((qp, idx) => {
            const QPIcon = qp.icon;
            return (
              <button
                key={idx}
                onClick={() => onSend(qp.prompt)}
                disabled={loading}
                className="w-full text-left p-3.5 rounded-xl border border-slate-800 bg-slate-950/40 hover:bg-slate-800/60 hover:border-slate-700 transition group space-y-1.5 disabled:opacity-40 cursor-pointer"
              >
                <div className="flex items-center justify-between">
                  <span className="font-medium text-slate-200 text-xs flex items-center gap-1.5 group-hover:text-sky-300">
                    <QPIcon className={`w-3.5 h-3.5 ${qp.iconColor}`} />
                    {qp.title}
                  </span>
                  <ChevronRight className="w-3.5 h-3.5 text-slate-600 group-hover:text-slate-400 group-hover:translate-x-0.5 transition" />
                </div>
                <p className="text-[11px] text-slate-500 leading-normal line-clamp-2">
                  {qp.desc}
                </p>
              </button>
            );
          })}
        </div>
      </div>

      <div className="p-4 border-t border-slate-800/80 space-y-2.5 bg-slate-950/80 text-xs">
        <div className="flex items-center justify-between">
          <span className="flex items-center gap-1.5 text-slate-400">
            <Database className="w-3.5 h-3.5" />
            DataHub GMS
          </span>
          <a
            href={DATAHUB_URL}
            target="_blank"
            rel="noreferrer"
            className="flex items-center gap-1 text-emerald-400 hover:text-emerald-300 font-medium"
          >
            <span className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse"></span>
            Live
            <ExternalLink className="w-3 h-3" />
          </a>
        </div>

        <div className="flex items-center justify-between">
          <span className="flex items-center gap-1.5 text-slate-400">
            <Zap className="w-3.5 h-3.5" />
            Model Engine
          </span>
          <span className="text-sky-400 font-medium">Gemini Flash</span>
        </div>
      </div>
    </aside>
  );
}

export default function App() {
  const [prompt, setPrompt] = useState("");
  const [loading, setLoading] = useState(false);
  const [chatHistory, setChatHistory] = useState([]);
  const chatEndRef = useRef(null);

  const scrollToBottom = useCallback(() => {
    chatEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, []);

  useEffect(() => {
    scrollToBottom();
  }, [chatHistory, loading, scrollToBottom]);

  const handleSend = useCallback(
    async (queryText) => {
      const q = typeof queryText === "string" ? queryText : prompt;
      if (!q || !q.trim() || loading) return;

      const userMessage = { role: "user", content: q };
      setChatHistory((prev) => [...prev, userMessage]);
      setPrompt("");
      setLoading(true);

      try {
        const response = await fetch(`${API_BASE_URL}/api/chat`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ prompt: q }),
        });

        if (!response.ok) {
          throw new Error(`Server returned status ${response.status}`);
        }

        const data = await response.json();

        if (data.status === "success") {
          setChatHistory((prev) => [
            ...prev,
            { role: "assistant", trace: data.trace, _id: Date.now() },
          ]);
        } else {
          throw new Error(data.detail || "Execution failed.");
        }
      } catch (err) {
        setChatHistory((prev) => [
          ...prev,
          { role: "error", content: err.message, _id: Date.now() },
        ]);
      } finally {
        setLoading(false);
      }
    },
    [prompt, loading]
  );

  return (
    <div className="flex h-screen bg-slate-950 text-slate-100 font-sans overflow-hidden">
      <Sidebar loading={loading} onSend={handleSend} />

      <main className="flex-1 flex flex-col justify-between bg-slate-950 overflow-hidden min-w-0">
        <header className="h-14 border-b border-slate-800/80 px-6 flex items-center justify-between bg-slate-900/40 glass-panel flex-shrink-0">
          <div className="flex items-center gap-2.5">
            <Terminal className="w-4 h-4 text-sky-400" />
            <span className="font-semibold text-sm text-slate-200">
              Multi-Agent Orchestration Workspace
            </span>
          </div>

          <div className="flex items-center gap-3">
            <button
              onClick={() => setChatHistory([])}
              className="text-xs text-slate-400 hover:text-slate-200 flex items-center gap-1.5 bg-slate-900 border border-slate-800 px-3 py-1.5 rounded-lg transition cursor-pointer"
            >
              <RefreshCw className="w-3 h-3" /> Clear Session
            </button>
            <span className="text-xs px-3 py-1 bg-sky-500/10 border border-sky-500/30 rounded-full text-sky-300 font-medium">
              Zero-Hallucination Guardrail Active
            </span>
          </div>
        </header>

        <div className="flex-1 overflow-y-auto p-6 space-y-6">
          {chatHistory.length === 0 ? (
            <div className="h-full flex flex-col items-center justify-center text-center max-w-md mx-auto space-y-4 text-slate-500">
              <Bot className="w-12 h-12 text-slate-700 animate-bounce" />
              <div>
                <h3 className="text-sm font-semibold text-slate-300">
                  DataGuardian AI Assistant
                </h3>
                <p className="text-xs text-slate-500 mt-1">
                  Select a trigger scenario from the sidebar or enter a prompt below.
                </p>
              </div>
            </div>
          ) : (
            chatHistory.map((msg, idx) => (
              <div key={msg._id || idx} className="max-w-4xl mx-auto space-y-3">
                {msg.role === "user" && (
                  <div className="flex justify-end">
                    <div className="bg-sky-600 text-white font-medium px-5 py-3 rounded-2xl rounded-tr-none text-sm shadow-md max-w-lg">
                      {msg.content}
                    </div>
                  </div>
                )}

                {msg.role === "error" && (
                  <div className="p-4 bg-rose-500/10 border border-rose-500/30 rounded-xl text-rose-400 text-xs flex items-center gap-2">
                    <XCircle className="w-4 h-4 flex-shrink-0" />
                    <span>{msg.content}</span>
                  </div>
                )}

                {msg.role === "assistant" && <ExecutionTrace message={msg} />}
              </div>
            ))
          )}

          {loading && (
            <div className="max-w-4xl mx-auto flex items-center gap-3 text-slate-400 text-xs p-4 bg-slate-900/60 rounded-xl border border-slate-800/80 w-fit glass-card">
              <div className="w-4 h-4 border-2 border-sky-400 border-t-transparent rounded-full animate-spin"></div>
              Orchestrating agents across DataHub graph...
            </div>
          )}
          <div ref={chatEndRef} />
        </div>

        <div className="p-5 border-t border-slate-800/80 bg-slate-900/40 glass-panel flex-shrink-0">
          <form
            onSubmit={(e) => {
              e.preventDefault();
              handleSend();
            }}
            className="flex gap-3 max-w-4xl mx-auto"
          >
            <input
              type="text"
              value={prompt}
              onChange={(e) => setPrompt(e.target.value)}
              placeholder="Ask DataGuardian AI (e.g., 'What is the impact if I remove customer_age?')"
              className="flex-1 bg-slate-950 border border-slate-800 rounded-xl px-5 py-3.5 text-sm text-slate-100 focus:outline-none focus:border-sky-500 transition placeholder:text-slate-600"
            />
            <button
              type="submit"
              disabled={loading || !prompt.trim()}
              className="px-6 py-3.5 bg-sky-500 hover:bg-sky-400 disabled:opacity-40 text-slate-950 font-semibold rounded-xl text-sm transition flex items-center gap-2 cursor-pointer"
            >
              <span>Execute</span>
              <Send className="w-4 h-4" />
            </button>
          </form>
        </div>
      </main>
    </div>
  );
}