# S8(a) DESIGN: LEVEL 4, THE FLEET IS AN ECONOMY

Status: DESIGN, Sat 2026-11-14 (Sunday program). Research lane
only; no allocation, strategy or sizing change is made by this
file. Inputs of record: runs/attribution_ledger_v1.json (339
sleeves), the desk dispatcher journal (the full dispatcher record
cited in the execution board evidence: 65,203 rows, 5 generations,
window 2026-11-02 to 2026-11-13, per
research_notes/sleeve-activation-calibration-20261111/execution_board.csv
evidence_detail), and that execution board CSV itself (340 lines:
339 sleeves plus header). Deep Dive Two section 1 is folded in by
name; where it binds, it governs.

## 0. Design rule 1 (binding, Deep Dive Two section 1.1)

Allocation, promotion and killing must be computable from a table
by a script. Any allocation decision requiring a narrative is, by
the Scharfstein and Stein rent-seeking mechanism, predicted to
drift toward the weak (allocation "socialism": the strong
subsidise the weak because the weak lobby hardest). Every spec
below therefore names its formula and its inputs. There is no
discretionary step in any of the three instruments. A human may
change a FORMULA, in writing, with a falsifier; a human may not
override an OUTPUT.

## 1. The nightly GDP line

Definition: GDP_t = graded expectancy per unit of drawdown,
published nightly, computed by script from the attribution ledger
JSON and the execution board CSV.

Components (each a named line, each in dollars where the record
supports dollars):
- Consumption (proven compounding): sum over sleeves at verdict
  grade (at least 3 own closes AND no NETTED flag) of
  realized_usd. Formula: C = sum(realized_usd | own_closes >= 3
  and NETTED not in flags). Today: C = 0 dollars, because the
  clean verdict-grade count is 0 (ATTRIBUTION-LEDGER-V1.md). The
  provisional, flagged subtotal is printed beside it, never inside
  it: 5,489.35 (aster_trader_donchian55) + 661.36
  (bta_onebar_rth) - 300.49 (bta_onebar_qqq, 2 closes, below bar)
  = 5,850.22 dollars realized across the only 3 sleeves with any
  own closes.
- Investment (candidates in forward test): count and paper capital
  assigned to sleeves in LOW SAMPLE klass with fills above 0 and
  own_closes below the bar. Today: 62 LOW SAMPLE sleeves, all 62
  with fills (7,766 fills fleet-wide, every fill sits in this
  klass), 13 own closes among 3 of them.
- Waste (idle-capital drag, in dollars): W = (number of sleeves in
  NOT FIRED plus PARKED klass) x (fleet paper capital / 339) x
  (SPY return over the sleeve's sessions window). The per-sleeve
  capital term uses the board's uniform paper allocation until a
  per-sleeve capital field exists; the SPY window return is the
  same Lens T excess basis the ledger already carries
  (excess_vs_spy_usd is computed per sleeve). Today: 223 NOT FIRED
  plus 54 PARKED = 277 of 339 sleeves (81.7 percent) produce no
  closes; their summed excess_vs_spy_usd in the ledger is the
  printed drag proxy until the capital field lands. GAP NAMED:
  the ledger carries no per-sleeve allocated-capital field, so
  the dollar drag is a proxy (summed SPY-relative drift on zero
  closes), not a true opportunity-cost accounting. The fix is a
  capital column in attribution ledger v1.1, already rowed there
  for the QQQ excess leg.
- Denominator: fleet drawdown = max peak-to-trough decline of the
  summed realized_usd curve over the trailing quarter, from the
  ledger's per-sleeve realized rows joined on session. GAP NAMED:
  the v1 ledger carries no per-sleeve equity curve (rowed as a
  v1.1 item in ATTRIBUTION-LEDGER-V1.md), so until v1.1 the GDP
  line publishes its numerator components and prints the
  denominator as UNMEASURED rather than inventing a curve.

GDP publication rule: the line prints nightly even when it prints
zeros. A zero consumption line is the finding, not a failure of
the report.

## 2. The correlation tax schedule

Measured from the dispatcher journal: for each sleeve pair, fire
correlation rho_ij = correlation of the two sleeves' daily fire
indicator series (1 on a session where the sleeve emitted at
least one intent that reached the dispatcher, else 0), computed
over the trailing 60 sessions of journal rows, minimum 20 shared
sessions or the pair is UNMEASURED and taxed at the fleet median
measured rho (never at zero).

Tax formula (Deep Dive Two section 1.3, verbatim shape):
tax_i = lambda * sum over j != i of w_j * rho_ij * sigma_i * sigma_j
where w_j is sleeve j's current allocation weight, sigma is the
sleeve's realized daily P and L volatility (from the attribution
ledger once closes exist; until then, fire-count volatility from
the journal), and lambda is calibrated so that a strategy
duplicating an incumbent (rho near 1 to the fleet) must earn
about 2x the fleet hurdle to be admitted. The tax is charged in
return units against the sleeve's expectancy before allocation:
net_i = expectancy_i - tax_i. Allocation is proportional to
max(net_i, 0) subject to a hard cap per correlation cluster
(eigenvalue cluster of the rho matrix).

