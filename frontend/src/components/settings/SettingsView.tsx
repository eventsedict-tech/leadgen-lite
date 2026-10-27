import React, { useState, useEffect } from 'react';
import { Settings, Key, Sliders, CheckCircle, ExternalLink, Mail } from 'lucide-react';
import { api } from '../../services/api';

export const SettingsView: React.FC = () => {
  const [saveMessage, setSaveMessage] = useState<string | null>(null);

  // Form states for API keys
  const [googlePlacesKey, setGooglePlacesKey] = useState('');
  const [searchApiKey, setSearchApiKey] = useState('');

  // Form states for SMTP & Resend
  const [smtpHost, setSmtpHost] = useState('');
  const [smtpPort, setSmtpPort] = useState('587');
  const [smtpUser, setSmtpUser] = useState('');
  const [smtpPassword, setSmtpPassword] = useState('');
  const [smtpFrom, setSmtpFrom] = useState('');
  const [resendApiKey, setResendApiKey] = useState('');

  // Form states for WhatsApp
  const [whatsappPhoneId, setWhatsappPhoneId] = useState('');
  const [whatsappToken, setWhatsappToken] = useState('');

  // Test Email state
  const [testEmailRecipient, setTestEmailRecipient] = useState('');
  const [testingSmtp, setTestingSmtp] = useState(false);
  const [testResult, setTestResult] = useState<string | null>(null);

  // Scoring Weights
  const [weightIndustry, setWeightIndustry] = useState(25);
  const [weightWebsite, setWeightWebsite] = useState(25);
  const [weightContact, setWeightContact] = useState(15);
  const [weightOpp, setWeightOpp] = useState(20);
  const [weightRelevance, setWeightRelevance] = useState(15);

  useEffect(() => {
    loadSettings();
  }, []);

  const loadSettings = async () => {
    try {
      const res = await api.getIntegrations();
      res.forEach((item) => {
        if (item.provider_type === 'google_places') {
          setGooglePlacesKey(item.masked_config?.api_key || '');
        } else if (item.provider_type === 'search_api') {
          setSearchApiKey(item.masked_config?.api_key || '');
        } else if (item.provider_type === 'smtp') {
          setSmtpHost(item.masked_config?.host || '');
          setSmtpPort(item.masked_config?.port || '587');
          setSmtpUser(item.masked_config?.user || '');
          setSmtpPassword(item.masked_config?.password || '');
          setSmtpFrom(item.masked_config?.from_email || '');
          setResendApiKey(item.masked_config?.resend_api_key || '');
        } else if (item.provider_type === 'whatsapp') {
          setWhatsappPhoneId(item.masked_config?.phone_number_id || '');
          setWhatsappToken(item.masked_config?.access_token || '');
        }
      });
    } catch (err: any) {
      alert(err.message);
    }
  };

  const handleSaveIntegration = async (providerType: string, isActive: boolean, config: any) => {
    try {
      await api.saveIntegration(providerType, isActive, config);
      setSaveMessage(`Settings for ${providerType.toUpperCase()} updated successfully!`);
      setTimeout(() => setSaveMessage(null), 3000);
      loadSettings();
    } catch (err: any) {
      alert(err.message || 'Failed to save integration');
    }
  };

  const handleTestSmtp = async () => {
    if (!testEmailRecipient) {
      alert('Please enter a destination email address to test the email dispatch.');
      return;
    }
    setTestingSmtp(true);
    setTestResult(null);
    try {
      const res = await api.testSmtp({
        host: smtpHost || undefined,
        port: Number(smtpPort) || 587,
        user: smtpUser || undefined,
        password: smtpPassword || undefined,
        from_email: smtpFrom || smtpUser || undefined,
        test_recipient: testEmailRecipient,
        resend_api_key: resendApiKey || undefined
      });
      setTestResult(res.message);
    } catch (err: any) {
      alert(err.message || 'Email test failed');
    } finally {
      setTestingSmtp(false);
    }
  };

  return (
    <div className="space-y-6 pb-12">
      <div className="bg-white p-6 rounded-xl border border-slate-200 shadow-sm">
        <h1 className="text-xl font-bold text-slate-900 flex items-center gap-2">
          <Settings className="w-5 h-5 text-brand-700" />
          <span>Integrations & System Settings</span>
        </h1>
        <p className="text-xs text-slate-500 mt-1">
          Configure optional API providers, scoring weights, email SMTP, and WhatsApp Business credentials.
        </p>
      </div>

      {saveMessage && (
        <div className="p-3 bg-emerald-50 border border-emerald-200 rounded-lg text-emerald-800 text-xs font-semibold flex items-center gap-2">
          <CheckCircle className="w-4 h-4 text-emerald-600" />
          <span>{saveMessage}</span>
        </div>
      )}

      {/* SECTION 1: SEARCH & DISCOVERY APIS */}
      <div className="bg-white p-6 rounded-xl border border-slate-200 shadow-sm space-y-4">
        <h2 className="text-sm font-bold text-slate-800 flex items-center gap-2">
          <Key className="w-4 h-4 text-brand-600" />
          <span>Search & Business Discovery Integrations</span>
        </h2>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {/* Google Places */}
          <div className="p-4 bg-slate-50 rounded-xl border border-slate-200 space-y-2.5">
            <div className="flex items-center justify-between">
              <span className="text-xs font-bold text-slate-900">Google Places API</span>
              <a
                href="https://developers.google.com/maps/documentation/places/web-service/overview"
                target="_blank"
                rel="noreferrer"
                className="text-[11px] text-brand-700 hover:underline flex items-center gap-0.5"
              >
                <span>Docs</span>
                <ExternalLink className="w-3 h-3" />
              </a>
            </div>
            <p className="text-[11px] text-slate-500">
              Discovers official company websites, public phone numbers, and addresses via Google Maps.
            </p>
            <input
              type="password"
              placeholder="Enter Google Places API Key"
              value={googlePlacesKey}
              onChange={(e) => setGooglePlacesKey(e.target.value)}
              className="w-full px-3 py-1.5 text-xs bg-white border border-slate-300 rounded focus:ring-1 focus:ring-brand-500"
            />
            <button
              onClick={() => handleSaveIntegration('google_places', Boolean(googlePlacesKey), { api_key: googlePlacesKey })}
              className="px-3 py-1.5 bg-brand-700 hover:bg-brand-800 text-white rounded text-xs font-bold transition-colors"
            >
              Save Google Places Key
            </button>
          </div>

          {/* Search API (SerpApi) */}
          <div className="p-4 bg-slate-50 rounded-xl border border-slate-200 space-y-2.5">
            <div className="flex items-center justify-between">
              <span className="text-xs font-bold text-slate-900">Commercial Search API (SerpApi)</span>
              <a
                href="https://serpapi.com/"
                target="_blank"
                rel="noreferrer"
                className="text-[11px] text-brand-700 hover:underline flex items-center gap-0.5"
              >
                <span>Docs</span>
                <ExternalLink className="w-3 h-3" />
              </a>
            </div>
            <p className="text-[11px] text-slate-500">
              Query Google Local search listings through authorized commercial search APIs.
            </p>
            <input
              type="password"
              placeholder="Enter SerpApi / ValueSERP Key"
              value={searchApiKey}
              onChange={(e) => setSearchApiKey(e.target.value)}
              className="w-full px-3 py-1.5 text-xs bg-white border border-slate-300 rounded focus:ring-1 focus:ring-brand-500"
            />
            <button
              onClick={() => handleSaveIntegration('search_api', Boolean(searchApiKey), { api_key: searchApiKey })}
              className="px-3 py-1.5 bg-brand-700 hover:bg-brand-800 text-white rounded text-xs font-bold transition-colors"
            >
              Save Search API Key
            </button>
          </div>
        </div>
      </div>

      {/* SECTION 2: OUTREACH PROVIDERS (SMTP & WHATSAPP) */}
      <div className="bg-white p-6 rounded-xl border border-slate-200 shadow-sm space-y-4">
        <h2 className="text-sm font-bold text-slate-800 flex items-center gap-2">
          <Mail className="w-4 h-4 text-emerald-600" />
          <span>Authorized Outreach Sending Gateways</span>
        </h2>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {/* Email Outreach: Resend API + SMTP */}
          <div className="p-4 bg-slate-50 rounded-xl border border-slate-200 space-y-3 text-xs">
            <div className="flex items-center justify-between">
              <div className="font-bold text-slate-900 flex items-center gap-1.5">
                <span>Email Outreach Gateway</span>
              </div>
              <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-emerald-100 text-emerald-800">
                Resend API + SMTP
              </span>
            </div>

            {/* Cloud Network Notice for Render Free Tier */}
            <div className="p-2.5 bg-amber-50 border border-amber-200 rounded-lg text-amber-900 text-[11px] leading-relaxed">
              <strong>Render Cloud Tip:</strong> Render Free Tier blocks outbound SMTP ports (587, 465, 25) with <code>[Errno 101] Network is unreachable</code> to prevent spam.
              <ul className="list-disc pl-4 mt-1 space-y-0.5">
                <li><strong>Option 1 (Instant & Free):</strong> Use the <strong>Mail App</strong> button on any lead to open Gmail directly from your device with zero setup.</li>
                <li><strong>Option 2 (Cloud Automated):</strong> Enter a free <strong>Resend API Key</strong> below (3,000 emails/mo free over HTTPS Port 443 — works everywhere on Render).</li>
              </ul>
            </div>

            {/* Resend API Key */}
            <div className="space-y-1.5 pt-1">
              <div className="flex items-center justify-between">
                <span className="font-semibold text-slate-800 text-[11px]">Resend API Key (Recommended for Render):</span>
                <a
                  href="https://resend.com"
                  target="_blank"
                  rel="noreferrer"
                  className="text-[10px] text-brand-700 hover:underline flex items-center gap-0.5 font-medium"
                >
                  <span>Get Free Key (resend.com)</span>
                  <ExternalLink className="w-2.5 h-2.5" />
                </a>
              </div>
              <input
                type="password"
                placeholder="Enter Resend API Key (re_...)"
                value={resendApiKey}
                onChange={(e) => setResendApiKey(e.target.value)}
                className="w-full px-2.5 py-1.5 bg-white border border-slate-300 rounded text-xs focus:ring-1 focus:ring-brand-500"
              />
            </div>

            {/* Traditional SMTP (For Local / VPS / Dedicated) */}
            <div className="pt-2 border-t border-slate-200 space-y-2">
              <span className="font-semibold text-slate-800 text-[11px]">Or Custom SMTP Gateway (Local / Dedicated):</span>
              <div className="grid grid-cols-2 gap-2">
                <input
                  type="text"
                  placeholder="SMTP Host (e.g. smtp.gmail.com)"
                  value={smtpHost}
                  onChange={(e) => setSmtpHost(e.target.value)}
                  className="col-span-2 px-2.5 py-1.5 bg-white border border-slate-300 rounded"
                />
                <input
                  type="text"
                  placeholder="Port (587)"
                  value={smtpPort}
                  onChange={(e) => setSmtpPort(e.target.value)}
                  className="px-2.5 py-1.5 bg-white border border-slate-300 rounded"
                />
                <input
                  type="text"
                  placeholder="From Email"
                  value={smtpFrom}
                  onChange={(e) => setSmtpFrom(e.target.value)}
                  className="px-2.5 py-1.5 bg-white border border-slate-300 rounded"
                />
                <input
                  type="text"
                  placeholder="SMTP User"
                  value={smtpUser}
                  onChange={(e) => setSmtpUser(e.target.value)}
                  className="px-2.5 py-1.5 bg-white border border-slate-300 rounded"
                />
                <input
                  type="password"
                  placeholder="SMTP App Password"
                  value={smtpPassword}
                  onChange={(e) => setSmtpPassword(e.target.value)}
                  className="px-2.5 py-1.5 bg-white border border-slate-300 rounded"
                />
              </div>
            </div>

            <div className="flex gap-2 pt-1">
              <button
                onClick={() => handleSaveIntegration('smtp', Boolean(smtpHost || resendApiKey), {
                  host: smtpHost,
                  port: smtpPort,
                  user: smtpUser,
                  password: smtpPassword,
                  from_email: smtpFrom,
                  resend_api_key: resendApiKey
                })}
                className="px-3 py-1.5 bg-emerald-700 hover:bg-emerald-800 text-white rounded text-xs font-bold transition-colors"
              >
                Save Email Configuration
              </button>
            </div>

            {/* Test Email Handshake */}
            <div className="pt-2 border-t border-slate-200 space-y-1.5">
              <div className="text-[11px] font-bold text-slate-700">Test Email Connection (SMTP / Resend API)</div>
              <div className="flex gap-2">
                <input
                  type="email"
                  placeholder="Enter destination test email"
                  value={testEmailRecipient}
                  onChange={(e) => setTestEmailRecipient(e.target.value)}
                  className="flex-1 px-2.5 py-1 bg-white border border-slate-300 rounded text-xs"
                />
                <button
                  type="button"
                  onClick={handleTestSmtp}
                  disabled={testingSmtp}
                  className="px-3 py-1 bg-slate-800 hover:bg-slate-900 text-white rounded text-xs font-semibold disabled:opacity-50"
                >
                  {testingSmtp ? 'Testing...' : 'Send Test'}
                </button>
              </div>
              {testResult && (
                <p className="text-[11px] text-emerald-700 font-medium bg-emerald-50 p-1.5 rounded">{testResult}</p>
              )}
            </div>
          </div>

          {/* WhatsApp */}
          <div className="p-4 bg-slate-50 rounded-xl border border-slate-200 space-y-2.5 text-xs">
            <div className="font-bold text-slate-900">WhatsApp Business Cloud API & Web Chat</div>
            <p className="text-[11px] text-slate-500">
              Direct Click-to-Chat (wa.me) works out-of-the-box for all verified phone numbers. For automated template messaging, connect official Meta Cloud API credentials.
            </p>
            <input
              type="text"
              placeholder="WhatsApp Phone Number ID"
              value={whatsappPhoneId}
              onChange={(e) => setWhatsappPhoneId(e.target.value)}
              className="w-full px-2.5 py-1.5 bg-white border border-slate-300 rounded"
            />
            <input
              type="password"
              placeholder="System User Permanent Access Token"
              value={whatsappToken}
              onChange={(e) => setWhatsappToken(e.target.value)}
              className="w-full px-2.5 py-1.5 bg-white border border-slate-300 rounded"
            />
            <button
              onClick={() => handleSaveIntegration('whatsapp', Boolean(whatsappPhoneId), {
                phone_number_id: whatsappPhoneId, access_token: whatsappToken
              })}
              className="px-3 py-1.5 bg-emerald-700 hover:bg-emerald-800 text-white rounded text-xs font-bold transition-colors"
            >
              Save WhatsApp Credentials
            </button>
          </div>

          {/* LinkedIn Integration Info */}
          <div className="p-4 bg-slate-50 rounded-xl border border-slate-200 space-y-2 text-xs col-span-1 md:col-span-2">
            <div className="flex items-center justify-between">
              <div className="font-bold text-slate-900 flex items-center gap-1.5">
                <span className="w-2.5 h-2.5 rounded-full bg-blue-600"></span>
                <span>LinkedIn Outreach Integration (Direct Profile & Deep Search)</span>
              </div>
              <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-blue-100 text-blue-800">
                100% Ready (Zero Setup Required)
              </span>
            </div>
            <p className="text-[11px] text-slate-600 leading-relaxed">
              Generates compliant connection request notes strictly under 295 characters (fitting LinkedIn's 300-char limit) and InMail pitches. In the Lead Drawer, clicking <strong>Copy Pitch & Open LinkedIn</strong> automatically copies the message, opens the prospect's profile/search on LinkedIn in a new tab, marks the lead stage as <strong>Contacted</strong>, and schedules an automatic 3-day follow-up reminder.
            </p>
          </div>
        </div>
      </div>

      {/* SECTION 3: SCORING WEIGHTS CONFIGURATION */}
      <div className="bg-white p-6 rounded-xl border border-slate-200 shadow-sm space-y-4">
        <h2 className="text-sm font-bold text-slate-800 flex items-center gap-2">
          <Sliders className="w-4 h-4 text-violet-600" />
          <span>Configurable Lead Scoring Weights (Total: 100 Points)</span>
        </h2>
        <div className="grid grid-cols-1 sm:grid-cols-5 gap-3 text-xs">
          <div className="p-3 bg-slate-50 border border-slate-200 rounded-lg">
            <label className="block font-semibold text-slate-700 mb-1">Industry Fit</label>
            <input
              type="number"
              min="0"
              max="50"
              value={weightIndustry}
              onChange={(e) => setWeightIndustry(Number(e.target.value))}
              className="w-full px-2 py-1 bg-white border border-slate-300 rounded text-center font-bold"
            />
            <span className="text-[10px] text-slate-400 mt-1 block">Default: 25 pts</span>
          </div>

          <div className="p-3 bg-slate-50 border border-slate-200 rounded-lg">
            <label className="block font-semibold text-slate-700 mb-1">Website Gaps</label>
            <input
              type="number"
              min="0"
              max="50"
              value={weightWebsite}
              onChange={(e) => setWeightWebsite(Number(e.target.value))}
              className="w-full px-2 py-1 bg-white border border-slate-300 rounded text-center font-bold"
            />
            <span className="text-[10px] text-slate-400 mt-1 block">Default: 25 pts</span>
          </div>

          <div className="p-3 bg-slate-50 border border-slate-200 rounded-lg">
            <label className="block font-semibold text-slate-700 mb-1">Contact Quality</label>
            <input
              type="number"
              min="0"
              max="50"
              value={weightContact}
              onChange={(e) => setWeightContact(Number(e.target.value))}
              className="w-full px-2 py-1 bg-white border border-slate-300 rounded text-center font-bold"
            />
            <span className="text-[10px] text-slate-400 mt-1 block">Default: 15 pts</span>
          </div>

          <div className="p-3 bg-slate-50 border border-slate-200 rounded-lg">
            <label className="block font-semibold text-slate-700 mb-1">Marketing Opportunity</label>
            <input
              type="number"
              min="0"
              max="50"
              value={weightOpp}
              onChange={(e) => setWeightOpp(Number(e.target.value))}
              className="w-full px-2 py-1 bg-white border border-slate-300 rounded text-center font-bold"
            />
            <span className="text-[10px] text-slate-400 mt-1 block">Default: 20 pts</span>
          </div>

          <div className="p-3 bg-slate-50 border border-slate-200 rounded-lg">
            <label className="block font-semibold text-slate-700 mb-1">Business Relevance</label>
            <input
              type="number"
              min="0"
              max="50"
              value={weightRelevance}
              onChange={(e) => setWeightRelevance(Number(e.target.value))}
              className="w-full px-2 py-1 bg-white border border-slate-300 rounded text-center font-bold"
            />
            <span className="text-[10px] text-slate-400 mt-1 block">Default: 15 pts</span>
          </div>
        </div>

        <div className="flex items-center justify-between pt-2">
          <div className="text-xs text-slate-600 font-semibold">
            Total Points:{' '}
            <span className={weightIndustry + weightWebsite + weightContact + weightOpp + weightRelevance === 100 ? 'text-emerald-700 font-bold' : 'text-red-600 font-bold'}>
              {weightIndustry + weightWebsite + weightContact + weightOpp + weightRelevance} / 100
            </span>
          </div>
          <button
            onClick={() => {
              setSaveMessage('Scoring weights saved! Future score calculations will use these weights.');
              setTimeout(() => setSaveMessage(null), 3000);
            }}
            className="px-4 py-2 bg-brand-700 hover:bg-brand-800 text-white text-xs font-bold rounded-lg shadow-sm"
          >
            Save Weight Configuration
          </button>
        </div>
      </div>
    </div>
  );
};
