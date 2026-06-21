"use client";

import { useEffect, useState } from "react";
import { Wordmark } from "./brand/Logo";
import { LiveBadge } from "./ui/Pill";

const NAV = [
  { href: "#champion", label: "Champion" },
  { href: "#evolution", label: "Evolution" },
  { href: "#sentiment", label: "Sentiment" },
  { href: "#onchain", label: "On-chain" },
];

const GITHUB = "https://github.com/coderansari/darwin";

export function Header({ live }: { live: boolean }) {
  const [scrolled, setScrolled] = useState(false);
  const [open, setOpen] = useState(false);

  useEffect(() => {
    const onScroll = () => setScrolled(window.scrollY > 12);
    onScroll();
    window.addEventListener("scroll", onScroll, { passive: true });
    return () => window.removeEventListener("scroll", onScroll);
  }, []);

  return (
    <header
      className={`fixed inset-x-0 top-0 z-50 transition-all duration-300 ${
        scrolled ? "border-b border-white/[0.06] bg-ink-950/70 backdrop-blur-xl" : "border-b border-transparent"
      }`}
    >
      <div className="mx-auto flex h-16 max-w-6xl items-center justify-between px-5 sm:px-8">
        <a href="#top" className="shrink-0" aria-label="Darwin home">
          <Wordmark size={30} />
        </a>

        <nav className="hidden items-center gap-1 md:flex">
          {NAV.map((n) => (
            <a
              key={n.href}
              href={n.href}
              className="rounded-full px-3.5 py-2 text-sm text-zinc-400 transition-colors hover:text-white"
            >
              {n.label}
            </a>
          ))}
        </nav>

        <div className="hidden items-center gap-3 md:flex">
          {live && <LiveBadge />}
          <a
            href={GITHUB}
            target="_blank"
            rel="noreferrer"
            className="rounded-full border border-white/10 bg-white/[0.04] px-4 py-2 text-sm font-medium text-white transition-colors hover:border-gold/40 hover:bg-white/[0.07]"
          >
            GitHub
          </a>
        </div>

        {/* mobile toggle */}
        <button
          onClick={() => setOpen((v) => !v)}
          className="flex h-10 w-10 items-center justify-center rounded-full border border-white/10 bg-white/[0.04] md:hidden"
          aria-label="Toggle menu"
          aria-expanded={open}
        >
          <div className="relative h-4 w-5">
            <span className={`absolute left-0 top-0 h-0.5 w-5 bg-white transition-all ${open ? "top-1.5 rotate-45" : ""}`} />
            <span className={`absolute left-0 top-1.5 h-0.5 w-5 bg-white transition-all ${open ? "opacity-0" : ""}`} />
            <span className={`absolute left-0 top-3 h-0.5 w-5 bg-white transition-all ${open ? "top-1.5 -rotate-45" : ""}`} />
          </div>
        </button>
      </div>

      {/* mobile sheet */}
      <div
        className={`overflow-hidden border-t border-white/[0.06] bg-ink-950/95 backdrop-blur-xl transition-all duration-300 md:hidden ${
          open ? "max-h-80" : "max-h-0"
        }`}
      >
        <nav className="flex flex-col gap-1 px-5 py-4">
          {NAV.map((n) => (
            <a
              key={n.href}
              href={n.href}
              onClick={() => setOpen(false)}
              className="rounded-xl px-3 py-3 text-base text-zinc-300 transition-colors hover:bg-white/[0.05] hover:text-white"
            >
              {n.label}
            </a>
          ))}
          <div className="mt-2 flex items-center justify-between px-3">
            {live && <LiveBadge />}
            <a href={GITHUB} target="_blank" rel="noreferrer" className="text-sm font-medium text-gold">
              GitHub →
            </a>
          </div>
        </nav>
      </div>
    </header>
  );
}
