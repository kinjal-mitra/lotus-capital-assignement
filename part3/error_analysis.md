## Faulty Spec 1: RiskManager

### Issues
- `optimal_kelly_fraction` is undefined
- No formula provided

### Why Rejected
- Cannot compute deterministically

### Questions
- What is the mathematical definition of optimal_kelly_fraction?

---

## Faulty Spec 2: PortfolioBuilder

### Issues
- "use best judgment" is subjective

### Why Rejected
- No deterministic algorithm

### Questions
- What objective function or rule should be applied?

---

## Faulty Spec 3: ExecutionEngine

### Issues
- "market is favorable" undefined
- "minimize as much as possible" non-quantifiable

### Why Rejected
- Cannot translate to code

### Questions
- What indicators define favorability?
- What is the slippage formula?
