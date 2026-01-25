"use client";

import ClientDashboard from "@/components/ClientDashboard";
import ManagerControlBar from "@/components/ManagerControlBar";
import Image from "next/image";

export default function DemoPage() {
  // Pre-select ACME Corporation as default demo client
  const defaultClientId = "acme-corp";
  
  // Demo client list (same as Manager page)
  const demoClients = [
    { id: "acme-corp", name: "ACME Corporation", riskTolerance: "Medium" },
    { id: "global-fund", name: "Global Growth Fund", riskTolerance: "High" },
    { id: "conservative-trust", name: "Conservative Trust", riskTolerance: "Low" },
    { id: "sovereign-wealth", name: "Sovereign Wealth Fund Alpha", riskTolerance: "Medium" },
    { id: "pension-fund-beta", name: "Pension Fund Beta", riskTolerance: "Low" },
    { id: "hedge-fund-gamma", name: "Hedge Fund Gamma", riskTolerance: "High" },
  ];

  return (
    <div className="relative min-h-screen overflow-hidden bg-gradient-to-br from-slate-900 via-black to-slate-900">
      {/* Header */}
      <header className="pointer-events-none relative z-10 flex items-start justify-between px-10 pt-8">
        <div className="pointer-events-auto flex items-center gap-3">
          <Image
            src="/mandala_logo.png"
            alt="Mandala"
            width={40}
            height={40}
            className="h-10 w-10 rounded-2xl object-contain"
            priority
          />
          <div className="flex flex-col gap-0.5">
            <p className="text-base font-semibold uppercase tracking-[0.38em] text-white/85">
              Mandala
            </p>
            <p className="text-sm font-[var(--font-display)] text-white/75">
              Demo
            </p>
          </div>
        </div>
        <div className="pointer-events-auto">
          <ManagerControlBar />
        </div>
      </header>

      {/* Client Dashboard - Demo mode with asset search */}
      <ClientDashboard
        clients={demoClients}
        selectedClientId={defaultClientId}
        onClientChange={() => {}} // No-op since we don't want to change client in demo
        hideClientSelector={true}
        demoMode={true}
      />
    </div>
  );
}
