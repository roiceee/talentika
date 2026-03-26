import Image from "next/image";

export default function AuthLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <div className="min-h-screen grid lg:grid-cols-2">
      {/* Left: Brand panel */}
      <div className="hidden lg:flex flex-col px-12 py-10 text-white relative overflow-hidden">
        {/* Background image */}
        <Image
          src="/auth-bg.svg"
          alt=""
          fill
          className="object-cover"
          priority
          unoptimized
        />
        {/* Overlay for readability */}
        <div className="absolute inset-0 bg-black/30" />

        {/* Logo */}
        <div className="relative flex items-center gap-3">
          <Image src="/icon.png" alt="Talentika" width={36} height={36} priority />
          <span className="font-heading text-xl text-white">Talentika</span>
        </div>

        {/* Tagline */}
        <div className="relative mt-auto mb-12">
          <h2 className="font-heading text-3xl text-white leading-snug mb-4">
            AI-powered talent<br />management
          </h2>
          <p className="text-white/75 text-base leading-relaxed max-w-sm">
            Screen, analyze, and shortlist candidates faster with intelligent resume parsing and scoring.
          </p>
        </div>

        {/* Feature list */}
        <div className="relative flex flex-col gap-3 mb-8">
          {[
            "Automated resume screening",
            "AI-driven candidate scoring",
            "Smart application tracking",
          ].map((feature) => (
            <div key={feature} className="flex items-center gap-3 text-sm text-white/80">
              <div className="h-1.5 w-1.5 rounded-full bg-white/60 shrink-0" />
              {feature}
            </div>
          ))}
        </div>
      </div>

      {/* Right: Form panel */}
      <div className="flex flex-col items-center justify-center px-6 py-10 bg-background">
        <div className="w-full max-w-md">
          {/* Mobile logo */}
          <div className="flex items-center justify-center gap-2 mb-8 lg:hidden">
            <Image src="/icon.png" alt="Talentika" width={32} height={32} priority />
            <span className="font-heading text-lg text-foreground">Talentika</span>
          </div>
          {children}
        </div>
      </div>
    </div>
  );
}
