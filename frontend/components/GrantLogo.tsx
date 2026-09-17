export function GrantLogo({ size = 30 }: { size?: number }) {
  return (
    <span
      className="grid shrink-0 place-items-center rounded-lg bg-brand-600 font-black text-white shadow-sm"
      style={{ width: size, height: size, fontSize: Math.max(10, Math.round(size * 0.34)) }}
      aria-hidden
    >
      GF
    </span>
  );
}
