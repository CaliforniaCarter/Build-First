export default function OnboardingLayout({ children }: { children: React.ReactNode }) {
  return (
    <div
      className="min-h-screen flex flex-col"
      style={{
        backgroundImage:
          "radial-gradient(1200px 500px at 80% -10%, rgba(255,229,0,.07), transparent 60%)",
      }}
    >
      {children}
    </div>
  );
}