Hurdle dynamics: the fleet hurdle rises when fleet correlation
rises (crowding is inflation). Script rule: hurdle_t = base
hurdle x (1 + median pairwise rho_t / 0.5), floored at the base
hurdle. No meeting sets the hurdle.

Decay planning (Deep Dive Two section 1.2, McLean and Pontiff
haircuts, binding): a new strategy is budgeted at 0.42x its paper
Sharpe if it belongs to a published family, 0.74x if genuinely
private and pre-registered before any tuning, and 0x until its
DSR exceeds 0.95 with an honest trial count (every variant anyone
looked at, including discarded ones). The budgeted figure, not
the raw paper Sharpe, is what the tax and hurdle are applied to.

Death rules (Deep Dive Two section 1.4, evidence-based, never
drawdown-only): a sleeve dies when (a) its forward Sharpe
confidence interval excludes its haircut budget, or (b) its DSR
on forward data falls below 0.5, or (c) its mechanism is
invalidated (the borrow fee, spread, or flow regime the edge
depended on has changed). Drawdown alone kills nothing in this
design; drawdown-only kills systematically kill mean-reverting
sleeves at their point of maximum expected return.

## 3. The exploration subsidy ledger

Rule: every sleeve younger than its pre-registered half-life, or
in forward test with fewer than 30 own closes, receives
subsidized paper capital from a named subsidy pool, recorded as
a ledger with four columns per sleeve: subsidy start date,
sunset date (birth date plus the pre-registered half-life,
printed at birth, never extended by narrative; an extension is a
formula change and needs its own falsifier), cumulative subsidy
in paper dollars, and closes accrued under subsidy. At sunset
the sleeve faces the unsubsidised hurdle and tax with whatever
record it accrued. Resurrection of a dead sleeve is forbidden
(Deep Dive Two section 1.1: resurrection is cross-subsidisation);
a genuinely new hypothesis is a new birth with a new trial count.

## 4. The health dashboard (Deep Dive Two section 1.3, seven metrics)

Computed weekly by script, published with the GDP line:
1. N_eff = (sum lambda_k)^2 / sum lambda_k^2 over the eigenvalues
   of the sleeve return (interim: fire) correlation matrix, plus
   the largest eigenvalue share.
2. Diversification ratio: fleet realised vol divided by the sum
   of stand-alone vols.
3. Median pairwise correlation AND tail correlation on
   worst-decile fleet days.
4. Birth rate, death rate, median age at death, percent of
   capital in sleeves past their pre-registered half-life.
5. Aggregate DSR distribution: percent of live capital with
   DSR below 0.95. Target 0 by construction.
6. Turnover-weighted spread cost as a percent of gross P and L.
7. Allocation Gini versus return Gini: if capital is more equal
   than opportunity, the fleet is running Scharfstein and Stein
   socialism, measured, not alleged.
Today's computability: metrics 4 (partially; see
DEMOGRAPHY-SNAPSHOT-1) is computable; 1 to 3 and 6 need the
per-sleeve daily series the v1.1 ledger rows; 5 needs trial
counts the fleet does not yet log honestly; 7 needs the capital
field. Each unmeasured metric prints UNMEASURED with its missing
input named. That is the design working, not failing.

## 5. Falsifiers

Ascension Level 4 falsifier, verbatim: "Falsifier: an
economy-governed allocator fails to beat the plain equal-vol
allocator on forward R over two quarters. If policy adds nothing,
we go back to being a portfolio."

Deep Dive Two section 1 falsifiable forward test, carried:
pre-register the next 100 paper strategies (in-sample Sharpe,
trial count, family, publication status). Prediction: forward
Sharpe averages at most 0.5x in-sample for published families,
and the DSR at least 0.95 subset outperforms the DSR below 0.95
subset forward. If the DSR subset does not outperform, the trial
accounting is dishonest (unlogged trials); that itself is the
finding. Dashboard kill criterion from the dive: if N_eff does
not predict next-month fleet drawdown depth better than raw
strategy count over 12 months, drop it.

STATUS: PARTIAL for S8(a) as scoped (buildable spec complete;
GDP denominator, per-sleeve capital, DSR trial counts and daily
series are named v1.1 gaps, not computed). EVIDENCE: this file;
attribution_ledger_v1.json; execution_board.csv.
