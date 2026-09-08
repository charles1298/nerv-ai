// Fundo ambiente fixo: brilho + textura. Puramente decorativo.

export function Ambient() {
  return (
    <div aria-hidden className="pointer-events-none fixed inset-0 -z-10 overflow-hidden">
      {/* eslint-disable-next-line @next/next/no-img-element */}
      <img
        src="/hero-glow.jpg"
        alt=""
        width={1920}
        height={1088}
        className="absolute inset-0 size-full object-cover opacity-70"
      />
      <div className="absolute left-1/2 top-[-18rem] size-[42rem] -translate-x-1/2 animate-pulse-glow rounded-full bg-primary/10 blur-[120px]" />
      <div className="absolute inset-0 bg-background/40" />
    </div>
  );
}
