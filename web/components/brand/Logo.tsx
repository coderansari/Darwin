/**
 * Darwin brand mark — the DNA-helix-that-becomes-a-rising-chart logo.
 * `size` is the rendered height in px; width follows the mark's aspect ratio.
 */
const ASPECT = 0.434; // width / height of /public/logo.png

export function Logo({ size = 32, className = "" }: { size?: number; className?: string }) {
  return (
    // eslint-disable-next-line @next/next/no-img-element
    <img
      src="/logo.png"
      alt="Darwin"
      width={Math.round(size * ASPECT)}
      height={size}
      className={className}
      style={{ height: size, width: "auto" }}
    />
  );
}

export function Wordmark({ size = 30, className = "" }: { size?: number; className?: string }) {
  return (
    <span className={`flex items-center gap-2.5 ${className}`}>
      <Logo size={size} />
      <span className="text-[1.15rem] font-semibold tracking-tight text-white">Darwin</span>
    </span>
  );
}
