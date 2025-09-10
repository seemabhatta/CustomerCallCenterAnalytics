export function DensityToggle() {
  const setDensity = (mode: 'compact' | 'cozy') => {
    document.documentElement.setAttribute('data-density', mode);
  };

  return (
    <div className="flex items-center gap-2 text-sm">
      <button 
        className="h-8 px-3 rounded-xl border border-border text-muted-foreground hover:bg-accent transition-colors" 
        onClick={() => setDensity('compact')}
      >
        Compact
      </button>
      <button 
        className="h-8 px-3 rounded-xl border border-border text-muted-foreground hover:bg-accent transition-colors" 
        onClick={() => setDensity('cozy')}
      >
        Cozy
      </button>
    </div>
  );
}