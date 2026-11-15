import { useMemo, useState } from 'react';
import { AlertsList } from './components/AlertsList';
import { BillsTable } from './components/BillsTable';
import { ConnectCard } from './components/ConnectCard';
import { ScanningCard } from './components/ScanningCard';
import { SummaryStrip } from './components/SummaryStrip';
import { fetchAuditReport } from './services/api';
import { exportAuditToCsv } from './services/csv';
import {
  requestGmailToken,
  requestOutlookToken,
  revokeGmailToken,
} from './services/oauth';

export function App() {
  const [view, setView] = useState('connect'); // 'connect' | 'scanning' | 'report'
  const [audit, setAudit] = useState(null);
  const [selectedIds, setSelectedIds] = useState(new Set());
  const [activeToken, setActiveToken] = useState(null);
  const [errorMessage, setErrorMessage] = useState(null);

  async function startAudit(provider, token) {
    setErrorMessage(null);
    setView('scanning');
    try {
      const report = await fetchAuditReport(provider, token);
      const defaultChecked = new Set(
        report.items
          .filter((item) => item.default_selected || item.flags.length > 0)
          .map((item) => item.id)
      );
      setAudit(report);
      setSelectedIds(defaultChecked);
      setView('report');
    } catch (err) {
      const message =
        err instanceof Error ? err.message : 'Something went wrong during scan.';
      setErrorMessage(message);
      setView('connect');
    }
  }

  async function handleConnectGmail() {
    setErrorMessage(null);
    try {
      const token = await requestGmailToken();
      setActiveToken(token);
      await startAudit('gmail', token);
    } catch (err) {
      setErrorMessage(
        err instanceof Error ? err.message : 'Failed to connect Gmail.'
      );
    }
  }

  async function handleConnectOutlook() {
    setErrorMessage(null);
    try {
      const token = await requestOutlookToken();
      setActiveToken(token);
      await startAudit('outlook', token);
    } catch (err) {
      setErrorMessage(
        err instanceof Error ? err.message : 'Failed to connect Outlook.'
      );
    }
  }

  function handleToggleItem(id) {
    setSelectedIds((prev) => {
      const next = new Set(prev);
      if (next.has(id)) {
        next.delete(id);
      } else {
        next.add(id);
      }
      return next;
    });
  }

  function handleClearSession() {
    revokeGmailToken(activeToken);
    setActiveToken(null);
    setAudit(null);
    setSelectedIds(new Set());
    setErrorMessage(null);
    setView('connect');
  }

  const selectedMonthlySavings = useMemo(() => {
    if (!audit) return 0;
    return audit.items
      .filter((item) => selectedIds.has(item.id))
      .reduce((sum, item) => sum + item.monthly_equivalent, 0);
  }, [audit, selectedIds]);

  return (
    <main className="page-shell">
      {view === 'connect' && (
        <ConnectCard
          onConnectGmail={handleConnectGmail}
          onConnectOutlook={handleConnectOutlook}
          onRunSample={() => startAudit('mock')}
          errorMessage={errorMessage}
        />
      )}

      {view === 'scanning' && <ScanningCard />}

      {view === 'report' && audit && (
        <div className="report-stack">
          <header className="report-topbar">
            <div>
              <h1 className="report-brand">LockIn</h1>
              <span className="report-meta">
                Scanned {audit.scanned_emails_count} billing emails (in memory)
              </span>
            </div>
            <div className="topbar-actions">
              <button
                type="button"
                className="btn btn-secondary btn-sm"
                onClick={() => exportAuditToCsv(audit, selectedIds)}
              >
                Export CSV
              </button>
              <button
                type="button"
                className="btn btn-ghost btn-sm"
                onClick={handleClearSession}
              >
                Clear
              </button>
            </div>
          </header>

          <SummaryStrip
            totalMonthlyRecurring={audit.total_monthly_recurring}
            totalAnnualRecurring={audit.total_annual_recurring}
            selectedMonthlySavings={selectedMonthlySavings}
            selectedCount={selectedIds.size}
            annualReturnRate={audit.annual_return_rate}
          />

          <AlertsList alerts={audit.alerts} />

          <BillsTable
            items={audit.items}
            selectedIds={selectedIds}
            onToggleItem={handleToggleItem}
          />

          <footer className="report-footer">
            Zero-storage session · Closing this tab or clicking Clear discards
            all results ·{' '}
            <a href="/privacy.html" className="subtle-link">
              Privacy
            </a>
          </footer>
        </div>
      )}
    </main>
  );
}

