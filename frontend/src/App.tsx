import React, { useState } from 'react';
import { useAuth } from './context/AuthContext';
import { Navbar } from './components/layout/Navbar';
import { AuthModal } from './components/auth/AuthModal';
import { DashboardView } from './components/dashboard/DashboardView';
import { LeadsView } from './components/leads/LeadsView';
import { DiscoveryView } from './components/discovery/DiscoveryView';
import { ImportExportView } from './components/imports/ImportExportView';
import { SuppressionView } from './components/suppression/SuppressionView';
import { SettingsView } from './components/settings/SettingsView';
import { NewLeadModal } from './components/leads/NewLeadModal';

export const App: React.FC = () => {
  const { user, isLoading } = useAuth();
  const [currentTab, setCurrentTab] = useState<string>('dashboard');
  const [isNewLeadOpen, setIsNewLeadOpen] = useState(false);

  if (isLoading) {
    return (
      <div className="flex items-center justify-center min-h-screen bg-slate-50">
        <div className="text-center space-y-3">
          <div className="animate-spin rounded-full h-10 w-10 border-b-2 border-brand-700 mx-auto"></div>
          <p className="text-xs text-slate-500 font-medium">Initializing LeadGen Lite...</p>
        </div>
      </div>
    );
  }

  if (!user) {
    return <AuthModal />;
  }

  return (
    <div className="min-h-screen bg-slate-50 flex flex-col font-sans">
      {/* Top Navigation */}
      <Navbar
        currentTab={currentTab}
        setCurrentTab={setCurrentTab}
        onOpenNewLead={() => setIsNewLeadOpen(true)}
      />

      {/* Main Content Area */}
      <main className="flex-1 max-w-7xl w-full mx-auto px-4 sm:px-6 lg:px-8 py-6">
        {currentTab === 'dashboard' && <DashboardView onNavigate={(tab) => setCurrentTab(tab)} />}
        {currentTab === 'leads' && <LeadsView />}
        {currentTab === 'discovery' && <DiscoveryView onNavigateToLeads={() => setCurrentTab('leads')} />}
        {currentTab === 'import-export' && <ImportExportView />}
        {currentTab === 'suppression' && <SuppressionView />}
        {currentTab === 'settings' && <SettingsView />}
      </main>

      {/* New Lead Modal */}
      <NewLeadModal
        isOpen={isNewLeadOpen}
        onClose={() => setIsNewLeadOpen(false)}
        onLeadCreated={() => {
          setIsNewLeadOpen(false);
          setCurrentTab('leads');
        }}
      />
    </div>
  );
};

export default App;
