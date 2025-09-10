export default function ActionPlansPage() {
  return (
    <div className="p-6 max-w-screen-2xl mx-auto space-y-6">
      <div className="flex items-start justify-between">
        <div>
          <h1 className="text-2xl font-semibold">Action Plans</h1>
          <p className="text-sm text-muted-foreground">
            Steps 3-4: Decision Agent generates comprehensive action plans
          </p>
        </div>
      </div>

      <div className="rounded-2xl border border-border p-8 text-center bg-card">
        <div className="text-6xl mb-4">⚪</div>
        <h2 className="text-xl font-semibold mb-2">Decision Agent</h2>
        <p className="text-muted-foreground mb-6 max-w-md mx-auto">
          AI generates comprehensive 4-layer action plans for mortgage servicing scenarios
          with intelligent routing based on risk and complexity.
        </p>
        <div className="grid grid-cols-2 gap-4 max-w-lg mx-auto text-sm text-muted-foreground">
          <div>👤 Borrower Actions</div>
          <div>👨‍💼 Advisor Actions</div>
          <div>👨‍💼 Supervisor Actions</div>
          <div>👔 Leadership Actions</div>
        </div>
      </div>
    </div>
  );
}