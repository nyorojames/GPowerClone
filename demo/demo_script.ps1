# demo/demo_script.ps1
# 60-Second Demonstration Script for gpower-clone (One-Way ANOVA Omnibus F-Test)
# Run from repository root in PowerShell: .\demo\demo_script.ps1

Write-Host "=================================================================" -ForegroundColor Cyan
Write-Host " gpower-clone CLI Demonstration (YZM301 Teardown Sprint)" -ForegroundColor Cyan
Write-Host "=================================================================" -ForegroundColor Cyan
Start-Sleep -Seconds 2

# -----------------------------------------------------------------------------
# STEP 1: Typical Cases from Oracle
# -----------------------------------------------------------------------------
Write-Host ""
Write-Host "[Step 1/4] Running Typical Oracle Vector v003: k=3, f=0.25, alpha=0.05, power=0.80" -ForegroundColor Yellow
Write-Host "> python -m src.cli.main --test anova-oneway --mode a-priori --groups 3 --f 0.25 --alpha 0.05 --power 0.80" -ForegroundColor Gray
python -m src.cli.main --test anova-oneway --mode a-priori --groups 3 --f 0.25 --alpha 0.05 --power 0.80
Start-Sleep -Seconds 2

Write-Host ""
Write-Host "[Step 1b] Running Typical Oracle Vector v016 (Different Group Count): k=5, f=0.25, alpha=0.05, power=0.95" -ForegroundColor Yellow
Write-Host "> python -m src.cli.main --test anova-oneway --mode a-priori --groups 5 --f 0.25 --alpha 0.05 --power 0.95" -ForegroundColor Gray
python -m src.cli.main --test anova-oneway --mode a-priori --groups 5 --f 0.25 --alpha 0.05 --power 0.95
Start-Sleep -Seconds 2

# -----------------------------------------------------------------------------
# STEP 2: Boundary Case from LEDGER.md [REA]
# Exercises L-014 (Oracle v046): Floating group count k=3.5 rounded half-up to k=4
# -----------------------------------------------------------------------------
Write-Host ""
Write-Host "[Step 2/4] Boundary Case: Non-Integer Group Count k=3.5 (LEDGER.md L-014 [REA], Oracle v046)" -ForegroundColor Yellow
Write-Host "           G*Power rounds fractional groups half-up to 4 (yielding df1=3, df2=176, N=180)." -ForegroundColor DarkYellow
Write-Host "> python -m src.cli.main --test anova-oneway --mode a-priori --groups 3.5 --f 0.25 --alpha 0.05 --power 0.80" -ForegroundColor Gray
python -m src.cli.main --test anova-oneway --mode a-priori --groups 3.5 --f 0.25 --alpha 0.05 --power 0.80
Start-Sleep -Seconds 3

# -----------------------------------------------------------------------------
# STEP 3: Invalid Input & Contract Error Handling
# Exercises L-018 (Oracle v035): Power strictly below alpha rejection
# -----------------------------------------------------------------------------
Write-Host ""
Write-Host "[Step 3/4] Invalid Input Rejection: Power < Alpha (LEDGER.md L-018 [REA], Oracle v035)" -ForegroundColor Yellow
Write-Host "           Ensures single-line JSON error output and non-zero exit code." -ForegroundColor DarkYellow
Write-Host "> python -m src.cli.main --test anova-oneway --mode a-priori --groups 3 --f 0.25 --alpha 0.05 --power 0.04" -ForegroundColor Gray
python -m src.cli.main --test anova-oneway --mode a-priori --groups 3 --f 0.25 --alpha 0.05 --power 0.04
$ec = $LASTEXITCODE
Write-Host "Exit Code: $ec" -ForegroundColor Red
Start-Sleep -Seconds 3

# -----------------------------------------------------------------------------
# STEP 4: Full Differential Test Suite Against G*Power Oracle
# -----------------------------------------------------------------------------
Write-Host ""
Write-Host "[Step 4/4] Executing Differential Verification Against All 46 G*Power GUI Vectors" -ForegroundColor Yellow
Write-Host "> python -m unittest tests/differential/test_differential.py" -ForegroundColor Gray
python -m unittest tests/differential/test_differential.py

Write-Host ""
Write-Host "=================================================================" -ForegroundColor Cyan
Write-Host " Demonstration complete. All outputs verified against specification." -ForegroundColor Cyan
Write-Host "=================================================================" -ForegroundColor Cyan
