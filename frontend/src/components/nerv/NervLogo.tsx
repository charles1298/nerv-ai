import Link from "next/link";

export function NervLogo({ withText = true, href = "/dashboard" }: { withText?: boolean; href?: string }) {
  return (
    <Link href={href} className="focus-nice group flex shrink-0 items-center gap-2 rounded-full">
      <span className="relative grid size-9 place-items-center">
        <span className="absolute inset-0 animate-pulse-glow rounded-full bg-primary/25 blur-md" />
        {/* eslint-disable-next-line @next/next/no-img-element */}
        <img
          src="/nerv-mark.png"
          alt="NERV.AI"
          width={512}
          height={512}
          className="relative size-8 transition-transform duration-500 group-hover:rotate-12"
        />
      </span>
      {withText ? (
        <span className="font-display text-lg font-bold tracking-tight">
          NERV<span className="text-gradient">.AI</span>
        </span>
      ) : null}
    </Link>
  );
}
