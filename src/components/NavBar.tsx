"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";

export default function NavBar() {
  const pathname = usePathname();
  const isDesk = pathname === "/" || pathname === "/desk";
  const isManager = pathname === "/manager";
  const isDemo = pathname === "/demo";

  return (
    <nav className="pointer-events-none absolute left-1/2 top-8 z-50 -translate-x-1/2">
      <div className="pointer-events-auto flex items-center gap-1 rounded-full border border-white/20 bg-black/40 px-2 py-1.5 backdrop-blur">
        <Link
          href="/desk"
          className={`rounded-full px-4 py-1.5 text-sm font-medium transition ${
            isDesk
              ? "bg-white/15 text-white"
              : "text-white/70 hover:bg-white/10 hover:text-white"
          }`}
        >
          Desk
        </Link>
        <Link
          href="/manager"
          className={`rounded-full px-4 py-1.5 text-sm font-medium transition ${
            isManager
              ? "bg-white/15 text-white"
              : "text-white/70 hover:bg-white/10 hover:text-white"
          }`}
        >
          Manager
        </Link>
        <Link
          href="/demo"
          className={`rounded-full px-4 py-1.5 text-sm font-medium transition ${
            isDemo
              ? "bg-white/15 text-white"
              : "text-white/70 hover:bg-white/10 hover:text-white"
          }`}
        >
          Demo
        </Link>
      </div>
    </nav>
  );
}
