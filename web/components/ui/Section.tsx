import { Reveal } from "./Reveal";

export function Section({
  id,
  eyebrow,
  title,
  intro,
  children,
  className = "",
}: {
  id?: string;
  eyebrow?: string;
  title?: string;
  intro?: string;
  children: React.ReactNode;
  className?: string;
}) {
  return (
    <section id={id} className={`relative mx-auto w-full max-w-6xl px-5 py-16 sm:px-8 sm:py-24 ${className}`}>
      {(eyebrow || title) && (
        <Reveal className="mb-10 max-w-2xl">
          {eyebrow && (
            <div className="mb-3 flex items-center gap-2.5 text-xs font-medium uppercase tracking-[0.2em] text-gold">
              <span className="h-px w-6 bg-gold/60" />
              {eyebrow}
            </div>
          )}
          {title && (
            <h2 className="text-balance text-3xl font-semibold tracking-tight text-white sm:text-4xl">
              {title}
            </h2>
          )}
          {intro && <p className="mt-4 text-base leading-relaxed text-zinc-400">{intro}</p>}
        </Reveal>
      )}
      {children}
    </section>
  );
}
