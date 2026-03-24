import Image from "next/image";

export default function AuthLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <div className="min-h-screen grid lg:grid-cols-2">
      {/* Left: Brand panel */}
      <div className="hidden lg:flex flex-col bg-primary px-12 py-10 text-primary-foreground relative overflow-hidden">
        {/* Background decoration */}
        <div className="absolute inset-0 opacity-10">
          <div className="absolute top-0 left-0 w-96 h-96 rounded-full bg-white translate-x-[-50%] translate-y-[-30%]" />
          <div className="absolute bottom-0 right-0 w-80 h-80 rounded-full bg-white translate-x-[40%] translate-y-[30%]" />
          <div className="absolute top-1/2 left-1/3 w-64 h-64 rounded-full bg-white opacity-50" />
        </div>

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
          <p className="text-primary-foreground/75 text-base leading-relaxed max-w-sm">
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
            <div key={feature} className="flex items-center gap-3 text-sm text-primary-foreground/80">
              <div className="h-1.5 w-1.5 rounded-full bg-primary-foreground/60 shrink-0" />
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
