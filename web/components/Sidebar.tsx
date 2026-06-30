"use client";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { useEffect, useState } from "react";
import { getName } from "@/lib/onboarding-store";

const NAV: { href: string; label: string }[] = [
  { href: "/home", label: "home" },
  { href: "/compose", label: "write" },
  { href: "/feed", label: "posts" },
  { href: "/profile", label: "voice profile" },
];

export function Sidebar() {
  const pathname = usePathname();
  const [name, setName] = useState("");
  useEffect(() => setName(getName() || "you"), []);
  const initial = (name || "y").trim().charAt(0).toUpperCase();

  return (
    <aside
      className="shrink-0 w-[230px] min-h-screen border-r flex flex-col gap-1 p-5"
      style={{ borderColor: "var(--border)" }}
    >
      <Link href="/home" className="brand mb-7 px-2">
        <span className="word">
          timbre<span className="dot">.</span>
        </span>
      </Link>

      <nav className="flex flex-col gap-1">
        {NAV.map((n) => {
          const active = pathname === n.href;
          return (
            <Link
              key={n.href}
              href={n.href}
              className="px-3 py-2.5 rounded-xl text-[14px] font-medium transition-colors"
              style={{
                background: active ? "var(--card)" : "transparent",
                color: active ? "var(--ink)" : "var(--muted)",
                border: `1px solid ${active ? "var(--border)" : "transparent"}`,
              }}
            >
              {n.label}
            </Link>
          );
        })}
      </nav>

      <div className="mt-auto flex items-center gap-3 px-2 pt-4">
        <span
          className="grid place-items-center w-9 h-9 rounded-full font-bold text-[13px]"
          style={{
            background: "linear-gradient(135deg,#FFE500,#FFB200)",
            color: "#0B0B0C",
            fontFamily: "var(--display)",
          }}
        >
          {initial}
        </span>
        <span className="leading-tight">
          <span className="block text-[13.5px] font-semibold">{name}</span>
          <span className="block text-[11px]" style={{ color: "var(--dim)" }}>
            tuned · local-first
          </span>
        </span>
      </div>
    </aside>
  );
}
